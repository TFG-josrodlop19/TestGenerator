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

    // Executable is the superclass for both CtMethod and CtConstructor
    private Map<String, CtExecutable<?>> executables;
    // CtAbstractInvocation is the superclass for both CtInvocation and CtConstructorCall
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

        // Recopilar todos los métodos e invocaciones del AST
        collectMethodsAndInvocations();

        // Construir el árbol de llamadas con control de ciclos por path
        ArtifactData callTree = buildCallTree(this.targetInvocation, new ArrayList<>());

        // Agregar el árbol de llamadas a artifactData
        this.setCallTree(callTree);

        // También generar todas las rutas posibles como lista
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
                List<CtAbstractInvocation<?>> invocations = executable
                        .getElements(new TypeFilter<>(CtAbstractInvocation.class));
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

    private ArtifactData buildCallTree(CtAbstractInvocation<?> currentInvocation, List<String> currentPath) {
        ArtifactData treeNode = new ArtifactData();

        // Obtener el método que contiene la invocación actual
        CtExecutable<?> currentMethod = currentInvocation.getParent(CtExecutable.class);

        if (currentMethod == null) {
            treeNode = OutputDataBuilder.createRootTreeNode(currentInvocation);
            return treeNode;
        }

        String currentMethodSignature = createSignature(currentMethod);
        boolean isCyclic = currentPath.contains(currentMethodSignature);

        // Crear información del nodo usando las funciones normales
        if (currentMethod instanceof CtMethod<?>) {
            treeNode = OutputDataBuilder.createMethodTreeNode((CtMethod<?>) currentMethod);
        } else if (currentMethod instanceof CtConstructor<?>) {
            treeNode = OutputDataBuilder.createConstructorTreeNode((CtConstructor<?>) currentMethod);
        }

        // Si es cíclico, modificar el nodo DESPUÉS de crearlo
        if (isCyclic) {
            treeNode.setNodeType("CyclicCall");

            // Modificar el nombre del artefacto para indicar ciclo
            String originalName = treeNode.getArtifactName();
            if (originalName != null) {
                treeNode.setArtifactName(originalName + " [CYCLE DETECTED]");
            } else {
                treeNode.setArtifactName("<init> [CYCLE DETECTED]");
            }

            // No buscar callers para cortar la recursión
            treeNode.setCallers(new ArrayList<>());
            return treeNode;
        }

        // Si no es cíclico, continuar normalmente
        List<String> newPath = new ArrayList<>(currentPath);
        newPath.add(currentMethodSignature);

        List<ArtifactData> callers = findAllCallers(currentMethod, newPath);
        treeNode.getCallers().addAll(callers);

        return treeNode;
    }

    private List<ArtifactData> findAllCallers(CtExecutable<?> targetMethod, List<String> currentPath) {
        List<ArtifactData> callers = new ArrayList<>();

        // Buscar en todas las invocaciones de todos los métodos
        for (Map.Entry<String, List<CtAbstractInvocation<?>>> entry : this.methodInvocations.entrySet()) {
            List<CtAbstractInvocation<?>> invocations = entry.getValue();

            for (CtAbstractInvocation<?> invocation : invocations) {
                if (isCallingTargetExecutable(invocation, targetMethod)) {
                    // Encontramos un caller, agregar al árbol recursivamente
                    // Cada invocación se procesa independientemente con su propio path
                    ArtifactData callerNode = buildCallTree(invocation, currentPath);
                    callers.add(callerNode);
                }
            }
        }

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
        nodeInfo.put("nodeType", treeNode.getNodeType());
        nodeInfo.put("artifactName", treeNode.getArtifactName());
        nodeInfo.put("className", treeNode.getClassName());
        nodeInfo.put("qualifierName", treeNode.getQualifierName());
        nodeInfo.put("qualifierType", treeNode.getQualifierType());
        nodeInfo.put("target", treeNode.getTarget());
        nodeInfo.put("filePath", treeNode.getFilePath());
        nodeInfo.put("lineNumber", treeNode.getLineNumber());
        nodeInfo.put("packageName", treeNode.getPackageName());
        nodeInfo.put("parameters", treeNode.getParameters());
        nodeInfo.put("isStatic", treeNode.getIsStatic());
        nodeInfo.put("isPublic", treeNode.getIsPublic());
        nodeInfo.put("constructorParameters", treeNode.getConstructorParameters());

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
