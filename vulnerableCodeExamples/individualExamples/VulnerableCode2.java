package individualExamples;
public class VulnerableCode2 {
    
    // Nivel 2: La variable 'lector' se declara aquí, como un campo.
    // Es el "puente" entre las dos ramas.
    private LectorDeFicheros lector;

    // RAMA 1: El método constructor.
    public VulnerableCode2(String ruta) { // Nivel 2
        // Nivel 4: La INSTANCIACIÓN ocurre aquí.
        this.lector = new LectorDeFicheros(ruta); 
    }

    // RAMA 2: Otro método de la clase.
    public String leerPrimeraLinea() { // Nivel 2
        // Nivel 4: El USO del objeto ocurre aquí.
        return this.lector.leerLinea();
    }
}