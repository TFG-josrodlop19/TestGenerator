package com.josrodlop19.javaAnalyzer;

import java.io.File;
import java.io.IOException;
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
        launcher.addInputResource(this.filePath);
        launcher.getEnvironment().setLevel("ALL"); 
        // TODO: set compliance level automatically depending on Java version

        launcher.buildModel();
        this.AST = launcher.getModel();
    }

    private void findFunctionInvocation() {
        String canonicalTargetPath;
        try {
            canonicalTargetPath = new File(this.filePath).getCanonicalPath();
        } catch (IOException e) {
            throw new RuntimeException("Error obtaining canonical path for the target file: " + this.filePath, e);
        }

        // 1. Itera por todas las clases que Spoon ha encontrado en el proyecto.
        for (CtType<?> node : this.AST.getAllTypes()) {
            if (node.getPosition().isValidPosition()) {
                try {
                    String nodeCanonicalPath = node.getPosition().getFile().getCanonicalPath();

                    if (nodeCanonicalPath.equals(canonicalTargetPath)) {
                        List<CtInvocation<?>> invocationsInClass = node
                                .getElements(new TypeFilter<>(CtInvocation.class));
                        CtInvocation<?> foundInvocation = findFunctionInsideCtType(invocationsInClass);
                        if (foundInvocation != null) {
                            this.targetInvocation = foundInvocation;
                            break;
                        }
                    }
                } catch (IOException e) {
                    // Si hay un error al obtener la ruta de un nodo, simplemente lo ignoramos y
                    // continuamos.
                    continue;
                }
            } else {
                // If not valid position, we skip this type
                // A valid position means the type has a valid file associated with it, aka, code actually exists.
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

        artifactData = new LinkedHashMap<>();

        // Get artifact type and name (name is not really necessary)
        artifactData.put("artifactType", this.targetInvocation.getClass().getSimpleName());
        artifactData.put("methodName", this.targetInvocation.getExecutable().getSimpleName());

        // Get qualifier type
        CtExpression<?> target = this.targetInvocation.getTarget();
        if (target != null) {
            CtTypeReference<?> qualifierTypeRef = target.getType();
            String qualifierType = (qualifierTypeRef != null) ? qualifierTypeRef.getQualifiedName() : "UNRESOLVED_TYPE";
            artifactData.put("qualifierType", qualifierType);
            artifactData.put("qualifierNameInCode", target.toString());
        } else {
            // If there is no target, it is a local call. EX: myMethod();
            artifactData.put("qualifierType", "Local call");
        }

        // Get parameters
        List<Map<String, String>> paramsData = new ArrayList<>();

        // Get the function declaration to extract parameter names and types
        CtExecutable<?> functionDeclaration = this.targetInvocation.getExecutable().getDeclaration();
        List<CtExpression<?>> arguments = this.targetInvocation.getArguments();
        for (int i = 0; i < arguments.size(); i++) {
            CtExpression<?> param = arguments.get(i);
            CtTypeReference<?> paramType = param.getType();
            // TODO: return parameter types as well as parameter types in declaration

            Map<String, String> paramInfo = new HashMap<>();
            paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");

            if (functionDeclaration != null) {
                List<CtParameter<?>> declarationParams = functionDeclaration.getParameters();
                if (i < declarationParams.size()) {
                    CtTypeReference<?> declarationType = declarationParams.get(i).getType();
                    paramInfo.put("parameterName", declarationParams.get(i).getSimpleName());
                    paramInfo.put("typeAtDeclaration",
                            (declarationType != null) ? declarationType.getQualifiedName() : "UNRESOLVED_TYPE");
                } else {
                    paramInfo.put("possibleArray", "true");
                }
            } else {
                // If no declaration is available, use a generic type
                paramInfo.put("typeAtDeclaration", "UNRESOLVED_TYPE");
            }

            paramsData.add(paramInfo);
        }
        artifactData.put("parameters", paramsData);

    }

    public void getDataAsString() {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String jsonOutput = gson.toJson(this.artifactData);
        System.out.println(jsonOutput);
    }

}
