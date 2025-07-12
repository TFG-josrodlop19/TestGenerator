package com.josrodlop19.javaAnalyzer;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import lombok.AccessLevel;
import lombok.Getter;
import lombok.Setter;
import spoon.MavenLauncher;
import spoon.SpoonAPI;
import spoon.reflect.CtModel;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.declaration.CtParameter;
import spoon.reflect.declaration.CtType;
import spoon.reflect.reference.CtTypeReference;
import spoon.reflect.visitor.filter.TypeFilter;

@Getter
@Setter
public class CodeAnalyzer {
    private String filePath;
    private Integer targetLine;
    private String targetName;
    private String pomPath;

    @Setter(AccessLevel.NONE)
    private CtModel AST;

    // Attribute to store target method invocation
    @Setter(AccessLevel.PRIVATE)
    @Getter(AccessLevel.PRIVATE)
    private CtInvocation<?> targetInvocation;

    // Attribute to store artifact data
    @Setter(AccessLevel.PRIVATE)
    private Map<String, Object> artifactData;

    // ClassLoader con el classpath de Spoon
    private ClassLoader spoonClassLoader;

    public CodeAnalyzer(String pomPath, String filePath, Integer targetLine, String targetName) {
        this.pomPath = pomPath;
        this.filePath = filePath;
        this.targetLine = targetLine;
        this.targetName = targetName;
    }

    public void processCode() {
        // Main method to process the code
        extractAST();
        findFunctionInvocation();
        extractArtifactData();
    }

    private void extractAST() {
        SpoonAPI launcher = new MavenLauncher(this.pomPath, MavenLauncher.SOURCE_TYPE.APP_SOURCE, true);

        // Reads the file and builds the AST
        launcher.getEnvironment().setLevel("ALL");
        launcher.getEnvironment().setAutoImports(true);

        String[] classpath = launcher.getEnvironment().getSourceClasspath();

        // Manually create the classloader to be able to read method declarations in
        // dependencies
        createSpoonClassLoader(classpath);

        launcher.buildModel();
        this.AST = launcher.getModel();
    }

    private void createSpoonClassLoader(String[] classpath) {
        try {
            URL[] urls = new URL[classpath.length];
            for (int i = 0; i < classpath.length; i++) {
                urls[i] = new File(classpath[i]).toURI().toURL();
            }
            this.spoonClassLoader = new URLClassLoader(urls, this.getClass().getClassLoader());
        } catch (Exception e) {
            System.err.println("Error while creating classpath: " + e.getMessage());
            this.spoonClassLoader = this.getClass().getClassLoader();
        }
    }

    private void findFunctionInvocation() {
        String canonicalTargetPath;
        try {
            canonicalTargetPath = new File(this.filePath).getCanonicalPath();
        } catch (IOException e) {
            throw new RuntimeException("Error obtaining canonical path for the target file: " + this.filePath, e);
        }

        // Iterate through all types (classes) in the AST to find the target invocation
        for (CtType<?> node : this.AST.getAllTypes()) {
            if (node.getPosition().isValidPosition()) {
                try {
                    String nodeCanonicalPath = node.getPosition().getFile().getCanonicalPath();

                    if (nodeCanonicalPath.equals(canonicalTargetPath)) {
                        // Get all invocations in the current type
                        List<CtInvocation<?>> invocationsInClass = node
                                .getElements(new TypeFilter<>(CtInvocation.class));

                        CtInvocation<?> foundInvocation = findFunctionInsideCtType(invocationsInClass);

                        if (foundInvocation != null) {
                            this.targetInvocation = foundInvocation;
                            break;
                        }
                    }
                } catch (IOException e) {
                    // If there is an error obtaining the canonical path, we skip this type
                    continue;
                }
            } else {
                // If not valid position, we skip this type
                // A valid position means the type has a valid file associated with it, aka,
                // code actually exists.
                continue;
            }
        }
    }

    private CtInvocation<?> findFunctionInsideCtType(List<CtInvocation<?>> allInvocations) {
        CtInvocation<?> foundInvocation = null;
        for (CtInvocation<?> invocation : allInvocations) {
            if (invocation.getPosition().isValidPosition() &&
                    invocation.getPosition().getLine() == this.targetLine &&
                    invocation.getExecutable().getSimpleName().equals(this.targetName)) {
                foundInvocation = invocation;
                break;
            }
        }
        return foundInvocation;
    }

    private void extractArtifactData() {
        if (this.targetInvocation == null) {
            throw new IllegalStateException("Target invocation not found.");
        }

        this.artifactData = new LinkedHashMap<>();

        // Get artifact type and name (name is not really necessary)
        this.artifactData.put("artifactType", this.targetInvocation.getClass().getSimpleName());
        this.artifactData.put("methodName", this.targetInvocation.getExecutable().getSimpleName());

        // Get qualifier type
        CtExpression<?> target = this.targetInvocation.getTarget();
        if (target != null) {
            CtTypeReference<?> qualifierTypeRef = target.getType();
            String qualifierType = (qualifierTypeRef != null) ? qualifierTypeRef.getQualifiedName() : "UNRESOLVED_TYPE";
            this.artifactData.put("qualifierType", qualifierType);
            this.artifactData.put("qualifierNameInCode", target.toString());
        } else {
            // If there is no target, it is a local call. EX: myMethod();
            this.artifactData.put("qualifierType", "Local call");
        }

        // Get wheather the method is static or not
        boolean isStatic = this.targetInvocation.getExecutable().isStatic();
        this.artifactData.put("isStatic", isStatic);

        // Get parameters
        List<Map<String, String>> paramsData = new ArrayList<>();

        // Get the function declaration to extract parameter names and types
        CtExecutable<?> functionDeclaration = this.targetInvocation.getExecutable().getDeclaration();
        List<CtExpression<?>> arguments = this.targetInvocation.getArguments();

        if (functionDeclaration != null) {
            // Use Spoon declaration to extract parameter names and types
            extractParamsFromSpoonDeclaration(functionDeclaration, arguments, paramsData);
        } else {
            // If no declaration is found, use reflection
            extractParamsFromReflection(arguments, paramsData);
        }

        this.artifactData.put("parameters", paramsData);
    }

    private void extractParamsFromSpoonDeclaration(CtExecutable<?> functionDeclaration,
            List<CtExpression<?>> arguments,
            List<Map<String, String>> paramsData) {
        for (int i = 0; i < arguments.size(); i++) {
            CtExpression<?> param = arguments.get(i);
            CtTypeReference<?> paramType = param.getType();

            Map<String, String> paramInfo = new HashMap<>();
            paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");

            List<CtParameter<?>> declarationParams = functionDeclaration.getParameters();
            if (i < declarationParams.size()) {
                CtTypeReference<?> declarationType = declarationParams.get(i).getType();
                paramInfo.put("parameterName", declarationParams.get(i).getSimpleName());
                paramInfo.put("typeAtDeclaration",
                        (declarationType != null) ? declarationType.getQualifiedName() : "UNRESOLVED_TYPE");
            } else {
                paramInfo.put("possibleArray", "true");
            }

            paramsData.add(paramInfo);
        }
    }

    private void extractParamsFromReflection(List<CtExpression<?>> arguments,
            List<Map<String, String>> paramsData) {
        try {
            CtExpression<?> target = this.targetInvocation.getTarget();
            if (target == null) {
                // Método local, usar reflection en la clase actual
                extractParamsFromReflectionFallback(arguments, paramsData);
                return;
            }

            CtTypeReference<?> qualifierTypeRef = target.getType();
            if (qualifierTypeRef == null) {
                extractParamsFromReflectionFallback(arguments, paramsData);
                return;
            }

            String qualifierClassName = qualifierTypeRef.getQualifiedName();

            // Load class using Spoon's classloader
            Class<?> clazz = spoonClassLoader.loadClass(qualifierClassName);

            // Get the types of the arguments to get the correct method
            Class<?>[] argTypes = new Class<?>[arguments.size()];
            for (int i = 0; i < arguments.size(); i++) {
                CtExpression<?> arg = arguments.get(i);
                CtTypeReference<?> argType = arg.getType();
                if (argType != null) {
                    try {
                        argTypes[i] = loadClassFromType(argType);
                    } catch (Exception e) {
                        argTypes[i] = Object.class;
                    }
                } else {
                    argTypes[i] = Object.class;
                }
            }

            // Look for the method in the class using reflection
            Method method = findMatchingMethod(clazz, this.targetName, argTypes);

            if (method != null) {
                Parameter[] parameters = method.getParameters();
                for (int i = 0; i < arguments.size(); i++) {
                    CtExpression<?> param = arguments.get(i);
                    CtTypeReference<?> paramType = param.getType();

                    Map<String, String> paramInfo = new HashMap<>();
                    paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");

                    if (i < parameters.length) {
                        Parameter reflectionParam = parameters[i];
                        paramInfo.put("parameterName", reflectionParam.getName());
                        paramInfo.put("typeAtDeclaration", reflectionParam.getType().getName());
                    } else {
                        paramInfo.put("possibleArray", "true");
                    }

                    paramsData.add(paramInfo);
                }
            } else {
                extractParamsFromReflectionFallback(arguments, paramsData);
            }

        } catch (Exception e) {
            System.err.println("Error usando reflection: " + e.getMessage());
            extractParamsFromReflectionFallback(arguments, paramsData);
        }
    }

    private void extractParamsFromReflectionFallback(List<CtExpression<?>> arguments,
            List<Map<String, String>> paramsData) {
        for (int i = 0; i < arguments.size(); i++) {
            CtExpression<?> param = arguments.get(i);
            CtTypeReference<?> paramType = param.getType();

            Map<String, String> paramInfo = new HashMap<>();
            paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");
            paramInfo.put("typeAtDeclaration", "UNRESOLVED_TYPE");
            paramInfo.put("parameterName", "param" + i);

            paramsData.add(paramInfo);
        }
    }

    private Class<?> loadClassFromType(CtTypeReference<?> typeRef) throws ClassNotFoundException {
        String typeName = typeRef.getQualifiedName();
        switch (typeName) {
            case "int":
                return int.class;
            case "long":
                return long.class;
            case "double":
                return double.class;
            case "float":
                return float.class;
            case "boolean":
                return boolean.class;
            case "char":
                return char.class;
            case "byte":
                return byte.class;
            case "short":
                return short.class;
            default:
                return spoonClassLoader.loadClass(typeName);
        }
    }

    private Method findMatchingMethod(Class<?> clazz, String methodName, Class<?>[] argTypes) {
        Method[] methods = clazz.getMethods();

        // Look for an exact match with parameter types
        for (Method method : methods) {
            if (method.getName().equals(methodName) &&
                    method.getParameterCount() == argTypes.length) {
                Class<?>[] paramTypes = method.getParameterTypes();
                boolean matches = true;
                for (int i = 0; i < paramTypes.length; i++) {
                    if (!paramTypes[i].isAssignableFrom(argTypes[i]) &&
                            !areCompatibleTypes(paramTypes[i], argTypes[i])) {
                        matches = false;
                        break;
                    }
                }
                if (matches) {
                    return method;
                }
            }
        }

        // If not found an exact match, look for a method with the same name and
        // parameter count
        for (Method method : methods) {
            if (method.getName().equals(methodName) &&
                    method.getParameterCount() == argTypes.length) {
                return method;
            }
        }

        return null;
    }

    private boolean areCompatibleTypes(Class<?> paramType, Class<?> argType) {
        if (paramType.isPrimitive() && !argType.isPrimitive() || !paramType.isPrimitive() && argType.isPrimitive()) {
            return isWrapperType(paramType, argType);
        }
        return paramType.equals(argType);
    }

    private boolean isWrapperType(Class<?> primitive, Class<?> wrapper) {
        return (primitive == int.class && wrapper == Integer.class) ||
                (primitive == long.class && wrapper == Long.class) ||
                (primitive == double.class && wrapper == Double.class) ||
                (primitive == float.class && wrapper == Float.class) ||
                (primitive == boolean.class && wrapper == Boolean.class) ||
                (primitive == char.class && wrapper == Character.class) ||
                (primitive == byte.class && wrapper == Byte.class) ||
                (primitive == short.class && wrapper == Short.class);
    }


    public void getDataAsString() {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String jsonOutput = gson.toJson(this.artifactData);
        System.out.println(jsonOutput);
    }
}