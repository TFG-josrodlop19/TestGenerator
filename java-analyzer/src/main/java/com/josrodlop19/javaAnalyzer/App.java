package com.josrodlop19.javaAnalyzer;

import java.util.ArrayList;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONObject;

public class App {

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Use: java -jar analyzer.jar <pom_path> <artifacts_json>");
            System.exit(1);
        }
        String pomPath = args[0];
        String artifactsJson = args[1];

        // String pomPath = "/home/josue/universidad/TFG/code/TestGenerator/OSS-Fuzz/projects/tfg-josrodlop19_vulnerableproject4/pom.xml";
        // String artifactsJson = 
        //         "[\n" +
        //         "  {\n" +
        //         "    \"file_path\": \"/home/josue/universidad/TFG/code/TestGenerator/OSS-Fuzz/projects/tfg-josrodlop19_vulnerableproject4/src/main/java/com/example/VulnerableApp.java\",\n" +
        //         "    \"target_line\": 18,\n" +
        //         "    \"target_name\": \"SAXReader\"\n" +
        //         "  }\n" +
        //         "]";

        try {
            // Parse JSON array
            JSONArray artifacts = new JSONArray(artifactsJson);
            CodeAnalyzer analyzer = new CodeAnalyzer(pomPath);
            analyzer.extractAST();

            List<String> completeData = new ArrayList<>();

            // Process each artifact
            for (int i = 0; i < artifacts.length(); i++) {
                JSONObject artifact = artifacts.getJSONObject(i);
                String filePath = artifact.getString("file_path");
                int targetLine = artifact.getInt("target_line");
                String targetName = artifact.getString("target_name");

                // Create an instance of CodeAnalyzer for each artifact
                analyzer.setFilePath(filePath);
                analyzer.setTargetLine(targetLine);
                analyzer.setTargetName(targetName);
                analyzer.processCode();
                completeData.add(analyzer.getCompleteDataAsString());
            }
            // Print all results
            System.out.println(completeData);
        } catch (Exception e) {
            System.err.println("Error parsing JSON: " + e.getMessage());
            System.exit(1);
        }
    }
}
