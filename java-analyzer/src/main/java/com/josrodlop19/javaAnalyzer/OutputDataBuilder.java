package com.josrodlop19.javaAnalyzer;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import spoon.reflect.code.CtAbstractInvocation;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtConstructor;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtParameter;
import spoon.reflect.reference.CtTypeReference;
import spoon.reflect.visitor.filter.TypeFilter;

public class OutputDataBuilder {

    // Profundidad máxima para evitar recursión infinita
    private static final int MAX_RECURSION_DEPTH = 5;

    public static ArtifactData extractArtifactData(CtInvocation<?> invocation) {
        return extractArtifactData(invocation, 0);
    }

    public static ArtifactData extractArtifactData(CtInvocation<?> invocation, int recursionDepth) {
        if (invocation == null) {
            throw new IllegalStateException("Target invocation not found.");
        }

        ArtifactData data = new ArtifactData();

        data.setClassName(invocation.getPosition().getFile().getName().replace(".java", ""));
        data.setLineNumber(invocation.getPosition().getLine());
        data.setFilePath(invocation.getPosition().getFile().getAbsolutePath());

        // Get artifact type and name
        data.setNodeType(invocation.getClass().getSimpleName());
        data.setArtifactName(invocation.getExecutable().getSimpleName());

        // Get qualifier type
        CtExpression<?> target = invocation.getTarget();
        if (target != null) {
            CtTypeReference<?> qualifierTypeRef = target.getType();
            String qualifierType = (qualifierTypeRef != null) ? qualifierTypeRef.getQualifiedName() : "UNRESOLVED_TYPE";
            data.setQualifierType(qualifierType);
            data.setQualifierName(target.toString());
        } else {
            // If there is no target, it is a local call. EX: myMethod();
            data.setQualifierType("Local call");
        }

        // Get whether the method is static or not
        boolean isStatic = invocation.getExecutable().isStatic();
        data.setIsStatic(isStatic);

        // Get parameters with recursive constructor information
        List<Map<String, Object>> paramsData;
        CtExecutable<?> functionDeclaration = invocation.getExecutable().getDeclaration();
        List<CtExpression<?>> arguments = invocation.getArguments();

        if (functionDeclaration != null) {
            paramsData = ParamsProcessor.extractParamsFromSpoonDeclaration(functionDeclaration, arguments,
                    recursionDepth);
        } else {
            paramsData = ParamsProcessor.extractParamsFromReflection(arguments, invocation,
                    invocation.getExecutable().getSimpleName(), recursionDepth);
        }

        data.setParameters(paramsData);
        return data;
    }

    public static ArtifactData createMethodTreeNode(CtMethod<?> method) {
        return createMethodTreeNode(method, 0);
    }

    public static ArtifactData createMethodTreeNode(CtMethod<?> method, int recursionDepth) {
        ArtifactData treeNode = new ArtifactData();
        treeNode.setFilePath(method.getPosition().getFile().getAbsolutePath());
        treeNode.setClassName(method.getDeclaringType().getSimpleName());
        treeNode.setLineNumber(method.getPosition().getLine());

        treeNode.setNodeType(method.getClass().getSimpleName());
        treeNode.setQualifierType(method.getDeclaringType().getQualifiedName());
        treeNode.setQualifierName(method.getDeclaringType().getSimpleName());
        treeNode.setArtifactName(method.getSimpleName());
        treeNode.setIsStatic(method.isStatic());
        treeNode.setIsPublic(method.isPublic());

        // Get parameters with recursive constructor information
        List<Map<String, Object>> paramsData = argumentsInfo(method, recursionDepth);
        treeNode.setParameters(paramsData);

        return treeNode;
    }

    public static ArtifactData createConstructorTreeNode(CtConstructor<?> constructor) {
        return createConstructorTreeNode(constructor, 0);
    }

    public static ArtifactData createConstructorTreeNode(CtConstructor<?> constructor, int recursionDepth) {
        ArtifactData treeNode = new ArtifactData();
        treeNode.setFilePath(constructor.getPosition().getFile().getAbsolutePath());
        treeNode.setClassName(constructor.getDeclaringType().getSimpleName());
        treeNode.setLineNumber(constructor.getPosition().getLine());

        treeNode.setNodeType(constructor.getClass().getSimpleName());
        treeNode.setQualifierType(constructor.getDeclaringType().getQualifiedName());
        treeNode.setQualifierName(constructor.getDeclaringType().getSimpleName());

        // Get parameters with recursive constructor information
        List<Map<String, Object>> paramsData = argumentsInfo(constructor, recursionDepth);
        treeNode.setParameters(paramsData);

        return treeNode;
    }

    public static ArtifactData createRootTreeNode(CtAbstractInvocation<?> invocation) {
        return createRootTreeNode(invocation, 0);
    }

    public static ArtifactData createRootTreeNode(CtAbstractInvocation<?> invocation, int recursionDepth) {
        ArtifactData treeNode = new ArtifactData();
        treeNode.setFilePath(invocation.getPosition().getFile().getAbsolutePath());
        treeNode.setLineNumber(invocation.getPosition().getLine());
        treeNode.setClassName(invocation.getPosition().getFile().getName().replace(".java", ""));

        treeNode.setNodeType("Root");
        treeNode.setTarget(invocation.getExecutable().getSimpleName());
        treeNode.setQualifierName(invocation.getExecutable().getDeclaringType().getQualifiedName());
        treeNode.setQualifierType(invocation.getExecutable().getDeclaringType().getSimpleName());

        // Get parameters with recursive constructor information
        List<Map<String, Object>> paramsData;
        CtExecutable<?> functionDeclaration = invocation.getExecutable().getDeclaration();
        List<CtExpression<?>> arguments = invocation.getArguments();

        if (functionDeclaration != null) {
            paramsData = ParamsProcessor.extractParamsFromSpoonDeclaration(functionDeclaration, arguments,
                    recursionDepth);
        } else {
            paramsData = ParamsProcessor.extractParamsFromReflection(arguments, invocation,
                    invocation.getExecutable().getSimpleName(), recursionDepth);
        }

        treeNode.setParameters(paramsData);
        return treeNode;
    }

    private static List<Map<String, Object>> argumentsInfo(CtExecutable<?> executable, int recursionDepth) {
        List<CtParameter<?>> arguments = executable.getParameters();
        List<Map<String, Object>> argumentsData = new ArrayList<>();

        for (int i = 0; i < arguments.size(); i++) {
            CtParameter<?> arg = arguments.get(i);
            Map<String, Object> argInfo = new LinkedHashMap<>();
            argInfo.put("position", String.valueOf(i));
            argInfo.put("value", arg.toString());
            argInfo.put("type", arg.getType() != null ? arg.getType().getQualifiedName() : "Unknown");

            // Extraer información recursiva de constructores si no hemos alcanzado la
            // profundidad máxima
            if (recursionDepth < MAX_RECURSION_DEPTH && arg.getType() != null) {
                List<Map<String, Object>> constructorInfo = extractConstructorInfo(arg.getType(), recursionDepth + 1);
                if (!constructorInfo.isEmpty()) {
                    argInfo.put("constructor", constructorInfo);
                }
            }

            argumentsData.add(argInfo);
        }
        return argumentsData;
    }

    public static List<Map<String, Object>> extractConstructorInfo(CtTypeReference<?> typeRef, int recursionDepth) {
        List<Map<String, Object>> constructorsInfo = new ArrayList<>();

        if (typeRef == null || recursionDepth >= MAX_RECURSION_DEPTH) {
            return constructorsInfo;
        }

        // Evitar tipos primitivos y tipos básicos de Java
        String typeName = typeRef.getQualifiedName();
        if (isPrimitiveOrBasicType(typeName)) {
            return constructorsInfo;
        }

        try {
            // Intentar obtener la declaración del tipo
            if (typeRef.getTypeDeclaration() != null) {
                // Usar getElements() con filtro para obtener constructores
                List<CtConstructor<?>> constructors = typeRef.getTypeDeclaration()
                        .getElements(new TypeFilter<>(CtConstructor.class));
                if (constructors != null && !constructors.isEmpty()) {
                    for (CtConstructor<?> constructor : constructors) {
                        Map<String, Object> constructorInfo = new LinkedHashMap<>();
                        constructorInfo.put("className", typeRef.getSimpleName());
                        constructorInfo.put("qualifiedName", typeName);
                        constructorInfo.put("isPublic", constructor.isPublic());

                        // Información detallada de parámetros
                        List<Map<String, Object>> paramDetails = new ArrayList<>();
                        for (CtParameter<?> param : constructor.getParameters()) {
                            Map<String, Object> paramInfo = new LinkedHashMap<>();
                            paramInfo.put("name", param.getSimpleName());
                            paramInfo.put("type",
                                    param.getType() != null ? param.getType().getQualifiedName() : "Unknown");

                            // Recursión: obtener constructores de los parámetros
                            if (param.getType() != null
                                    && !isPrimitiveOrBasicType(param.getType().getQualifiedName())) {
                                List<Map<String, Object>> nestedConstructors = extractConstructorInfo(param.getType(),
                                        recursionDepth + 1);
                                if (!nestedConstructors.isEmpty()) {
                                    paramInfo.put("parameterConstructors", nestedConstructors);
                                }
                            }

                            paramDetails.add(paramInfo);
                        }

                        constructorInfo.put("parameters", paramDetails);
                        constructorsInfo.add(constructorInfo);
                    }
                } else {
                    // Fallback usando reflection si no hay constructores Spoon disponibles
                    constructorsInfo.addAll(extractConstructorInfoUsingReflection(typeName, recursionDepth));
                }
            } else {
                // Fallback usando reflection si no hay declaración Spoon disponible
                constructorsInfo.addAll(extractConstructorInfoUsingReflection(typeName, recursionDepth));
            }
        } catch (Exception e) {
            System.err.println("Error extracting constructor info for " + typeName + ": " + e.getMessage());
            // Intentar con reflection como fallback
            constructorsInfo.addAll(extractConstructorInfoUsingReflection(typeName, recursionDepth));
        }

        return constructorsInfo;
    }

    /**
     * Extrae información de constructores usando reflection como fallback
     */
    private static List<Map<String, Object>> extractConstructorInfoUsingReflection(String typeName,
            int recursionDepth) {
        List<Map<String, Object>> constructorsInfo = new ArrayList<>();

        try {
            Class<?> clazz = SpoonClassLoader.getInstance().getClassLoader().loadClass(typeName);
            java.lang.reflect.Constructor<?>[] constructors = clazz.getConstructors();

            for (java.lang.reflect.Constructor<?> constructor : constructors) {
                Map<String, Object> constructorInfo = new LinkedHashMap<>();
                constructorInfo.put("className", clazz.getSimpleName());
                constructorInfo.put("qualifiedName", typeName);
                constructorInfo.put("isPublic", java.lang.reflect.Modifier.isPublic(constructor.getModifiers()));
                constructorInfo.put("parameterCount", constructor.getParameterCount());

                // Información detallada de parámetros
                List<Map<String, Object>> paramDetails = new ArrayList<>();
                java.lang.reflect.Parameter[] params = constructor.getParameters();

                for (java.lang.reflect.Parameter param : params) {
                    Map<String, Object> paramInfo = new LinkedHashMap<>();
                    paramInfo.put("name", param.getName());
                    paramInfo.put("type", param.getType().getName());

                    // Recursión: obtener constructores de los parámetros
                    if (!isPrimitiveOrBasicType(param.getType().getName())) {
                        List<Map<String, Object>> nestedConstructors = extractConstructorInfoUsingReflection(
                                param.getType().getName(), recursionDepth + 1);
                        if (!nestedConstructors.isEmpty()) {
                            paramInfo.put("parameterConstructors", nestedConstructors);
                        }
                    }

                    paramDetails.add(paramInfo);
                }

                constructorInfo.put("parameters", paramDetails);
                constructorsInfo.add(constructorInfo);
            }
        } catch (Exception e) {
            System.err.println("Reflection fallback failed for " + typeName + ": " + e.getMessage());
        }

        return constructorsInfo;
    }

    /**
     * Verifica si un tipo es primitivo o un tipo básico de Java que no necesita
     * análisis recursivo
     */
    private static boolean isPrimitiveOrBasicType(String typeName) {
        return typeName.equals("int") || typeName.equals("long") || typeName.equals("double") ||
                typeName.equals("float") || typeName.equals("boolean") || typeName.equals("char") ||
                typeName.equals("byte") || typeName.equals("short") || typeName.equals("void") ||
                typeName.equals("java.lang.String") || typeName.equals("java.lang.Integer") ||
                typeName.equals("java.lang.Long") || typeName.equals("java.lang.Double") ||
                typeName.equals("java.lang.Float") || typeName.equals("java.lang.Boolean") ||
                typeName.equals("java.lang.Character") || typeName.equals("java.lang.Byte") ||
                typeName.equals("java.lang.Short") || typeName.equals("java.lang.Object") ||
                typeName.startsWith("java.util.") || typeName.startsWith("java.io.") ||
                typeName.startsWith("java.net.") || typeName.startsWith("java.time.");
    }
}