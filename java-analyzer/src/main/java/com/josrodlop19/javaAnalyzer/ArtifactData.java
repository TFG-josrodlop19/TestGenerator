package com.josrodlop19.javaAnalyzer;

import java.util.List;
import java.util.Map;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class ArtifactData {
    // Location atributes
    private String filePath;
    private int lineNumber;
    private String className;

    // Method atributes
    private String nodeType;
    private String qualifierType;
    private String qualifierName;
    private String artifactName;
    private String artifactSignature;
    private String target;
    private Boolean isStatic;
    private List<Map<String, String>> parameters;

}
