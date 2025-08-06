package com.josrodlop19.javaAnalyzer;

public class App {

    public static void main(String[] args) {
        // if (args.length < 4) {
        //     System.err.println("Use: java -jar analyzer.jar <file_path> <line_number> <artifact_name>");
        //     System.exit(1);
        // }
        // String pomPath = args[0];
        // String filePath = args[1];
        // int targetLine = Integer.parseInt(args[2]);
        // String targetName = args[3];

        String pomPath = "/home/josue/universidad/TFG/TestGenerator/vulnerableCodeExamples/jacksonDatabind-CWE-502";
        String filePath = "/home/josue/universidad/TFG/TestGenerator/vulnerableCodeExamples/jacksonDatabind-CWE-502/src/main/java/com/example/JsonProcessor.java";
        int targetLine = 24;
        String targetName = "readValue";

        // Create an instance of CodeAnalyzer
        CodeAnalyzer analyzer = new CodeAnalyzer(pomPath, filePath, targetLine, targetName);
        analyzer.processCode();
        analyzer.getCompleteDataAsString();
    }
}
