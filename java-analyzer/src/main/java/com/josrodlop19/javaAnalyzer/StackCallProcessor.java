package com.josrodlop19.javaAnalyzer;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import lombok.AccessLevel;
import lombok.Getter;
import lombok.Setter;
import spoon.reflect.CtModel;
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

    private Map<String, CtMethod<?>> methodMap;
    private Map<String, List<CtInvocation<?>>> methodInvocations;
    private ArtifactData callTree;
    private List<List<Map<String, Object>>> allCallPaths;

    public StackCallProcessor(CtInvocation<?> targetInvocation, CtModel AST) {
        this.targetInvocation = targetInvocation;
        this.AST = AST;
        this.methodMap = new LinkedHashMap<>();
        this.methodInvocations = new LinkedHashMap<>();
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

        // Recorrer todos los tipos en el AST
        for (CtType<?> type : this.getAST().getAllTypes()) {
            // Procesar todos los métodos del tipo
            for (CtMethod<?> method : type.getMethods()) {
                String methodKey = createSignature(method);
                this.methodMap.put(methodKey, method);

                // Encontrar todas las invocaciones dentro de este método
                List<CtInvocation<?>> invocations = method.getElements(new TypeFilter<>(CtInvocation.class));
                this.methodInvocations.put(methodKey, invocations);
            }

            // También procesar constructores
            List<CtConstructor<?>> constructors = type.getElements(new TypeFilter<>(CtConstructor.class));
            for (CtConstructor<?> constructor : constructors) {
                String constructorKey = createSignature(constructor);
                // Los constructores también pueden tener invocaciones
                List<CtInvocation<?>> invocations = constructor.getElements(new TypeFilter<>(CtInvocation.class));
                this.methodInvocations.put(constructorKey, invocations);
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

    private ArtifactData buildCallTree(CtInvocation<?> currentInvocation, Map<String, ArtifactData> visited) {

        ArtifactData treeNode = new ArtifactData();

        // Obtener el método que contiene la invocación actual
        // TODO: revisar el caso en el que haya un constructor en lugar de método
        CtMethod<?> currentMethod = currentInvocation.getParent(CtMethod.class);

        if (currentMethod == null) {
            // Podría estar en un constructor
            CtConstructor<?> constructor = currentInvocation.getParent(CtConstructor.class);
            if (constructor != null) {
                treeNode = OutputDataBuilder.createContructorTreeNode(constructor);
            } else {
                // Nodo raíz o sin contexto
                treeNode = OutputDataBuilder.createRootTreeNode(currentInvocation);
            }
            return treeNode;
        }

        String currentMethodSignature = createSignature(currentMethod);
        if (visited.containsKey(currentMethodSignature)) {
            return visited.get(currentMethodSignature);
        }

        String currentMethodKey = createSignature(currentMethod);

        // Crear información del nodo actual

        treeNode = OutputDataBuilder.createMethodTreeNode(currentMethod);

        // Crear nueva lista para esta rama
        // Map<String, Object> newVisited = new LinkedHashMap<>(visited);
        // newVisited.put(currentMethodKey, currentMethod);

        visited.put(currentMethodKey, treeNode);

        // Buscar TODOS los métodos que llaman al método actual
        List<ArtifactData> callers = findAllCallers(currentMethod, visited);
        treeNode.getCallers().addAll(callers);

        return treeNode;
    }

    private List<ArtifactData> findAllCallers(CtMethod<?> targetMethod, Map<String, ArtifactData> visitedMethods) {

        List<ArtifactData> callers = new ArrayList<>();

        // Buscar en todas las invocaciones de todos los métodos
        for (Map.Entry<String, List<CtInvocation<?>>> entry : this.methodInvocations.entrySet()) {
            String methodKey = entry.getKey();
            List<CtInvocation<?>> invocations = entry.getValue();

            // Saltar métodos ya visitados
            if (visitedMethods.containsKey(methodKey)) {
                continue;
            }

            for (CtInvocation<?> invocation : invocations) {
                if (isCallingTargetMethod(invocation, targetMethod)) {
                    // Encontramos un caller, agregar al árbol recursivamente
                    ArtifactData callerNode = buildCallTree(invocation, visitedMethods);
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
