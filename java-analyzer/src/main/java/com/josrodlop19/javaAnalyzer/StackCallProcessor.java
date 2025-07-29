package com.josrodlop19.javaAnalyzer;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import lombok.AccessLevel;
import lombok.Getter;
import lombok.Setter;
import spoon.reflect.CtModel;
import spoon.reflect.code.CtAbstractInvocation;
import spoon.reflect.code.CtConstructorCall;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtConstructor;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtParameter;
import spoon.reflect.declaration.CtType;
import spoon.reflect.reference.CtTypeReference;
import spoon.reflect.visitor.filter.TypeFilter;

@Getter
@Setter
public class StackCallProcessor {
    private CtInvocation<?> targetInvocation;
    @Setter(AccessLevel.PRIVATE)
    private CtModel AST;

    private Map<String, CtExecutable<?>> executables;
    private Map<String, List<CtAbstractInvocation<?>>> methodInvocations;
    private Map<String, List<CtConstructorCall<?>>> constructorCalls;
    private ArtifactData callTree;
    private List<List<Map<String, Object>>> allCallPaths;

    public StackCallProcessor(CtInvocation<?> targetInvocation, CtModel AST) {
        this.targetInvocation = targetInvocation;
        this.AST = AST;
        this.executables = new LinkedHashMap<>();
        this.methodInvocations = new LinkedHashMap<>();
        this.constructorCalls = new LinkedHashMap<>();
    }

    public void extractCallStack() {
        if (this.targetInvocation == null) {
            System.out.println("No se encontró la invocación objetivo para extraer la pila de llamadas");
            return;
        }

        // Crear mapas para almacenar métodos y sus invocaciones
        Map<String, ArtifactData> visited = new LinkedHashMap<>();

        // Recopilar todos los métodos e invocaciones del AST
        collectMethodsAndInvocations();

        // Construir el árbol de llamadas
        ArtifactData callTree = buildCallTree(this.targetInvocation, visited);

        // Agregar el árbol de llamadas a artifactData
        this.setCallTree(callTree);

        // También generar todas las rutas posibles como lista plana
        List<List<Map<String, Object>>> allPaths = new ArrayList<>();
        extractAllPaths(callTree, new ArrayList<>(), allPaths);
        this.setAllCallPaths(allPaths);
    }

    private void collectMethodsAndInvocations() {
        for (CtType<?> type : this.getAST().getAllTypes()) {
            List<CtExecutable<?>> executables = type.getElements(new TypeFilter<>(CtExecutable.class));
            for (CtExecutable<?> executable : executables) {
                String signature = createSignature(executable);
                this.executables.put(signature, executable);
                List<CtAbstractInvocation<?>> invocations = executable.getElements(new TypeFilter<>(CtAbstractInvocation.class));
                this.methodInvocations.put(signature, invocations);
                
                
                List<CtConstructorCall<?>> constructorCalls = executable
                        .getElements(new TypeFilter<>(CtConstructorCall.class));
                this.constructorCalls.put(signature, constructorCalls);
            }
        }
    }

    private String createSignature(CtExecutable<?> artifact) {
        StringBuilder key = new StringBuilder();

        key.append(artifact.getReference().getDeclaringType().getQualifiedName());

        if (artifact instanceof CtMethod<?>) {
            key.append(".")
                    .append(artifact.getSimpleName())
                    .append("(");
        } else if (artifact instanceof CtConstructor<?>) {
            key.append(".<init>(");
        } else {
            throw new IllegalArgumentException("Unsupported executable type: " + artifact.getClass().getSimpleName());

        }
        List<CtParameter<?>> parameters = artifact.getParameters();
        for (int i = 0; i < parameters.size(); i++) {
            if (i > 0)
                key.append(",");
            CtTypeReference<?> type = parameters.get(i).getType();
            key.append(type != null ? type.getQualifiedName() : "?");
        }
        key.append(")");
        return key.toString();
    }

    private ArtifactData buildCallTree(CtAbstractInvocation<?> currentInvocation, Map<String, ArtifactData> visited) {

        ArtifactData treeNode = new ArtifactData();

        // Obtener el método que contiene la invocación actual
        CtExecutable<?> currentMethod = currentInvocation.getParent(CtExecutable.class);

        if (currentMethod == null) {
            treeNode = OutputDataBuilder.createRootTreeNode(currentInvocation);
            return treeNode;
        }

        String currentMethodSignature = createSignature(currentMethod);
        if (visited.containsKey(currentMethodSignature)) {
            return visited.get(currentMethodSignature);
        }

        String currentMethodKey = createSignature(currentMethod);

        // Crear información del nodo actual
        if (currentMethod instanceof CtMethod<?>) {
            treeNode = OutputDataBuilder.createMethodTreeNode((CtMethod<?>) currentMethod);
        } else if (currentMethod instanceof CtConstructor<?>) {
            treeNode = OutputDataBuilder.createConstructorTreeNode((CtConstructor<?>) currentMethod);
        } else {
            throw new IllegalArgumentException(
                    "Unsupported executable type: " + currentMethod.getClass().getSimpleName());
        }

        // Crear nueva lista para esta rama
        // Map<String, Object> newVisited = new LinkedHashMap<>(visited);
        // newVisited.put(currentMethodKey, currentMethod);

        visited.put(currentMethodKey, treeNode);

        // Buscar TODOS los métodos que llaman al método actual
        List<ArtifactData> callers = findAllCallers(currentMethod, visited);
        treeNode.getCallers().addAll(callers);

        return treeNode;
    }

    private List<ArtifactData> findAllCallers(CtExecutable<?> targetMethod, Map<String, ArtifactData> visitedMethods) {

        List<ArtifactData> callers = new ArrayList<>();

        // Buscar en todas las invocaciones de todos los métodos
        for (Map.Entry<String, List<CtAbstractInvocation<?>>> entry : this.methodInvocations.entrySet()) {
            String methodKey = entry.getKey();
            List<CtAbstractInvocation<?>> invocations = entry.getValue();

            // Saltar métodos ya visitados
            if (visitedMethods.containsKey(methodKey)) {
                continue;
            }

            for (CtAbstractInvocation<?> invocation : invocations) {
                if (isCallingTargetExecutable(invocation, targetMethod)) {
                    // Encontramos un caller, agregar al árbol recursivamente
                    ArtifactData callerNode = buildCallTree(invocation, visitedMethods);
                    callers.add(callerNode);
                }
            }
        }

        // List<ArtifactData> constructorCallers = new ArrayList<>();
        // for (Map.Entry<String, List<CtConstructorCall<?>>> entry : this.constructorCalls.entrySet()) {
        //     String methodKey = entry.getKey();
        //     List<CtConstructorCall<?>> constructorCalls = entry.getValue();

        //     // Saltar métodos ya visitados
        //     if (visitedMethods.containsKey(methodKey)) {
        //         continue;
        //     }

        //     for (CtConstructorCall<?> constructorCall : constructorCalls) {
        //         if (isCallingTargetExecutable(constructorCall, targetMethod)) {
        //             // Encontramos un caller, agregar al árbol recursivamente
        //             ArtifactData callerNode = buildCallTree(constructorCall, visitedMethods);
        //             constructorCallers.add(callerNode);
        //         }
        //     }
            
        // }

        return callers;
    }

    private Boolean isCallingTargetExecutable(CtAbstractInvocation<?> invocation, CtExecutable<?> targetExecutable) {
        // La forma más robusta de comparar es usando las referencias, que contienen la
        // firma completa.
        return targetExecutable.getReference().equals(invocation.getExecutable());
    }

    private void extractAllPaths(ArtifactData treeNode, List<Map<String, Object>> currentPath,
            List<List<Map<String, Object>>> allPaths) {

        // Agregar el nodo actual al path
        Map<String, Object> nodeInfo = new LinkedHashMap<>();
        nodeInfo.put("type", treeNode.getNodeType());
        nodeInfo.put("methodName", treeNode.getArtifactName());
        nodeInfo.put("className", treeNode.getClassName());
        nodeInfo.put("qualifiedClassName", treeNode.getQualifierName());
        nodeInfo.put("invocationTarget", treeNode.getTarget());
        nodeInfo.put("invocationClass", treeNode.getClassName());
        nodeInfo.put("fileName", treeNode.getFilePath());
        nodeInfo.put("lineNumber", treeNode.getLineNumber());
        nodeInfo.put("packageName", treeNode.getPackageName());
        nodeInfo.put("arguments", treeNode.getParameters());

        List<Map<String, Object>> newPath = new ArrayList<>(currentPath);
        newPath.add(nodeInfo);
        List<ArtifactData> callers = treeNode.getCallers();

        if (callers == null || callers.isEmpty()) {
            // Es una hoja, agregar el path completo
            allPaths.add(newPath);
        } else {
            // Continuar recursivamente con cada caller
            for (ArtifactData caller : callers) {
                extractAllPaths(caller, newPath, allPaths);
            }
        }
    }
}
