import os
from jinja2 import Environment, FileSystemLoader
from aux_generator import type_selector_function_for_fuzzing_param

def generar_fuzzer_desde_plantilla(contexto: dict, directorio_salida: str = "."):
    
    # 1. Configurar el entorno de Jinja2
    env = Environment(loader=FileSystemLoader('plantillas'), trim_blocks=True, lstrip_blocks=True)
    
    # 2. Inyectar el tipo de datos
    contexto["params"] = type_selector_function_for_fuzzing_param(contexto["params"])

    # 3. Cargar la plantilla
    plantilla = env.get_template('fuzzer.java.j2')

    # 4. Renderizar la plantilla con el contexto
    # Aquí es donde Jinja2 reemplaza los {{ ... }} con los valores del diccionario
    codigo_generado = plantilla.render(contexto)

    # 5. Guardar el resultado en un fichero
    clase_fuzzer = contexto.get("clase_fuzzer", "FuzzerGenerico")
    ruta_salida = os.path.join(directorio_salida, f"{clase_fuzzer}.java")

    if not os.path.exists(directorio_salida):
        os.makedirs(directorio_salida)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(codigo_generado)

    print(f"✅ Fuzzer generado con plantilla en: {ruta_salida}")
