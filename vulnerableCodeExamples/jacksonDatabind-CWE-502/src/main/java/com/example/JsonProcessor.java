package com.example;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;

public class JsonProcessor {

    private final ObjectMapper mapper;

    // El constructor configura el componente de forma insegura
    public JsonProcessor() {
        this.mapper = new ObjectMapper();
        // LA VULNERABILIDAD SE CONFIGURA AQUÍ
        this.mapper.enableDefaultTyping();
    }

    /**
     * Este es el método que procesa la entrada externa y que será el objetivo de nuestro fuzzer.
     */
    public void processJson(String jsonInput) throws IOException {
        System.out.println("[Processor] Procesando JSON: " + jsonInput);
        // El método vulnerable es llamado aquí
        if (true) {
            this.mapper.readValue(jsonInput, Object.class);
        }
        
        System.out.println("[Processor] JSON procesado con éxito.");
    }
}