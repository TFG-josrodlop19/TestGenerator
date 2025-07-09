package com.josrodlop19.javaAnalyzer;

public class App {

    public static void main(String[] args) {
        if (args.length < 3) {
            System.err.println("Use: java -jar analyzer.jar <file_path> <line_number> <artifact_name>");
            System.exit(1);
        }
        String filePath = args[0];
        int targetLine = Integer.parseInt(args[1]);
        String targetName = args[2];

        // Create an instance of CodeAnalyzer
        CodeAnalyzer analyzer = new CodeAnalyzer(filePath, targetLine, targetName);
        analyzer.processCode();
        analyzer.getDataAsString();
    }
}
