package com.example;

import com.code_intelligence.jazzer.api.FuzzedDataProvider;
import java.io.IOException;

public class JacksonFuzzTarget {

    private static JsonProcessor processor;

    // Se inicializa el componente vulnerable una sola vez
    static {
        processor = new JsonProcessor();
    }

    // El fuzzer llama directamente al método vulnerable
    public static void fuzzerTestOneInput(FuzzedDataProvider data) {
        String jsonInput = data.consumeRemainingAsString();
        try {
            // Se llama al método objetivo con los datos del fuzzer
            processor.processJson(jsonInput);
        } catch (IOException ignored) {
            // Ignoramos las excepciones esperadas
        }
    }
}