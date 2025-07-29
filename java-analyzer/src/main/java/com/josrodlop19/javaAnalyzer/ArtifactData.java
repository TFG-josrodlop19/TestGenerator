package com.josrodlop19.javaAnalyzer;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class ArtifactData {
    // Location atributes
    private String filePath;
    private String className;
    private int lineNumber;
    private String packageName;

    // Method atributes
    private String nodeType;
    private String qualifierType;
    private String qualifierName;
    private String artifactName;
    private String artifactSignature;
    private String target;
    private Boolean isStatic;
    private Boolean isPublic;
    private List<Map<String, String>> parameters;

    // Call tree atributes
    private List<ArtifactData> callers;

    public ArtifactData() {
        // Default constructor
        this.callers = new ArrayList<>();
    }
}
