package com.josrodlop19.javaAnalyzer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

public class ReadValueTest {
    
    private static ArtifactData artifactData;
    private static List<List<Map<String, Object>>> allCallPaths;
    
    @BeforeAll
    public static void setup() {
        // Get absolute paths
        String projectRoot = System.getProperty("user.dir");
        String parentDir = new java.io.File(projectRoot).getParent();
        
        String pomPath = parentDir + "/vulnerableCodeExamples/VulnerableProject1/pom.xml";
        String javaFilePath = parentDir + "/vulnerableCodeExamples/VulnerableProject1/src/main/java/com/example/JsonProcessor.java";
        
        CodeAnalyzer analyzer = new CodeAnalyzer(pomPath);
        analyzer.extractAST();
        analyzer.setFilePath(javaFilePath);
        analyzer.setTargetLine(24);
        analyzer.setTargetName("readValue");
        analyzer.processCode();
        artifactData = analyzer.getArtifactData();
        allCallPaths = analyzer.getAllCallPaths();
    }


    // Tests for artifactData corresponding to the method call 'readValue' in JsonProcessor.java
    @Test
    public void testArtifactDataNotNull() {
        assertTrue(artifactData != null, "There should be an artifact found for the given target.");
    }

    @Test
    public void testArtifactDataBasicData() {
        assertEquals("JsonProcessor", artifactData.getClassName(), "Artifact class name should be 'JsonProcessor' for the given target.");
        assertEquals("readValue", artifactData.getArtifactName(), "Artifact method name should be 'readValue' for the given target.");
        assertEquals(24, artifactData.getLineNumber(), "Artifact line number should be 24 for the given target.");
        assertEquals("CtInvocationImpl", artifactData.getNodeType(), "The artifact should be a method invocation (CtInvocationImpl) for the given target.");
        assertFalse(artifactData.getIsStatic(), "The method 'readValue' is not static, so isStatic should be false.");
    }

    @Test
    public void testArtifactDataQualifier() {
        assertEquals("com.fasterxml.jackson.databind.ObjectMapper", artifactData.getQualifierType(), "The qualifier type should be 'ObjectMapper' for the 'readValue' method.");
        assertEquals("this.mapper", artifactData.getQualifierName(), "The qualifier name should be 'this.mapper' for the 'readValue' method.");
    }

    @Test
    public void testArtifactDataParameters() {
        assertEquals(2, artifactData.getParameters().size(), "The 'readValue' method should have 2 parameters.");
        // Parameter 1
        assertEquals("java.lang.String", artifactData.getParameters().get(0).get("typeAtCall"), "Parameter 1 type at call should be 'java.lang.String'.");
        assertEquals("arg0", artifactData.getParameters().get(0).get("parameterName"), "Parameter 1 name should be 'arg0'.");
        assertEquals("java.lang.String", artifactData.getParameters().get(0).get("typeAtDeclaration"), "Parameter 1 type at declaration should be 'java.lang.String'.");
        // Parameter 2
        assertEquals("java.lang.Class", artifactData.getParameters().get(1).get("typeAtCall"), "Parameter 2 type at call should be 'java.lang.Class'.");
        assertEquals("arg1", artifactData.getParameters().get(1).get("parameterName"), "Parameter 2 name should be 'arg1'.");
        assertEquals("java.lang.Class", artifactData.getParameters().get(1).get("typeAtDeclaration"), "Parameter 2 type at declaration should be 'java.lang.Class'.");
    }


    // Tests for call paths leading to 'readValue'
    @Test
    public void testCallPathsNotNull() {
        assertNotNull(allCallPaths, "The list of call paths should not be null.");
        assertEquals(4, allCallPaths.size(), "There should be 4 call paths leading to the target method.");
    }
    
    // Tests for call path 1: processJson -> SecondMethodCall constructor -> main
    
    
    @Test
    public void testCallPath1HasCorrectLength() {
        List<Map<String, Object>> callPath1 = allCallPaths.get(0);
        assertEquals(3, callPath1.size(), "Call path 1 should have 3 methods in the chain");
    }
    
    @Test
    public void testCallPath1ProcessJson() {
        Map<String, Object> processJsonMethod = allCallPaths.get(0).get(0);
        
        assertEquals("CtMethodImpl", processJsonMethod.get("nodeType"), "First method should be CtMethodImpl");
        assertEquals("processJson", processJsonMethod.get("artifactName"), "First method should be processJson");
        assertEquals("JsonProcessor", processJsonMethod.get("className"), "First method should belong to JsonProcessor class");
        assertEquals("com.example.JsonProcessor", processJsonMethod.get("qualifierType"), "First method qualifier type should be com.example.JsonProcessor");
        assertEquals(20, processJsonMethod.get("lineNumber"), "processJson method should be at line 20");
        assertEquals(false, processJsonMethod.get("isStatic"), "processJson should not be static");
        assertEquals(true, processJsonMethod.get("isPublic"), "processJson should be public");
        assertEquals(true, processJsonMethod.get("usesParameters"), "processJson should use parameters");
    }

    @Test
    public void testCallPath1ProcessJsonParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(0).get(0);
        List<Map<String, String>> parameters = (List<Map<String, String>>) processJsonMethod.get("parameters");
        assertEquals(1, parameters.size(), "processJson should have 1 parameter");
        
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String jsonInput", param1.get("value"), "First parameter should be 'String jsonInput'");
        assertEquals("java.lang.String", param1.get("type"), "First parameter type should be java.lang.String");
    }

    @Test
    public void testCallPath1ProcessJsonConstructorParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(0).get(0);
        List<Map<String, Object>> constructorParameters = (List<Map<String, Object>>) processJsonMethod.get("constructorParameters");
        assertEquals(1, constructorParameters.size(), "processJson should have 1 constructor parameter");

        Map<String, Object> param1 = constructorParameters.get(0);
        assertEquals("JsonProcessor", param1.get("className"), "First constructor parameter should be of type JsonProcessor");
        assertEquals("com.example.JsonProcessor", param1.get("qualifiedName"), "First constructor parameter qualified name should be com.example.JsonProcessor");
        assertEquals(true, param1.get("isPublic"), "First constructor parameter should be public");
        List<Map<String, Object>> parameters = (List<Map<String, Object>>) param1.get("parameters");
        assertNotNull(parameters, "Constructor parameters should not be null");
        assertEquals(0, parameters.size(), "First constructor parameter should have no parameters");
    }
    
    @Test
    public void testCallPath1SecondMethodCallConstructor() {
        Map<String, Object> constructorMethod = allCallPaths.get(0).get(1);
        
        assertEquals("CtConstructorImpl", constructorMethod.get("nodeType"), "Second method should be CtConstructorImpl");
        assertEquals("SecondMethodCall", constructorMethod.get("className"), "Second method should belong to SecondMethodCall class");
        assertEquals("com.example.SecondMethodCall", constructorMethod.get("qualifierType"), "Second method qualifier type should be com.example.SecondMethodCall");
        assertEquals(8, constructorMethod.get("lineNumber"), "SecondMethodCall constructor should be at line 8");
        assertEquals(true, constructorMethod.get("usesParameters"), "SecondMethodCall constructor should use parameters");
        assertEquals(true, constructorMethod.get("usesParameters"), "SecondMethodCall constructor should use parameters");
    }

    @Test
    public void testCallPath1SecondMethodCallConstructorParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(0).get(1);
        List<Map<String, Object>> parameters = (List<Map<String, Object>>) processJsonMethod.get("parameters");
        assertEquals(1, parameters.size(), "processJson should have 1 parameter");

        Map<String, Object> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("User jsonString", param1.get("value"), "First parameter should be 'User jsonString'");
        assertEquals("com.example.User", param1.get("type"), "First parameter type should be com.example.User");

        List<Map<String, Object>> constructor = (List<Map<String, Object>>) param1.get("constructor");
        assertEquals("User", constructor.get(0).get("className"), "First parameter should have 1 constructor");
        assertEquals(true, constructor.get(0).get("isPublic"), "First parameter constructor should be public");
        List<Map<String, Object>> constructorParams = (List<Map<String, Object>>) constructor.get(0).get("parameters");
        assertEquals(3, constructorParams.size(), "First parameter constructor should have 2 parameters");

        // Constructor Parameter 1
        assertEquals("id", constructorParams.get(0).get("name"), "First constructor parameter name should be 'id'");
        assertEquals("int", constructorParams.get(0).get("type"), "First constructor parameter type should be 'int'");

        // Constructor Parameter 2
        assertEquals("name", constructorParams.get(1).get("name"), "Second constructor parameter name should be 'name'");
        assertEquals("java.lang.String", constructorParams.get(1).get("type"), "Second constructor parameter type should be 'java.lang.String'");

        // Constructor Parameter 3
        assertEquals("data", constructorParams.get(2).get("name"), "Third constructor parameter name should be 'data'");
        assertEquals("com.example.Data", constructorParams.get(2).get("type"), "Third constructor parameter type should be 'com.example.Data'");
        List<Map<String, Object>> parameterConstructor = (List<Map<String, Object>>) constructorParams.get(2).get("parameterConstructors");
        assertEquals(1, parameterConstructor.size(), "Third constructor parameter should have 1 constructor");
        assertEquals("Data", parameterConstructor.get(0).get("className"), "Third constructor parameter constructor class name should be 'Data'");
        assertEquals(true, parameterConstructor.get(0).get("isPublic"), "Third constructor parameter constructor should be public");
        assertEquals("com.example.Data", parameterConstructor.get(0).get("qualifiedName"), "Third constructor parameter constructor qualified name should be 'com.example.Data'");
        List<Map<String, Object>> dataConstructorParams = (List<Map<String, Object>>) parameterConstructor.get(0).get("parameters");
        assertEquals(1, dataConstructorParams.size(), "Third constructor parameter constructor should have 1 parameter");
        assertEquals("data", dataConstructorParams.get(0).get("name"), "Data constructor parameter name should be 'data'");
        assertEquals("java.lang.Integer", dataConstructorParams.get(0).get("type"), "Data constructor parameter type should be 'java.lang.Integer'");
    }
    
    @Test
    public void testCallPath1Main() {
        Map<String, Object> mainMethod = allCallPaths.get(0).get(2);
        
        assertEquals("CtMethodImpl", mainMethod.get("nodeType"), "Third method should be CtMethodImpl");
        assertEquals("main", mainMethod.get("artifactName"), "Third method should be main");
        assertEquals("VulnerableApp", mainMethod.get("className"), "Third method should belong to VulnerableApp class");
        assertEquals("com.example.VulnerableApp", mainMethod.get("qualifierType"), "Third method qualifier type should be com.example.VulnerableApp");
        assertEquals(6, mainMethod.get("lineNumber"), "main method should be at line 6");
        assertEquals(true, mainMethod.get("isStatic"), "main should be static");
        assertEquals(true, mainMethod.get("isPublic"), "main should be public");
        assertEquals(false, mainMethod.get("usesParameters"), "main should not use parameters");
    }

    @Test
    public void testCallPath1MainParameters() {
        Map<String, Object> mainMethod = allCallPaths.get(0).get(2);
        List<Map<String, String>> parameters = (List<Map<String, String>>) mainMethod.get("parameters");
        assertEquals(1, parameters.size(), "main should not have any parameters");
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String[] args", param1.get("value"), "First parameter should be 'String[] args'");
        assertEquals("java.lang.String[]", param1.get("type"), "First parameter type should be java.lang.String[]");
    }
    
    // Tests for call path 2: processJson -> secondVulnerableMethodCall -> main
    
    @Test
    public void testCallPath2HasCorrectLength() {
        List<Map<String, Object>> callPath2 = allCallPaths.get(1);
        assertEquals(3, callPath2.size(), "Call path 2 should have 3 methods in the chain");
    }

    @Test
    public void testCallPath2ProcessJson() {
        Map<String, Object> processJsonMethod = allCallPaths.get(1).get(0);

        assertEquals("CtMethodImpl", processJsonMethod.get("nodeType"), "First method should be CtMethodImpl");
        assertEquals("processJson", processJsonMethod.get("artifactName"), "First method should be processJson");
        assertEquals("JsonProcessor", processJsonMethod.get("className"), "First method should belong to JsonProcessor class");
        assertEquals("com.example.JsonProcessor", processJsonMethod.get("qualifierType"), "First method qualifier type should be com.example.JsonProcessor");
        assertEquals(20, processJsonMethod.get("lineNumber"), "processJson method should be at line 20");
        assertEquals(false, processJsonMethod.get("isStatic"), "processJson should not be static");
        assertEquals(true, processJsonMethod.get("isPublic"), "processJson should be public");
        assertEquals(true, processJsonMethod.get("usesParameters"), "processJson should use parameters");
    }

    @Test
    public void testCallPath2ProcessJsonParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(1).get(0);
        List<Map<String, String>> parameters = (List<Map<String, String>>) processJsonMethod.get("parameters");
        assertEquals(1, parameters.size(), "processJson should have 1 parameter");
        
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String jsonInput", param1.get("value"), "First parameter should be 'String jsonInput'");
        assertEquals("java.lang.String", param1.get("type"), "First parameter type should be java.lang.String");
    }

    @Test
    public void testCallPath2ProcessJsonConstructorParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(1).get(0);
        List<Map<String, Object>> constructorParameters = (List<Map<String, Object>>) processJsonMethod.get("constructorParameters");
        assertEquals(1, constructorParameters.size(), "processJson should have 1 constructor parameter");

        Map<String, Object> param1 = constructorParameters.get(0);
        assertEquals("JsonProcessor", param1.get("className"), "First constructor parameter should be of type JsonProcessor");
        assertEquals("com.example.JsonProcessor", param1.get("qualifiedName"), "First constructor parameter qualified name should be com.example.JsonProcessor");
        assertEquals(true, param1.get("isPublic"), "First constructor parameter should be public");
        List<Map<String, Object>> parameters = (List<Map<String, Object>>) param1.get("parameters");
        assertNotNull(parameters, "Constructor parameters should not be null");
        assertEquals(0, parameters.size(), "First constructor parameter should have no parameters");
    }

    
    @Test
    public void testCallPath2SecondVulnerableMethodCall() {
        Map<String, Object> secondVulnerableMethod = allCallPaths.get(1).get(1);
        
        assertEquals("CtMethodImpl", secondVulnerableMethod.get("nodeType"), "Second method should be CtMethodImpl");
        assertEquals("secondVulnerableMethodCall", secondVulnerableMethod.get("artifactName"), "Second method should be secondVulnerableMethodCall");
        assertEquals("SecondMethodCall", secondVulnerableMethod.get("className"), "Second method should belong to SecondMethodCall class");
        assertEquals("com.example.SecondMethodCall", secondVulnerableMethod.get("qualifierType"), "Second method qualifier type should be com.example.SecondMethodCall");
        assertEquals(20, secondVulnerableMethod.get("lineNumber"), "secondVulnerableMethodCall should be at line 20");
        assertEquals(false, secondVulnerableMethod.get("isStatic"), "secondVulnerableMethodCall should not be static");
        assertEquals(true, secondVulnerableMethod.get("isPublic"), "secondVulnerableMethodCall should be public");
        assertEquals(true, secondVulnerableMethod.get("usesParameters"), "secondVulnerableMethodCall should use parameters");
    }

    @Test
    public void testCallPath2SecondVulnerableMethodCallParameters() {
        Map<String, Object> secondVulnerableMethod = allCallPaths.get(1).get(1);
        List<Map<String, String>> parameters = (List<Map<String, String>>) secondVulnerableMethod.get("parameters");
        assertEquals(1, parameters.size(), "secondVulnerableMethodCall should have 1 parameter");

        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String arg", param1.get("value"), "First parameter should be 'String arg'");
        assertEquals("java.lang.String", param1.get("type"), "First parameter type should be java.lang.String");
    }

    @Test
    public void testCallPath2SecondVulnerableMethodCallConstructorParameters() {
        Map<String, Object> secondVulnerableMethod = allCallPaths.get(1).get(1);
        List<Map<String, Object>> constructorParameters = (List<Map<String, Object>>) secondVulnerableMethod.get("constructorParameters");
        assertEquals(1, constructorParameters.size(), "secondVulnerableMethodCall should have 1 constructor parameter");

        Map<String, Object> param1 = constructorParameters.get(0);
        assertEquals("SecondMethodCall", param1.get("className"), "First constructor parameter should be of type SecondMethodCall");
        assertEquals("com.example.SecondMethodCall", param1.get("qualifiedName"), "First constructor parameter qualified name should be com.example.SecondMethodCall");
        assertEquals(true, param1.get("isPublic"), "First constructor parameter should be public");
        
        List<Map<String, Object>> parameters = (List<Map<String, Object>>) param1.get("parameters");
        assertEquals(1, parameters.size(), "First constructor parameter should have 1 parameter");
        Map<String, Object> constructorParam1 = parameters.get(0);
        assertEquals("jsonString", constructorParam1.get("name"), "Constructor parameter name should be 'User user'");
        assertEquals("com.example.User", constructorParam1.get("type"), "Constructor parameter type should be 'com.example.User'");
        
        List<Map<String, Object>> userConstructors = (List<Map<String, Object>>) constructorParam1.get("parameterConstructors");
        assertEquals(1, userConstructors.size(), "Constructor parameter should have 1 constructor");

        Map<String, Object> userConstructor = userConstructors.get(0);
        assertEquals("User", userConstructor.get("className"), "Constructor class name should be 'User'");
        assertEquals(true, userConstructor.get("isPublic"), "User constructor should be public");
        assertEquals("com.example.User", userConstructor.get("qualifiedName"), "User constructor qualified name should be 'com.example.User'");
        List<Map<String, Object>> userConstructorParams = (List<Map<String, Object>>) userConstructor.get("parameters");
        assertEquals(3, userConstructorParams.size(), "User constructor should have 3 parameters");
        assertEquals("id", userConstructorParams.get(0).get("name"), "First constructor parameter name should be 'id'");
        assertEquals("int", userConstructorParams.get(0).get("type"), "First constructor parameter type should be 'int'");
        assertEquals("name", userConstructorParams.get(1).get("name"), "Second constructor parameter name should be 'name'");
        assertEquals("java.lang.String", userConstructorParams.get(1).get("type"), "Second constructor parameter type should be 'java.lang.String'");
        assertEquals("data", userConstructorParams.get(2).get("name"), "Third constructor parameter name should be 'data'");
        assertEquals("com.example.Data", userConstructorParams.get(2).get("type"), "Third constructor parameter type should be 'com.example.Data'");

    }
    
    @Test
    public void testCallPath2MainParameters() {
        Map<String, Object> mainMethod = allCallPaths.get(1).get(2);
        List<Map<String, String>> parameters = (List<Map<String, String>>) mainMethod.get("parameters");
        assertEquals(1, parameters.size(), "main should not have any parameters");
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String[] args", param1.get("value"), "First parameter should be 'String[] args'");
        assertEquals("java.lang.String[]", param1.get("type"), "First parameter type should be java.lang.String[]");
    }
    
    // Tests for call path 3: processJson -> main (Direct call)
    
    @Test
    public void testCallPath3HasCorrectLength() {
        List<Map<String, Object>> callPath3 = allCallPaths.get(2);
        assertEquals(2, callPath3.size(), "Call path 3 should have 2 methods in the chain (direct call)");
    }
    
    @Test
    public void testCallPath3ProcessJson() {
        Map<String, Object> processJsonMethod = allCallPaths.get(2).get(0);

        assertEquals("CtMethodImpl", processJsonMethod.get("nodeType"), "First method should be CtMethodImpl");
        assertEquals("processJson", processJsonMethod.get("artifactName"), "First method should be processJson");
        assertEquals("JsonProcessor", processJsonMethod.get("className"), "First method should belong to JsonProcessor class");
        assertEquals("com.example.JsonProcessor", processJsonMethod.get("qualifierType"), "First method qualifier type should be com.example.JsonProcessor");
        assertEquals(20, processJsonMethod.get("lineNumber"), "processJson method should be at line 20");
        assertEquals(false, processJsonMethod.get("isStatic"), "processJson should not be static");
        assertEquals(true, processJsonMethod.get("isPublic"), "processJson should be public");
        assertEquals(true, processJsonMethod.get("usesParameters"), "processJson should use parameters");
    }

    @Test
    public void testCallPath3ProcessJsonParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(2).get(0);
        List<Map<String, String>> parameters = (List<Map<String, String>>) processJsonMethod.get("parameters");
        assertEquals(1, parameters.size(), "processJson should have 1 parameter");
        
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String jsonInput", param1.get("value"), "First parameter should be 'String jsonInput'");
        assertEquals("java.lang.String", param1.get("type"), "First parameter type should be java.lang.String");
    }

    @Test
    public void testCallPath3ProcessJsonConstructorParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(2).get(0);
        List<Map<String, Object>> constructorParameters = (List<Map<String, Object>>) processJsonMethod.get("constructorParameters");
        assertEquals(1, constructorParameters.size(), "processJson should have 1 constructor parameter");

        Map<String, Object> param1 = constructorParameters.get(0);
        assertEquals("JsonProcessor", param1.get("className"), "First constructor parameter should be of type JsonProcessor");
        assertEquals("com.example.JsonProcessor", param1.get("qualifiedName"), "First constructor parameter qualified name should be com.example.JsonProcessor");
        assertEquals(true, param1.get("isPublic"), "First constructor parameter should be public");
        List<Map<String, Object>> parameters = (List<Map<String, Object>>) param1.get("parameters");
        assertNotNull(parameters, "Constructor parameters should not be null");
        assertEquals(0, parameters.size(), "First constructor parameter should have no parameters");
    }
    
    @Test
    public void testCallPath3MainParameters() {
        Map<String, Object> mainMethod = allCallPaths.get(2).get(1);
        List<Map<String, String>> parameters = (List<Map<String, String>>) mainMethod.get("parameters");
        assertEquals(1, parameters.size(), "main should not have any parameters");
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String[] args", param1.get("value"), "First parameter should be 'String[] args'");
        assertEquals("java.lang.String[]", param1.get("type"), "First parameter type should be java.lang.String[]");
    }

    // Tests for call path 4: processJson -> main (Alternative path)

    @Test
    public void testCallPath4HasCorrectLength() {
        List<Map<String, Object>> callPath4 = allCallPaths.get(3);
        assertEquals(2, callPath4.size(), "Call path 4 should have 2 methods in the chain");
    }
    
     @Test
    public void testCallPath4ProcessJson() {
        Map<String, Object> processJsonMethod = allCallPaths.get(3).get(0);

        assertEquals("CtMethodImpl", processJsonMethod.get("nodeType"), "First method should be CtMethodImpl");
        assertEquals("processJson", processJsonMethod.get("artifactName"), "First method should be processJson");
        assertEquals("JsonProcessor", processJsonMethod.get("className"), "First method should belong to JsonProcessor class");
        assertEquals("com.example.JsonProcessor", processJsonMethod.get("qualifierType"), "First method qualifier type should be com.example.JsonProcessor");
        assertEquals(20, processJsonMethod.get("lineNumber"), "processJson method should be at line 20");
        assertEquals(false, processJsonMethod.get("isStatic"), "processJson should not be static");
        assertEquals(true, processJsonMethod.get("isPublic"), "processJson should be public");
        assertEquals(true, processJsonMethod.get("usesParameters"), "processJson should use parameters");
    }

    @Test
    public void testCallPath4ProcessJsonParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(3).get(0);
        List<Map<String, String>> parameters = (List<Map<String, String>>) processJsonMethod.get("parameters");
        assertEquals(1, parameters.size(), "processJson should have 1 parameter");
        
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String jsonInput", param1.get("value"), "First parameter should be 'String jsonInput'");
        assertEquals("java.lang.String", param1.get("type"), "First parameter type should be java.lang.String");
    }

    @Test
    public void testCallPath4ProcessJsonConstructorParameters() {
        Map<String, Object> processJsonMethod = allCallPaths.get(3).get(0);
        List<Map<String, Object>> constructorParameters = (List<Map<String, Object>>) processJsonMethod.get("constructorParameters");
        assertEquals(1, constructorParameters.size(), "processJson should have 1 constructor parameter");

        Map<String, Object> param1 = constructorParameters.get(0);
        assertEquals("JsonProcessor", param1.get("className"), "First constructor parameter should be of type JsonProcessor");
        assertEquals("com.example.JsonProcessor", param1.get("qualifiedName"), "First constructor parameter qualified name should be com.example.JsonProcessor");
        assertEquals(true, param1.get("isPublic"), "First constructor parameter should be public");
        List<Map<String, Object>> parameters = (List<Map<String, Object>>) param1.get("parameters");
        assertNotNull(parameters, "Constructor parameters should not be null");
        assertEquals(0, parameters.size(), "First constructor parameter should have no parameters");
    }
    
    @Test
    public void testCallPath4MainParameters() {
        Map<String, Object> mainMethod = allCallPaths.get(3).get(1);
        List<Map<String, String>> parameters = (List<Map<String, String>>) mainMethod.get("parameters");
        assertEquals(1, parameters.size(), "main should not have any parameters");
        Map<String, String> param1 = parameters.get(0);
        assertEquals("0", param1.get("position"), "First parameter should be at position 0");
        assertEquals("String[] args", param1.get("value"), "First parameter should be 'String[] args'");
        assertEquals("java.lang.String[]", param1.get("type"), "First parameter type should be java.lang.String[]");
    }  
}
