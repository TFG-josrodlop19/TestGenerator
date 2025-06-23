import os
from jinja2 import Environment, FileSystemLoader

def generar_fuzzer_desde_plantilla(contexto: dict, directorio_salida: str = "."):
    """
    Genera un archivo de fuzzer usando una plantilla Jinja2.

    Args:
        contexto (dict): Un diccionario con los datos para la plantilla.
        directorio_salida (str): Carpeta donde se guardará el fuzzer.
    """
    # 1. Configurar el entorno de Jinja2
    # Le decimos a Jinja2 que busque las plantillas en la carpeta 'plantillas'
    env = Environment(loader=FileSystemLoader('plantillas'), trim_blocks=True, lstrip_blocks=True)

    # 2. Cargar la plantilla
    plantilla = env.get_template('fuzzer.java.j2')

    # 3. Renderizar la plantilla con el contexto
    # Aquí es donde Jinja2 reemplaza los {{ ... }} con los valores del diccionario
    codigo_generado = plantilla.render(contexto)

    # 4. Guardar el resultado en un fichero
    clase_fuzzer = contexto.get("clase_fuzzer", "FuzzerGenerico")
    ruta_salida = os.path.join(directorio_salida, f"{clase_fuzzer}.java")

    if not os.path.exists(directorio_salida):
        os.makedirs(directorio_salida)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(codigo_generado)

    print(f"✅ Fuzzer generado con plantilla en: {ruta_salida}")


# --- Ejemplo de Uso ---
if __name__ == "__main__":
    # Define todos los datos que la plantilla necesita en un solo lugar.
    # Esto hace que el código sea mucho más limpio.
    contexto_parser_csv = {
        "clase_fuzzer": "CSVParserFuzzer",
        "paquete_fuzzer": "com.example.fuzz.csv",
        "paquete_target": "org.apache.commons.csv",
        "clase_target": "CSVParser",
        "metodo_target": "parse" # Un método estático de ejemplo
    }

    generar_fuzzer_desde_plantilla(
        contexto=contexto_parser_csv,
        directorio_salida="fuzzers_generados"
    )