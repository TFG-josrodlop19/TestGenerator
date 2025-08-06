import os
from jinja2 import Environment, FileSystemLoader

# Diccionario de tipos, movido fuera para ser una constante global
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
    La función clave: recorre recursivamente los parámetros y los estandariza.
    1. Extrae un nombre de variable limpio del campo 'value'.
    2. Asigna un 'fuzz_method' a los tipos primitivos.
    3. Llama a sí misma para los constructores anidados.
    """
    if not params:
        return

    for param in params:
        # 1. Extraer nombre de variable limpio desde el campo 'value'
        # Esto soluciona el problema de "String jsonInput" vs "User jsonString"
        if 'value' in param:
            # Separamos por el último espacio para obtener el nombre de la variable
            # ej: "String jsonInput" -> "jsonInput"
            param['name'] = param['value'].rsplit(' ', 1)[-1]
        
        # 2. Asignar 'fuzz_method' o procesar constructor anidado
        if 'constructor' in param:
            # Es un objeto complejo, procesamos sus parámetros recursivamente
            constructor_params = param.get("constructor", [{}])[0].get("parameters", [])
            standardize_parameters(constructor_params)
        else:
            # Es un tipo primitivo, le asignamos su método de fuzzing
            java_type = param.get('type')
            param['fuzz_method'] = TYPE_TO_FUZZ_FUNCTION.get(java_type, f"// Tipo no soportado: {java_type}")

def generate_fuzzer(data: dict, exit_directory: str = "."):
    """
    Genera un fuzzer a partir de una estructura de datos JSON.
    """
    # Configuración del entorno Jinja
    env = Environment(loader=FileSystemLoader('plantillas'), trim_blocks=True, lstrip_blocks=True)
    
    # <<-- PASO CLAVE: ESTANDARIZAR LOS DATOS ANTES DE RENDERIZAR -->>
    standardize_parameters(data.get("parameters", []))
    
    # Nombres simples para la clase y la instancia
    data["qualifierType_simple_name"] = data["qualifierType"].split('.')[-1]
    data["instance_name"] = data.get("qualifierName", data["qualifierType_simple_name"]).replace('this.', '').lower()
    
    # Cargar la plantilla definitiva
    plantilla = env.get_template('fuzzer.java.j2')

    # Renderizar la plantilla con los datos ya limpios y estandarizados
    codigo_generado = plantilla.render(data)

    # Guardar el resultado en un fichero
    class_name = data.get("className", data.get("qualifierType_simple_name"))
    # Si es un constructor, el nombre del artefacto no existe, usamos "Constructor"
    artifact_name = data.get("artifactName", "Constructor")
    clase_fuzzer = f"{class_name}{artifact_name.capitalize()}Fuzzer"
    ruta_salida = os.path.join(exit_directory, f"{clase_fuzzer}.java")

    if not os.path.exists(exit_directory):
        os.makedirs(exit_directory)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(codigo_generado)

    print(f"Fuzzer generado en: {ruta_salida}")