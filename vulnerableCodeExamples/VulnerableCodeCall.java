package TestGenerator.vulnerableCodeExamples;

public class VulnerableCodeCall {
    public static void main(String[] args) {
        // Suponiendo que necesitas crear un objeto de la clase que tiene el método
        VulnerableCode vulnerable = new VulnerableCode();
        vulnerable.proceedInput(new byte[]{88}); // Ahora la llamada está dentro de un método
    }
}
