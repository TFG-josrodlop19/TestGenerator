package com.josrodlop19.javaAnalyzer;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.reference.CtTypeReference;

public class OutputDataBuilder {
    public static ArtifactData extractArtifactData(CtInvocation<?> invocation, ClassLoader classLoader) {
        if (invocation == null) {
            throw new IllegalStateException("Target invocation not found.");
        }

        ArtifactData data = new ArtifactData();

        // Get class name
        data.setClassName(invocation.getPosition().getFile().getName()
                .replace(".java", ""));
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
        List<Map<String, String>> paramsData = new ArrayList<>();

        // Get the function declaration to extract parameter names and types
        CtExecutable<?> functionDeclaration = invocation.getExecutable().getDeclaration();
        List<CtExpression<?>> arguments = invocation.getArguments();

        if (functionDeclaration != null) {
            // Use Spoon declaration to extract parameter names and types
            ParamsProcessor.extractParamsFromSpoonDeclaration(functionDeclaration, arguments, paramsData);
        } else {
            // If no declaration is found, use reflection
            ParamsProcessor.extractParamsFromReflection(arguments, paramsData, invocation,
                    invocation.getExecutable().getSimpleName(), classLoader);
        }

        data.setParameters(paramsData);
        return data;
    }
}
