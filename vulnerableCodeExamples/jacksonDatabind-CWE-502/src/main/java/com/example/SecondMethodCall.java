package com.example;

import java.io.IOException;

public class SecondMethodCall {
    public void secondVulnerableMethodCall() {
        JsonProcessor processor = new JsonProcessor();

        // Escenario 1: Uso legítimo (funcionaría bien)
        String legitimateJson = "{\"id\":123, \"name\":\"Alice\"}";
        try {
            processor.processJson(legitimateJson);
        } catch (IOException e) {
            System.err.println("Error en uso legítimo: " + e.getMessage());
        }
    }
}
