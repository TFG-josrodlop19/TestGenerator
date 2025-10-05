package com.josrodlop19.javaAnalyzer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

import spoon.SpoonException;

public class NegativeCasestTest {
    
    @Test
    public void testWrongPomPath() {
        String pomPath = "non_existent_pom.xml";
        CodeAnalyzer analyzer = new CodeAnalyzer(pomPath);
        assertThrows(SpoonException.class, () -> {
            analyzer.extractAST();
        }, "Expected extractAST to throw SpoonException, but it didn't");
    }

    @Test
    public void testNotSupportedArtifact() {
        // Get absolute paths
        String projectRoot = System.getProperty("user.dir");
        String parentDir = new java.io.File(projectRoot).getParent();
        
        String pomPath = parentDir + "/vulnerableCodeExamples/VulnerableProject1/pom.xml";
        String javaFilePath = parentDir + "/vulnerableCodeExamples/VulnerableProject1/src/main/java/com/example/JsonProcessor.java";
        
        CodeAnalyzer analyzer = new CodeAnalyzer(pomPath);
        analyzer.extractAST();
        analyzer.setFilePath(javaFilePath);
        analyzer.setTargetLine(8);
        analyzer.setTargetName("ObjectMapper");
        analyzer.processCode();
        String data = analyzer.getCompleteDataAsString();
        assertEquals("{}", data, "Expected empty JSON object for unsupported artifact, but got: " + data);
    }

    @Test
    public void testArtifactDoNotExists() {
        // Get absolute paths
        String projectRoot = System.getProperty("user.dir");
        String parentDir = new java.io.File(projectRoot).getParent();
        
        String pomPath = parentDir + "/vulnerableCodeExamples/VulnerableProject1/pom.xml";
        String javaFilePath = parentDir + "/vulnerableCodeExamples/VulnerableProject1/src/main/java/com/example/JsonProcessor.java";
        
        CodeAnalyzer analyzer = new CodeAnalyzer(pomPath);
        analyzer.extractAST();
        analyzer.setFilePath(javaFilePath);
        analyzer.setTargetLine(20);
        analyzer.setTargetName("NonExistentMethod");
        analyzer.processCode();
        String data = analyzer.getCompleteDataAsString();
        assertEquals("{}", data, "Expected empty JSON object for unsupported artifact, but got: " + data);
    }

    @Test
    public void testWrongFilePath() {
        // Get absolute paths
        String projectRoot = System.getProperty("user.dir");
        String parentDir = new java.io.File(projectRoot).getParent();
        
        String pomPath = parentDir + "/vulnerableCodeExamples/VulnerableProject1/pom.xml";
        String javaFilePath = "non_existent_file.java";
        
        CodeAnalyzer analyzer = new CodeAnalyzer(pomPath);
        analyzer.extractAST();
        analyzer.setFilePath(javaFilePath);
        analyzer.setTargetLine(20);
        analyzer.setTargetName("readValue");
        String data = analyzer.getCompleteDataAsString();
        assertEquals("{}", data, "Expected empty JSON object for unsupported artifact, but got: " + data);
    }
}
