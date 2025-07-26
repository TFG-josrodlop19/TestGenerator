package com.josrodlop19.javaAnalyzer;

import java.io.File;
import java.io.IOException;
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
    // Input parameters
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
        this.artifactData = new LinkedHashMap<>();
        this.callStack = new ArrayList<>();
    }

    public void processCode() {
        // Main method to process the code
        extractAST();
        findFunctionInvocation();

        this.artifactData.put("artifactData", extractArtifactData(this.targetInvocation));
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

    private Map<String, Object> extractArtifactData(CtInvocation<?> invocation) {
        if (this.targetInvocation == null) {
            throw new IllegalStateException("Target invocation not found.");
        }

        Map<String, Object> data = new LinkedHashMap<>();

        // Get class name
        data.put("className",
                this.targetInvocation.getPosition().getFile().getName().replace(".java", ""));

        // Get artifact type and name
        data.put("artifactType", this.targetInvocation.getClass().getSimpleName());
        data.put("methodName", this.targetInvocation.getExecutable().getSimpleName());

        // Get qualifier type
        CtExpression<?> target = this.targetInvocation.getTarget();
        if (target != null) {
            CtTypeReference<?> qualifierTypeRef = target.getType();
            String qualifierType = (qualifierTypeRef != null) ? qualifierTypeRef.getQualifiedName() : "UNRESOLVED_TYPE";
            data.put("qualifierType", qualifierType);
            data.put("qualifierNameInCode", target.toString());
        } else {
            // If there is no target, it is a local call. EX: myMethod();
            data.put("qualifierType", "Local call");
        }

        // Get wheather the method is static or not
        boolean isStatic = this.targetInvocation.getExecutable().isStatic();
        data.put("isStatic", isStatic);

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

        data.put("parameters", paramsData);
        return data;
    }

    private void extractCallStack() {
        if (this.targetInvocation == null) {
            System.out.println("No se encontró la invocación objetivo para extraer la pila de llamadas");
            return;
        }

        // Crear mapas para almacenar métodos y sus invocaciones
        Map<String, CtMethod<?>> methodMap = new HashMap<>();
        Map<String, List<CtInvocation<?>>> methodInvocations = new HashMap<>();

        // Recopilar todos los métodos e invocaciones del AST
        collectMethodsAndInvocations(methodMap, methodInvocations);

        // Construir el árbol de llamadas
        Map<String, Object> callTree = buildCallTree(this.targetInvocation, methodMap, methodInvocations,
                new ArrayList<>());

        // Agregar el árbol de llamadas a artifactData
        this.artifactData.put("callTree", callTree);

        // También generar todas las rutas posibles como lista plana
        List<List<Map<String, Object>>> allPaths = new ArrayList<>();
        extractAllPaths(callTree, new ArrayList<>(), allPaths);
        this.artifactData.put("allCallPaths", allPaths);
    }

    private void collectMethodsAndInvocations(Map<String, CtMethod<?>> methodMap,
            Map<String, List<CtInvocation<?>>> methodInvocations) {

        // Recorrer todos los tipos en el AST
        for (CtType<?> type : this.AST.getAllTypes()) {
            // Procesar todos los métodos del tipo
            for (CtMethod<?> method : type.getMethods()) {
                String methodKey = createMethodKey(method);
                methodMap.put(methodKey, method);

                // Encontrar todas las invocaciones dentro de este método
                List<CtInvocation<?>> invocations = method.getElements(new TypeFilter<>(CtInvocation.class));
                methodInvocations.put(methodKey, invocations);
            }

            // También procesar constructores
            List<CtConstructor<?>> constructors = type.getElements(new TypeFilter<>(CtConstructor.class));
            for (CtConstructor<?> constructor : constructors) {
                String constructorKey = createConstructorKey(constructor);
                // Los constructores también pueden tener invocaciones
                List<CtInvocation<?>> invocations = constructor.getElements(new TypeFilter<>(CtInvocation.class));
                methodInvocations.put(constructorKey, invocations);
            }
        }
    }

    private String createMethodKey(CtMethod<?> method) {
        StringBuilder key = new StringBuilder();
        key.append(method.getDeclaringType().getQualifiedName())
                .append(".")
                .append(method.getSimpleName())
                .append("(");

        // Agregar tipos de parámetros para uniqueness
        List<CtParameter<?>> parameters = method.getParameters();
        for (int i = 0; i < parameters.size(); i++) {
            if (i > 0)
                key.append(",");
            CtTypeReference<?> type = parameters.get(i).getType();
            key.append(type != null ? type.getQualifiedName() : "?");
        }
        key.append(")");
        return key.toString();
    }

    private String createConstructorKey(CtConstructor<?> constructor) {
        StringBuilder key = new StringBuilder();
        key.append(constructor.getDeclaringType().getQualifiedName())
                .append(".<init>(");

        // Agregar tipos de parámetros
        List<CtParameter<?>> parameters = constructor.getParameters();
        for (int i = 0; i < parameters.size(); i++) {
            if (i > 0)
                key.append(",");
            CtTypeReference<?> type = parameters.get(i).getType();
            key.append(type != null ? type.getQualifiedName() : "?");
        }
        key.append(")");
        return key.toString();
    }

    private Map<String, Object> buildCallTree(CtInvocation<?> currentInvocation,
            Map<String, CtMethod<?>> methodMap,
            Map<String, List<CtInvocation<?>>> methodInvocations,
            List<String> visitedMethods) {

        Map<String, Object> treeNode = new LinkedHashMap<>();

        // Obtener el método que contiene la invocación actual
        CtMethod<?> currentMethod = currentInvocation.getParent(CtMethod.class);
        if (currentMethod == null) {
            // Podría estar en un constructor
            CtConstructor<?> constructor = currentInvocation.getParent(CtConstructor.class);
            if (constructor != null) {
                treeNode = createConstructorTreeNode(constructor, currentInvocation);
            } else {
                // Nodo raíz o sin contexto
                treeNode = createRootTreeNode(currentInvocation);
            }
            treeNode.put("callers", new ArrayList<>());
            return treeNode;
        }

        String currentMethodKey = createMethodKey(currentMethod);

        // Crear información del nodo actual
        treeNode = createMethodTreeNode(currentMethod, currentInvocation);
        // TODO: cambiar el if para que se haga antes de crear el nodo
        // Evitar ciclos infinitos
        if (visitedMethods.contains(currentMethodKey)) {
            treeNode.put("callers", new ArrayList<>());
            treeNode.put("cycleDetected", true);
            return treeNode;
        }

        // Crear nueva lista para esta rama
        List<String> newVisited = new ArrayList<>(visitedMethods);
        newVisited.add(currentMethodKey);

        // Buscar TODOS los métodos que llaman al método actual
        List<Map<String, Object>> callers = findAllCallers(currentMethod, methodMap, methodInvocations, newVisited);
        treeNode.put("callers", callers);

        return treeNode;
    }

    private List<Map<String, Object>> findAllCallers(CtMethod<?> targetMethod,
            Map<String, CtMethod<?>> methodMap,
            Map<String, List<CtInvocation<?>>> methodInvocations,
            List<String> visitedMethods) {

        List<Map<String, Object>> callers = new ArrayList<>();

        // Buscar en todas las invocaciones de todos los métodos
        for (Map.Entry<String, List<CtInvocation<?>>> entry : methodInvocations.entrySet()) {
            String methodKey = entry.getKey();
            List<CtInvocation<?>> invocations = entry.getValue();

            // Saltar métodos ya visitados
            if (visitedMethods.contains(methodKey)) {
                continue;
            }

            for (CtInvocation<?> invocation : invocations) {
                if (isCallingTargetMethod(invocation, targetMethod)) {
                    // Encontramos un caller, agregar al árbol recursivamente
                    Map<String, Object> callerNode = buildCallTree(invocation, methodMap, methodInvocations,
                            visitedMethods);
                    callers.add(callerNode);
                }
            }
        }

        return callers;
    }

    private boolean isCallingTargetMethod(CtInvocation<?> invocation, CtMethod<?> targetMethod) {
        // Verificar nombre del método
        if (!invocation.getExecutable().getSimpleName().equals(targetMethod.getSimpleName())) {
            return false;
        }

        // Verificar clase declarante
        CtTypeReference<?> invocationDeclaringType = invocation.getExecutable().getDeclaringType();
        CtType<?> targetDeclaringType = targetMethod.getDeclaringType();

        if (invocationDeclaringType != null && targetDeclaringType != null) {
            String invocationClassName = invocationDeclaringType.getQualifiedName();
            String targetClassName = targetDeclaringType.getQualifiedName();

            if (!invocationClassName.equals(targetClassName)) {
                return false;
            }
        }

        // Verificar parámetros (número y tipos si es posible)
        List<CtTypeReference<?>> invocationParams = invocation.getExecutable().getParameters();
        List<CtParameter<?>> targetParams = targetMethod.getParameters();

        if (invocationParams.size() != targetParams.size()) {
            return false;
        }

        // Verificación más detallada de tipos de parámetros
        for (int i = 0; i < invocationParams.size(); i++) {
            CtTypeReference<?> invocationParam = invocationParams.get(i);
            CtTypeReference<?> targetParam = targetParams.get(i).getType();

            if (invocationParam != null && targetParam != null) {
                if (!invocationParam.getQualifiedName().equals(targetParam.getQualifiedName())) {
                    return false;
                }
            }
        }

        return true;
    }

    private Map<String, Object> createMethodTreeNode(CtMethod<?> method, CtInvocation<?> invocation) {
        Map<String, Object> node = new LinkedHashMap<>();

        // Información básica del método
        node.put("type", "method");
        node.put("methodName", method.getSimpleName());
        node.put("className", method.getDeclaringType().getSimpleName());
        node.put("qualifiedClassName", method.getDeclaringType().getQualifiedName());
        node.put("methodKey", createMethodKey(method));

        // Información de la invocación
        node.put("invocationTarget", invocation.getExecutable().getSimpleName());
        node.put("invocationClass", invocation.getExecutable().getDeclaringType().getQualifiedName());

        // Información de posición
        addPositionInfo(node, invocation);

        // Argumentos de la invocación
        addArgumentsInfo(node, invocation);

        // Información adicional del método
        node.put("isStatic", method.isStatic());
        node.put("isPublic", method.isPublic());
        node.put("isPrivate", method.isPrivate());
        node.put("returnType", method.getType().getQualifiedName());

        return node;
    }

    private Map<String, Object> createConstructorTreeNode(CtConstructor<?> constructor, CtInvocation<?> invocation) {
        Map<String, Object> node = new LinkedHashMap<>();
        node.put("type", "constructor");
        node.put("className", constructor.getDeclaringType().getSimpleName());
        node.put("qualifiedClassName", constructor.getDeclaringType().getQualifiedName());
        node.put("methodKey", createConstructorKey(constructor));
        node.put("invocationTarget", invocation.getExecutable().getSimpleName());
        node.put("invocationClass", invocation.getExecutable().getDeclaringType().getQualifiedName());

        // Información de posición
        addPositionInfo(node, invocation);

        // Argumentos
        addArgumentsInfo(node, invocation);

        return node;
    }

    private Map<String, Object> createRootTreeNode(CtInvocation<?> invocation) {
        Map<String, Object> node = new LinkedHashMap<>();
        node.put("type", "root");
        node.put("invocationTarget", invocation.getExecutable().getSimpleName());
        node.put("invocationClass", invocation.getExecutable().getDeclaringType().getQualifiedName());

        // Información de posición
        addPositionInfo(node, invocation);

        // Argumentos
        addArgumentsInfo(node, invocation);

        return node;
    }

    private void addPositionInfo(Map<String, Object> node, CtInvocation<?> invocation) {
        if (invocation.getPosition() != null && invocation.getPosition().isValidPosition()) {
            node.put("fileName", invocation.getPosition().getFile().getName());
            node.put("lineNumber", invocation.getPosition().getLine());
            node.put("columnNumber", invocation.getPosition().getColumn());

            try {
                node.put("filePath", invocation.getPosition().getFile().getCanonicalPath());
            } catch (IOException e) {
                node.put("filePath", invocation.getPosition().getFile().getAbsolutePath());
            }
        } else {
            node.put("fileName", "Unknown");
            node.put("lineNumber", -1);
            node.put("columnNumber", -1);
            node.put("filePath", "Unknown");
        }
    }

    private void addArgumentsInfo(Map<String, Object> node, CtInvocation<?> invocation) {
        List<Map<String, String>> arguments = new ArrayList<>();
        for (int i = 0; i < invocation.getArguments().size(); i++) {
            CtExpression<?> arg = invocation.getArguments().get(i);
            Map<String, String> argInfo = new LinkedHashMap<>();
            argInfo.put("position", String.valueOf(i));
            argInfo.put("value", arg.toString());
            argInfo.put("type", arg.getType() != null ? arg.getType().getQualifiedName() : "Unknown");
            arguments.add(argInfo);
        }
        node.put("arguments", arguments);
    }

    // Método para extraer todas las rutas posibles del árbol
    private void extractAllPaths(Map<String, Object> treeNode, List<Map<String, Object>> currentPath,
            List<List<Map<String, Object>>> allPaths) {

        // Agregar el nodo actual al path
        Map<String, Object> nodeInfo = new LinkedHashMap<>();
        nodeInfo.put("type", treeNode.get("type"));
        nodeInfo.put("methodName", treeNode.get("methodName"));
        nodeInfo.put("className", treeNode.get("className"));
        nodeInfo.put("qualifiedClassName", treeNode.get("qualifiedClassName"));
        nodeInfo.put("invocationTarget", treeNode.get("invocationTarget"));
        nodeInfo.put("invocationClass", treeNode.get("invocationClass"));
        nodeInfo.put("fileName", treeNode.get("fileName"));
        nodeInfo.put("lineNumber", treeNode.get("lineNumber"));
        nodeInfo.put("arguments", treeNode.get("arguments"));

        List<Map<String, Object>> newPath = new ArrayList<>(currentPath);
        newPath.add(nodeInfo);

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> callers = (List<Map<String, Object>>) treeNode.get("callers");

        if (callers == null || callers.isEmpty()) {
            // Es una hoja, agregar el path completo
            allPaths.add(newPath);
        } else {
            // Continuar recursivamente con cada caller
            for (Map<String, Object> caller : callers) {
                extractAllPaths(caller, newPath, allPaths);
            }
        }
    }

    // Método auxiliar para obtener el árbol como JSON formateado
    public String getCallTreeAsJson() {
        Map<String, Object> callTree = (Map<String, Object>) this.artifactData.get("callTree");
        if (callTree == null) {
            return "{}";
        }
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        return gson.toJson(callTree);
    }

    // Método auxiliar para obtener todas las rutas como JSON
    public String getAllCallPathsAsJson() {
        List<List<Map<String, Object>>> allPaths = (List<List<Map<String, Object>>>) this.artifactData
                .get("allCallPaths");
        if (allPaths == null) {
            return "[]";
        }
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        return gson.toJson(allPaths);
    }

    // Método para imprimir el árbol de llamadas
    public void printCallTree() {
        Map<String, Object> callTree = (Map<String, Object>) this.artifactData.get("callTree");
        if (callTree == null) {
            System.out.println("No se encontró árbol de llamadas");
            return;
        }

        System.out.println("\n=== ÁRBOL DE LLAMADAS ===");
        printTreeNode(callTree, 0);
        System.out.println("=========================\n");
    }

    private void printTreeNode(Map<String, Object> node, int depth) {
        String indent = "  ".repeat(depth);

        System.out.println(indent + "├─ " + node.get("qualifiedClassName") + "." + node.get("methodName") + "()");
        System.out.println(indent + "│  Archivo: " + node.get("fileName") + ", Línea: " + node.get("lineNumber"));
        System.out.println(indent + "│  Invoca: " + node.get("invocationTarget"));

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> callers = (List<Map<String, Object>>) node.get("callers");

        if (callers != null && !callers.isEmpty()) {
            System.out.println(indent + "│  Llamado por:");
            for (Map<String, Object> caller : callers) {
                printTreeNode(caller, depth + 1);
            }
        }
    }

    // Método para imprimir todas las rutas
    public void printAllCallPaths() {
        List<List<Map<String, Object>>> allPaths = (List<List<Map<String, Object>>>) this.artifactData
                .get("allCallPaths");
        if (allPaths == null || allPaths.isEmpty()) {
            System.out.println("No se encontraron rutas de llamadas");
            return;
        }

        System.out.println("\n=== TODAS LAS RUTAS DE LLAMADAS ===");
        for (int i = 0; i < allPaths.size(); i++) {
            System.out.println("Ruta " + (i + 1) + ":");
            List<Map<String, Object>> path = allPaths.get(i);
            for (int j = 0; j < path.size(); j++) {
                Map<String, Object> node = path.get(j);
                System.out.println("  " + (j + 1) + ". " + node.get("qualifiedClassName") +
                        "." + node.get("methodName") + "() [" + node.get("fileName") +
                        ":" + node.get("lineNumber") + "]");
            }
            System.out.println();
        }
        System.out.println("===================================\n");
    }

    // Método auxiliar para obtener la pila de llamadas como JSON (compatibilidad)
    public String getCallStackAsJson() {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        return gson.toJson(this.callStack);
    }

    // Método auxiliar para imprimir la pila de llamadas (compatibilidad)
    public void printCallStack() {
        if (this.callStack == null || this.callStack.isEmpty()) {
            System.out.println("No se encontró pila de llamadas");
            return;
        }

        System.out.println("\n=== PILA DE LLAMADAS (Primera Ruta) ===");
        for (int i = 0; i < this.callStack.size(); i++) {
            Map<String, Object> methodInfo = this.callStack.get(i);
            System.out.println((i + 1) + ". " + methodInfo.get("qualifiedClassName") +
                    "." + methodInfo.get("methodName") + "()");
            System.out.println("   Archivo: " + methodInfo.get("fileName") +
                    ", Línea: " + methodInfo.get("lineNumber"));
            System.out.println("   Invoca: " + methodInfo.get("invocationTarget"));
            System.out.println();
        }
        System.out.println("=======================================\n");
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

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String jsonOutput = gson.toJson(this.artifactData);
        System.out.println(jsonOutput);
    }
}