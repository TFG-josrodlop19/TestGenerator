package com.josrodlop19.javaAnalyzer;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import lombok.AccessLevel;
import lombok.Getter;
import lombok.Setter;
import spoon.reflect.CtModel;
import spoon.reflect.code.CtAbstractInvocation;
import spoon.reflect.code.CtConstructorCall;
import spoon.reflect.code.CtStatement;
import spoon.reflect.code.CtVariableRead;
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
    private CtAbstractInvocation<?> targetInvocation;
    @Setter(AccessLevel.PRIVATE)
    private CtModel AST;

    // Executable is the superclass for both CtMethod and CtConstructor
    private Map<String, CtExecutable<?>> executables;
    // CtAbstractInvocation is the superclass for both CtInvocation and
    // CtConstructorCall
    private Map<String, List<CtAbstractInvocation<?>>> methodInvocations;
    private Map<String, List<CtConstructorCall<?>>> constructorCalls;
    private ArtifactData callTree;
    private List<List<Map<String, Object>>> allCallPaths;

    public StackCallProcessor(CtAbstractInvocation<?> targetInvocation, CtModel AST) {
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

        // Save all methods and their invocations in the AST
        collectMethodsAndInvocations();

        // Build the call tree with cycle control by path
        ArtifactData callTree = buildCallTree(this.targetInvocation, new ArrayList<>());

        // Add the call tree to artifactData
        this.setCallTree(callTree);

        // Also generate all possible paths as a list
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

        // Get the parent executable (method or constructor) of the current invocation
        CtExecutable<?> currentMethod = currentInvocation.getParent(CtExecutable.class);

        if (currentMethod == null) {
            treeNode = OutputDataBuilder.createRootTreeNode(currentInvocation);
            return treeNode;
        }

        String currentMethodSignature = createSignature(currentMethod);
        boolean isCyclic = currentPath.contains(currentMethodSignature);

        // Create node information using normal functions
        if (currentMethod instanceof CtMethod<?>) {
            treeNode = OutputDataBuilder.createMethodTreeNode((CtMethod<?>) currentMethod);
        } else if (currentMethod instanceof CtConstructor<?>) {
            treeNode = OutputDataBuilder.createConstructorTreeNode((CtConstructor<?>) currentMethod);
        }

        // If it's cyclic, modify the node AFTER creating it
        if (isCyclic) {
            treeNode.setNodeType("CyclicCall");

            // Modify the artifact name to indicate cycle
            String originalName = treeNode.getArtifactName();
            if (originalName != null) {
                treeNode.setArtifactName(originalName + " [CYCLE DETECTED]");
            } else {
                treeNode.setArtifactName("<init> [CYCLE DETECTED]");
            }

            // No search further to avoid infinite loops
            treeNode.setCallers(new ArrayList<>());
            Boolean usesTargetFields = checkIfMethodUsesItsParameters(currentMethod);
            treeNode.setUsesParameters(usesTargetFields);
            return treeNode;
        }

        // If not cyclic, continue building the tree
        List<String> newPath = new ArrayList<>(currentPath);
        newPath.add(currentMethodSignature);

        List<ArtifactData> callers = findAllCallers(currentMethod, newPath);
        treeNode.getCallers().addAll(callers);
        Boolean usesParameters = checkIfMethodUsesItsParameters(currentMethod);
        treeNode.setUsesParameters(usesParameters);

        return treeNode;
    }

    private List<ArtifactData> findAllCallers(CtExecutable<?> targetMethod, List<String> currentPath) {
        List<ArtifactData> callers = new ArrayList<>();

        // Search all invocations of all methods
        for (Map.Entry<String, List<CtAbstractInvocation<?>>> entry : this.methodInvocations.entrySet()) {
            List<CtAbstractInvocation<?>> invocations = entry.getValue();

            for (CtAbstractInvocation<?> invocation : invocations) {
                if (isCallingTargetExecutable(invocation, targetMethod)) {
                    // Found a caller, add to the tree recursively
                    // Each invocation is processed independently with its own path
                    ArtifactData callerNode = buildCallTree(invocation, currentPath);

                    callers.add(callerNode);
                }
            }
        }

        return callers;
    }

    private Boolean checkIfMethodUsesItsParameters(CtExecutable<?> targetMethod) {
        // Get method parameters
        List<CtParameter<?>> methodParameters = targetMethod.getParameters();
        if (methodParameters.isEmpty())
            return false; // If there is no parameters, fuzzer only need one iteration

        CtStatement body = targetMethod.getBody();
        if (body == null)
            return false;

        // Find all references to variables
        List<CtVariableRead<?>> varReads = body.getElements(new TypeFilter<>(CtVariableRead.class));

        // Create set of parameter names for quick lookup
        Set<String> parameterNames = methodParameters.stream()
                .map(CtParameter::getSimpleName)
                .collect(Collectors.toSet());

        // Verify if params are used
        for (CtVariableRead<?> varRead : varReads) {
            String varName = varRead.getVariable().getSimpleName();
            if (parameterNames.contains(varName)) {
                return true; // At least one parameter is used
            }
        }

        return false;
    }

    private Boolean isCallingTargetExecutable(CtAbstractInvocation<?> invocation, CtExecutable<?> targetExecutable) {
        return targetExecutable.getReference().equals(invocation.getExecutable());
    }

    private void extractAllPaths(ArtifactData treeNode, List<Map<String, Object>> currentPath,
            List<List<Map<String, Object>>> allPaths) {

        // Add the current node to the path
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
        nodeInfo.put("usesParameters", treeNode.getUsesParameters());
        nodeInfo.put("constructorParameters", treeNode.getConstructorParameters());

        List<Map<String, Object>> newPath = new ArrayList<>(currentPath);
        newPath.add(nodeInfo);
        List<ArtifactData> callers = treeNode.getCallers();

        if (callers == null || callers.isEmpty()) {
            // It's a leaf, add the full path
            allPaths.add(newPath);
        } else {
            // Continue recursively with each caller
            for (ArtifactData caller : callers) {
                extractAllPaths(caller, newPath, allPaths);
            }
        }
    }
}
