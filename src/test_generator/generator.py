import os
from jinja2 import Environment, FileSystemLoader
from utils.aux_generator import type_selector_function_for_fuzzing_param

def generate_fuzzer(data: dict, exit_directory: str = "."):
    
    # Config jinja environment
    env = Environment(loader=FileSystemLoader('plantillas'), trim_blocks=True, lstrip_blocks=True)
    
    # 2. Inyectar el tipo de datos
    type_to_fuzz_function = {
        "java.lang.String": "consumeString(1000)", # Usamos un límite para seguridad
        "java.lang.Integer": "consumeInt()",
        "int": "consumeInt()",
        "java.lang.Boolean": "consumeBoolean()",
        "boolean": "consumeBoolean()",
        "byte[]": "consumeBytes(4096)",
        # Añade más mapeos según necesites
    }
    
    # Procesamos cada parámetro para añadir la función de fuzzing
    for param in data.get("parameters", []):
        java_type = param.get("typeAtDeclaration", param.get("typeAtCall", param.get("type")))
        param["type"] = java_type  # Un solo punto de lectura del tipo para jinja2
        # Asigna la función de fuzzing o un valor por defecto si no se encuentra
        param["fuzz_method"] = type_to_fuzz_function.get(java_type, f"// No se pudo generar el tipo {java_type}")

    # Extraemos nombres simples para usarlos en el código Java
    data["qualifierType_simple_name"] = data["qualifierType"].split('.')[-1]
    # Simplificamos el nombre de la instancia para que sea un nombre de variable válido
    data["instance_name"] = data["qualifierName"].replace('this.', '')
    
    # 3. Cargar la plantilla
    plantilla = env.get_template('fuzzer.java.j2')

    # 4. Renderizar la plantilla con el data
    # Aquí es donde Jinja2 reemplaza los {{ ... }} con los valores del diccionario
    codigo_generado = plantilla.render(data)

    # 5. Guardar el resultado en un fichero
    clase_fuzzer = data.get("className") + data.get("artifactName").capitalize() + "Fuzzer"
    ruta_salida = os.path.join(exit_directory, f"{clase_fuzzer}.java")

    if not os.path.exists(exit_directory):
        os.makedirs(exit_directory)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(codigo_generado)

    print(f"Fuzzer generated at: {ruta_salida}")
