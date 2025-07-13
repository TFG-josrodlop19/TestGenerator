package com.josrodlop19.javaAnalyzer;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
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
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtConstructor;
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

    // Nuevo atributo para almacenar la pila de llamadas
    @Setter(AccessLevel.PRIVATE)
    private List<Map<String, Object>> callStack;

    // ClassLoader con el classpath de Spoon
    @Setter(AccessLevel.PRIVATE)
    @Getter(AccessLevel.PRIVATE)
    private ClassLoader spoonClassLoader;

    public CodeAnalyzer(String pomPath, String filePath, Integer targetLine, String targetName) {
        this.pomPath = pomPath;
        this.filePath = filePath;
        this.targetLine = targetLine;
        this.targetName = targetName;
        this.callStack = new ArrayList<>();
    }

    public void processCode() {
        // Main method to process the code
        extractAST();
        findFunctionInvocation();
        extractArtifactData();
        extractCallStack(); // Nuevo método para extraer la pila de llamadas
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

        // Get class name
        this.artifactData.put("className",
                this.targetInvocation.getPosition().getFile().getName().replace(".java", ""));

        // Get artifact type and name
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
            ParamsProcessor.extractParamsFromSpoonDeclaration(functionDeclaration, arguments, paramsData);
        } else {
            // If no declaration is found, use reflection
            ParamsProcessor.extractParamsFromReflection(arguments, paramsData, this.targetInvocation,
                    this.targetName, this.spoonClassLoader);
        }

        this.artifactData.put("parameters", paramsData);
    }


    // NUEVOS MÉTODOS PARA EXTRAER LA PILA DE LLAMADAS

    /**
     * Extrae la pila de llamadas del método target, comenzando desde el método que
     * contiene
     * la invocación target y subiendo por la jerarquía de llamadas.
     */
    private void extractCallStack() {
        if (this.targetInvocation == null) {
            throw new IllegalStateException("Target invocation not found.");
        }

        // Empezamos desde el método que contiene la invocación target
        CtExecutable<?> containingMethod = this.targetInvocation.getParent(CtExecutable.class);
        List<String> visitedMethods = new ArrayList<>();
        if (containingMethod != null) {
            buildCallStackRecursively(containingMethod, visitedMethods);
        }
    }

    /**
     * Construye la pila de llamadas de forma recursiva
     */
    private void buildCallStackRecursively(CtExecutable<?> currentMethod, List<String> visitedMethods) {
        if (currentMethod == null) {
            return;
        }

        // Evitar ciclos infinitos
        String methodSignature = getMethodSignature(currentMethod);
        if (visitedMethods.contains(methodSignature)) {
            return;
        }

        visitedMethods.add(methodSignature);

        // Crear información del método actual
        Map<String, Object> methodInfo = createMethodInfo(currentMethod);
        this.callStack.add(0, methodInfo); // Añadir al principio para mantener el orden correcto

        // Buscar invocaciones a este método en todo el AST
        List<CtInvocation<?>> invocationsToCurrentMethod = findInvocationsToMethod(currentMethod);

        // Para cada invocación encontrada, continuar subiendo en la pila
        for (CtInvocation<?> invocation : invocationsToCurrentMethod) {
            CtExecutable<?> parentMethod = invocation.getParent(CtExecutable.class);
            if (parentMethod != null && !visitedMethods.contains(getMethodSignature(parentMethod))) {
                buildCallStackRecursively(parentMethod, new ArrayList<>(visitedMethods));
                break; // Tomamos solo la primera cadena de llamadas encontrada
            }
        }
    }

    /**
     * Busca todas las invocaciones a un método específico en el AST
     */
    private List<CtInvocation<?>> findInvocationsToMethod(CtExecutable<?> targetMethod) {
        List<CtInvocation<?>> invocations = new ArrayList<>();
        String targetMethodName = targetMethod.getSimpleName();

        // Buscar en todo el AST
        for (CtType<?> type : this.AST.getAllTypes()) {
            List<CtInvocation<?>> typeInvocations = type.getElements(new TypeFilter<>(CtInvocation.class));

            for (CtInvocation<?> invocation : typeInvocations) {
                if (isInvocationToMethod(invocation, targetMethod)) {
                    invocations.add(invocation);
                }
            }
        }

        return invocations;
    }

    /**
     * Verifica si una invocación corresponde a un método específico
     */
    private boolean isInvocationToMethod(CtInvocation<?> invocation, CtExecutable<?> targetMethod) {
        String invocationName = invocation.getExecutable().getSimpleName();
        String targetName = targetMethod.getSimpleName();

        if (!invocationName.equals(targetName)) {
            return false;
        }

        // Verificar que el número de parámetros coincida
        int invocationArgCount = invocation.getArguments().size();
        int targetParamCount = targetMethod.getParameters().size();

        if (invocationArgCount != targetParamCount) {
            return false;
        }

        // Verificar que la clase contenedora coincida (si es posible)
        CtType<?> targetClass = targetMethod.getParent(CtType.class);
        if (targetClass != null) {
            CtExpression<?> invocationTarget = invocation.getTarget();
            if (invocationTarget != null && invocationTarget.getType() != null) {
                String invocationClassName = invocationTarget.getType().getQualifiedName();
                String targetClassName = targetClass.getQualifiedName();
                return invocationClassName.equals(targetClassName);
            }
        }

        return true; // Si no podemos verificar la clase, asumimos que es correcto
    }

    /**
     * Crea la información completa de un método para la pila de llamadas
     */
    private Map<String, Object> createMethodInfo(CtExecutable<?> method) {
        Map<String, Object> methodInfo = new LinkedHashMap<>();

        // Información básica del método
        methodInfo.put("methodName", method.getSimpleName());
        methodInfo.put("methodType", method instanceof CtMethod ? "method" : "constructor");

        // Información de la clase contenedora
        CtType<?> containingClass = method.getParent(CtType.class);
        if (containingClass != null) {
            methodInfo.put("className", containingClass.getSimpleName());
            methodInfo.put("packageName",
                    containingClass.getPackage() != null ? containingClass.getPackage().getQualifiedName() : "default");
            methodInfo.put("fullClassName", containingClass.getQualifiedName());
        }

        // Información de posición en el código
        if (method.getPosition().isValidPosition()) {
            methodInfo.put("fileName", method.getPosition().getFile().getName());
            methodInfo.put("lineNumber", method.getPosition().getLine());
        }

        // Información de parámetros
        List<Map<String, String>> parametersInfo = new ArrayList<>();
        for (CtParameter<?> param : method.getParameters()) {
            Map<String, String> paramInfo = new HashMap<>();
            paramInfo.put("parameterName", param.getSimpleName());
            paramInfo.put("parameterType",
                    param.getType() != null ? param.getType().getQualifiedName() : "UNRESOLVED_TYPE");
            parametersInfo.add(paramInfo);
        }
        methodInfo.put("parameters", parametersInfo);

        // Información adicional
        if (method instanceof CtMethod) {
            CtMethod<?> ctMethod = (CtMethod<?>) method;
            methodInfo.put("isStatic", ctMethod.isStatic());
            methodInfo.put("isPublic", ctMethod.isPublic());
            methodInfo.put("isPrivate", ctMethod.isPrivate());
            methodInfo.put("isProtected", ctMethod.isProtected());
            methodInfo.put("returnType", ctMethod.getType() != null ? ctMethod.getType().getQualifiedName() : "void");
        } else if (method instanceof CtConstructor) {
            CtConstructor<?> ctConstructor = (CtConstructor<?>) method;
            methodInfo.put("isPublic", ctConstructor.isPublic());
            methodInfo.put("isPrivate", ctConstructor.isPrivate());
            methodInfo.put("isProtected", ctConstructor.isProtected());
            methodInfo.put("returnType", "constructor");
        }

        return methodInfo;
    }

    /**
     * Genera una signatura única para un método
     */
    private String getMethodSignature(CtExecutable<?> method) {
        StringBuilder signature = new StringBuilder();

        CtType<?> containingClass = method.getParent(CtType.class);
        if (containingClass != null) {
            signature.append(containingClass.getQualifiedName()).append(".");
        }

        signature.append(method.getSimpleName()).append("(");

        for (int i = 0; i < method.getParameters().size(); i++) {
            if (i > 0)
                signature.append(",");
            CtParameter<?> param = method.getParameters().get(i);
            signature.append(param.getType() != null ? param.getType().getQualifiedName() : "UNRESOLVED");
        }

        signature.append(")");
        return signature.toString();
    }

    public void getDataAsString() {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String jsonOutput = gson.toJson(this.artifactData);
        System.out.println(jsonOutput);
    }

    /**
     * Nuevo método para obtener tanto los datos del artefacto como la pila de
     * llamadas
     */
    public void getCompleteDataAsString() {
        Map<String, Object> completeData = new LinkedHashMap<>();
        completeData.put("artifactData", this.artifactData);
        completeData.put("callStack", this.callStack);

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String jsonOutput = gson.toJson(completeData);
        System.out.println(jsonOutput);
    }
}