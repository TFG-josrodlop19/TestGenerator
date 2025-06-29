package com.example;

import java.util.ArrayList;

public class VulnerableCode {
    private static final String CONSTANT_STRING = "Test";

    // Esta función es vulnerable si 'index' está fuera de los límites de CONSTANT_STRING
    public static void triggerVulnerability(int index) {
        System.out.println("Intentando acceder al índice: " + index + " de la cadena '" + CONSTANT_STRING + "'");
        // Vulnerabilidad: si index < 0 o index >= CONSTANT_STRING.length()
        char c = CONSTANT_STRING.charAt(index);
        System.out.println("Carácter obtenido: " + c); // No se alcanzará si hay excepción
    }

    public static void processInput(byte[] data) {
        if (data == null || data.length == 0) {
            return; // No hacer nada si no hay datos
        }

        // Usaremos el primer byte de la entrada como índice.
        // Esto es muy propenso a errores si no se valida.
        int potentialIndex = data[0]; // Puede ser negativo o muy grande

        // Para hacer la vulnerabilidad más directa y menos dependiente del valor exacto del byte:
        // Si el primer byte es 'X' (88 en ASCII), intentamos un índice claramente fuera de límites.
        // Si no, intentamos usar el valor del byte directamente (que también puede fallar).
        if (data[0] == (byte)'X') {
            triggerVulnerability(100); // "Test" solo tiene 4 caracteres (índices 0-3)
        } else {
            triggerVulnerability(potentialIndex);
        }
    }
}