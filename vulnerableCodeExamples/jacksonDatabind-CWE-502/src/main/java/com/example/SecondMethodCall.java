package com.example;

import java.io.IOException;

public class SecondMethodCall {
    private String jsonString;

    public SecondMethodCall(User jsonString) {
        this.jsonString = jsonString.name;
        JsonProcessor processor = new JsonProcessor();        
        try {
            processor.processJson(this.jsonString);
        } catch (IOException e) {
            System.err.println("Error en uso legítimo: " + e.getMessage());
        }
    }



    public void secondVulnerableMethodCall() {
        JsonProcessor processor = new JsonProcessor();        
        try {
            processor.processJson(this.jsonString);
        } catch (IOException e) {
            System.err.println("Error en uso legítimo: " + e.getMessage());
        }
    }
}
