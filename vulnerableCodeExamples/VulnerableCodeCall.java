package TestGenerator.vulnerableCodeExamples;

import Callable.VulnerableCode;
import java.util.*;

public class VulnerableCodeCall {
    public static void main(String[] args) {
        // Suponiendo que necesitas crear un objeto de la clase que tiene el método
        com.example.VulnerableCode.processInput(new byte[]{88}); // 88 es el valor ASCII de 'X', que activa la vulnerabilidad
    }
}
