package individualExamples;
public class VulnerableCode4 {
    public static void main(String[] args) {
        // Se crea un nuevo objeto String("hola") y sobre ese objeto recién creado,
        // se llama al método .length(). El resultado (4) se guarda en la variable.
        int longitud = new String("hola").length(); 

        System.out.println(longitud); // Imprime 4

    }
}