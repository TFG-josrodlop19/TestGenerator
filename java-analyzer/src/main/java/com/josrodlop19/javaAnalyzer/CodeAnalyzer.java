package com.josrodlop19.javaAnalyzer;

import java.io.File;
import java.io.IOException;
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
import spoon.reflect.code.CtAbstractInvocation;
import spoon.reflect.code.CtConstructorCall;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtType;
import spoon.reflect.visitor.filter.TypeFilter;

@Getter
@Setter
public class CodeAnalyzer {
    // Input parameters
    private String filePath;
    private Integer targetLine;
    private String targetName;
    private String pomPath;

    @Setter(AccessLevel.PRIVATE)
    private CtModel AST;

    // Attribute to store target method invocation
    @Setter(AccessLevel.PRIVATE)
    @Getter(AccessLevel.PRIVATE)
    private CtAbstractInvocation<?> targetInvocation;

    // Attribute to store artifact data
    @Setter(AccessLevel.PRIVATE)
    private ArtifactData artifactData;

    @Setter(AccessLevel.PRIVATE)
    private ArtifactData callStack;

    private List<List<Map<String, Object>>> allCallPaths;

    public CodeAnalyzer(String pomPath) {
        this.pomPath = pomPath;
    }

    public CodeAnalyzer(String pomPath, String filePath, Integer targetLine, String targetName) {
        this.pomPath = pomPath;
        this.filePath = filePath;
        this.targetLine = targetLine;
        this.targetName = targetName;
    }

    public void processCode() {
        // Main method to process the code
        findFunctionInvocation();
        if (this.targetInvocation != null) {
            ArtifactData artifactData = OutputDataBuilder.extractArtifactData(this.targetInvocation);
            this.setArtifactData(artifactData);
            // extractCallStack();
            StackCallProcessor stackCallProcessor = new StackCallProcessor(this.getTargetInvocation(), this.getAST());
            stackCallProcessor.extractCallStack();
            this.setCallStack(stackCallProcessor.getCallTree());
            this.setAllCallPaths(stackCallProcessor.getAllCallPaths());
        }
    }

    public void extractAST() {
        SpoonAPI launcher = new MavenLauncher(this.pomPath, MavenLauncher.SOURCE_TYPE.APP_SOURCE, true);

        // Reads the file and builds the AST
        launcher.getEnvironment().setLevel("ALL");
        launcher.getEnvironment().setAutoImports(true);

        String[] classpath = launcher.getEnvironment().getSourceClasspath();

        // Manually create the classloader to be able to read method declarations in
        // dependencies
        SpoonClassLoader.getInstance().setClassLoader(classpath);

        launcher.buildModel();
        this.setAST(launcher.getModel());
    }

    private void findFunctionInvocation() {
        String canonicalTargetPath;
        try {
            canonicalTargetPath = new File(this.getFilePath()).getCanonicalPath();
        } catch (IOException e) {
            throw new RuntimeException("Error obtaining canonical path for the target file: " + this.getFilePath(), e);
        }

        // Iterate through all types (classes) in the AST to find the target invocation
        for (CtType<?> node : this.getAST().getAllTypes()) {
            if (node.getPosition().isValidPosition()) {
                try {
                    String nodeCanonicalPath = node.getPosition().getFile().getCanonicalPath();

                    if (nodeCanonicalPath.equals(canonicalTargetPath)) {
                        // Get all invocations in the current type
                        List<CtAbstractInvocation<?>> invocationsInClass = node
                                .getElements(new TypeFilter<>(CtAbstractInvocation.class));

                        CtAbstractInvocation<?> foundInvocation = findFunctionInsideCtType(invocationsInClass);

                        if (foundInvocation != null) {
                            this.setTargetInvocation(foundInvocation);
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

    private CtAbstractInvocation<?> findFunctionInsideCtType(List<CtAbstractInvocation<?>> allInvocationsInNode) {
        for (CtAbstractInvocation<?> invocation : allInvocationsInNode) {
            if (invocation.getPosition().isValidPosition() &&
                    invocation.getPosition().getLine() == this.targetLine) {

                // Get the invocation name based on its type (method or constructor)
                String invocationName = getInvocationName(invocation);

                if (invocationName.equals(this.targetName)) {
                    return invocation;
                }
            }
        }
        return null;
    }

    // Method to get the name of the invocation, handling different types
    private String getInvocationName(CtAbstractInvocation<?> invocation) {
        if (invocation instanceof CtInvocation) {
            // For methods: use getSimpleName()
            return ((CtInvocation<?>) invocation).getExecutable().getSimpleName();
        } else if (invocation instanceof CtConstructorCall) {
            // For constructors: use the class name
            return ((CtConstructorCall<?>) invocation).getType().getSimpleName();
        }
        return "";
    }

    public String getCompleteDataAsString() {

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        Map<String, Object> completeData = new LinkedHashMap<>();
        completeData.put("artifactData", this.artifactData);
        // completeData.put("callStack", this.callStack);
        completeData.put("allCallPaths", this.allCallPaths);
        String jsonOutput = gson.toJson(completeData);
        return jsonOutput;
    }
}