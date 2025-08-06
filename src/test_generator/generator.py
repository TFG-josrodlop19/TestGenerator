import os
from jinja2 import Environment, FileSystemLoader

# El diccionario de tipos no cambia
TYPE_TO_FUZZ_FUNCTION = {
    "java.lang.String": "consumeString(1000)",
    "java.lang.Integer": "consumeInt()",
    "int": "consumeInt()",
    "java.lang.Boolean": "consumeBoolean()",
    "boolean": "consumeBoolean()",
    "byte[]": "consumeBytes(4096)",
}

def standardize_parameters(params: list):
    """
    Función recursiva mejorada que estandariza los parámetros.
    Ahora maneja tanto la clave 'constructor' como 'parameterConstructors'.
    """
    if not params:
        return

    for param in params:
        if 'value' in param:
            param['name'] = param['value'].rsplit(' ', 1)[-1]
        
        # <<-- CAMBIO: Maneja ambas claves para los constructores -->>
        # Busca la lista de constructores, sin importar el nombre de la clave.
        constructor_list = param.get("constructor") or param.get("parameterConstructors")

        if constructor_list:
            # Es un objeto complejo, procesamos sus parámetros recursivamente.
            # Asumimos que siempre usamos la primera sobrecarga del constructor.
            constructor_params = constructor_list[0].get("parameters", [])
            standardize_parameters(constructor_params)
        else:
            # Es un tipo primitivo, le asignamos su método de fuzzing.
            java_type = param.get('type')
            param['fuzz_method'] = TYPE_TO_FUZZ_FUNCTION.get(java_type, f"// Tipo no soportado: {java_type}")

def generate_fuzzer(data: dict, exit_directory: str = "."):
    # El resto de esta función no necesita cambios.
    # Solo asegúrate de que llama a la nueva versión de standardize_parameters.
    env = Environment(loader=FileSystemLoader('plantillas'), trim_blocks=True, lstrip_blocks=True)
    standardize_parameters(data.get("parameters", []))
    data["qualifierType_simple_name"] = data["qualifierType"].split('.')[-1]
    data["instance_name"] = data.get("qualifierName", data["qualifierType_simple_name"]).replace('this.', '').lower()
    
    # Cargar la nueva plantilla recursiva
    plantilla = env.get_template('fuzzer.java.j2')
    codigo_generado = plantilla.render(data)

    class_name = data.get("className", data.get("qualifierType_simple_name"))
    artifact_name = data.get("artifactName", "Constructor")
    clase_fuzzer = f"{class_name}{artifact_name.capitalize()}Fuzzer"
    ruta_salida = os.path.join(exit_directory, f"{clase_fuzzer}.java")

    if not os.path.exists(exit_directory):
        os.makedirs(exit_directory)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(codigo_generado)
    print(f"Fuzzer generado en: {ruta_salida}")