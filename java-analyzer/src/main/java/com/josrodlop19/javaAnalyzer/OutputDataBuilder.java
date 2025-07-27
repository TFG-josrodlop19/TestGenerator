package com.josrodlop19.javaAnalyzer;

import java.io.IOException;
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

public class OutputDataBuilder {
    public static ArtifactData extractArtifactData(CtInvocation<?> invocation) {
        if (invocation == null) {
            throw new IllegalStateException("Target invocation not found.");
        }

        ArtifactData data = new ArtifactData();

        data.setClassName(invocation.getPosition().getFile().getName().replace(".java", ""));
        data.setLineNumber(invocation.getPosition().getLine());

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

        // Get wheather the method is static or not
        boolean isStatic = invocation.getExecutable().isStatic();
        data.setIsStatic(isStatic);

        // Get parameters

        List<Map<String, String>> paramsData;
        // Get the function declaration to extract parameter names and types
        CtExecutable<?> functionDeclaration = invocation.getExecutable().getDeclaration();
        List<CtExpression<?>> arguments = invocation.getArguments();

        if (functionDeclaration != null) {
            // Use Spoon declaration to extract parameter names and types
            paramsData = ParamsProcessor.extractParamsFromSpoonDeclaration(functionDeclaration, arguments);
        } else {
            // If no declaration is found, use reflection
            paramsData = ParamsProcessor.extractParamsFromReflection(arguments, invocation,
                    invocation.getExecutable().getSimpleName());
        }

        data.setParameters(paramsData);
        return data;
    }


    public static ArtifactData createMethodTreeNode(CtMethod<?> method) {
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

        // Get the function declaration to extract parameter names and types
        List<Map<String, String>> paramsData = argumentsInfo(method);
        treeNode.setParameters(paramsData);

        return treeNode;
    }


    // TODO: Mirar si cambiar los parametros de ubicacion a los de la llamada y no los del metodo (mirar en todos lo de TreeNode)
    public static ArtifactData createConstructorTreeNode(CtConstructor<?> constructor) {
        ArtifactData treeNode = new ArtifactData();
        treeNode.setFilePath(constructor.getPosition().getFile().getAbsolutePath());
        treeNode.setClassName(constructor.getDeclaringType().getSimpleName());
        treeNode.setLineNumber(constructor.getPosition().getLine());

        treeNode.setNodeType(constructor.getClass().getSimpleName());
        treeNode.setQualifierType(constructor.getDeclaringType().getQualifiedName());
        treeNode.setQualifierName(constructor.getDeclaringType().getSimpleName());

        // Get the function declaration to extract parameter names and types
        List<Map<String, String>> paramsData = argumentsInfo(constructor);

        treeNode.setParameters(paramsData);
        return treeNode;
    }

    public static ArtifactData createRootTreeNode(CtAbstractInvocation<?> invocation) {
        ArtifactData treeNode = new ArtifactData();
        treeNode.setFilePath(invocation.getPosition().getFile().getAbsolutePath());
        treeNode.setLineNumber(invocation.getPosition().getLine());
        treeNode.setClassName(invocation.getPosition().getFile().getName().replace(".java", ""));

        treeNode.setNodeType("Root");
        treeNode.setTarget(invocation.getExecutable().getSimpleName());
        treeNode.setQualifierName(invocation.getExecutable().getDeclaringType().getQualifiedName());
        treeNode.setQualifierType(invocation.getExecutable().getDeclaringType().getSimpleName());

        // Get parameters
        List<Map<String, String>> paramsData;
        // Get the function declaration to extract parameter names and types
        CtExecutable<?> functionDeclaration = invocation.getExecutable().getDeclaration();
        List<CtExpression<?>> arguments = invocation.getArguments();

        if (functionDeclaration != null) {
            // Use Spoon declaration to extract parameter names and types
            paramsData = ParamsProcessor.extractParamsFromSpoonDeclaration(functionDeclaration, arguments);
        } else {
            // If no declaration is found, use reflection
            paramsData = ParamsProcessor.extractParamsFromReflection(arguments, invocation,
                    invocation.getExecutable().getSimpleName());
        }

        treeNode.setParameters(paramsData);
        return treeNode;
    }
    

    private static List<Map<String, String>> argumentsInfo(CtExecutable<?> executable) {
        List<CtParameter<?>> arguments = executable.getParameters();
        List<Map<String, String>> argumentsData = new ArrayList<>();
        for (int i = 0; i < arguments.size(); i++) {
            CtParameter<?> arg = arguments.get(i);
            Map<String, String> argInfo = new LinkedHashMap<>();
            argInfo.put("position", String.valueOf(i));
            argInfo.put("value", arg.toString());
            argInfo.put("type", arg.getType() != null ? arg.getType().getQualifiedName() : "Unknown");
            argumentsData.add(argInfo);
        }
        return argumentsData;
    }
}
