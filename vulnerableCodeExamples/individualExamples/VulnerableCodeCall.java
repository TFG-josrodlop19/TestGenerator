package individualExamples;

import Callable.VulnerableCode;
import java.util.*;

public class VulnerableCodeCall {
    public static void main(String[] args) {
        // Suponiendo que necesitas crear un objeto de la clase que tiene el método
        VulnerableCode vulnerable = new VulnerableCode();
        vulnerable.processInput(new byte[]{88}); // Ahora la llamada está dentro de un método
        // com.example.VulnerableCode.processInput(new byte[]{88}); // Llamada al método estático directamente
    }
}
