import os
from pathlib import Path
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
    """
    Genera un fuzzer basado en los datos proporcionados.
    
    Args:
        data (dict): Datos del artefacto para generar el fuzzer
        exit_directory (str): Directorio donde guardar el fuzzer generado
    """
    # Obtener la ruta absoluta del directorio de plantillas
    current_file_dir = Path(__file__).parent  # src/test_generator/
    templates_dir = current_file_dir.parent.parent / "plantillas"  # src/plantillas/
    
    # Verificar que el directorio de plantillas existe
    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found at: {templates_dir}")
    
    # Configurar Jinja2 con la ruta absoluta
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)), 
        trim_blocks=True, 
        lstrip_blocks=True
    )
    
    # Procesar los datos
    standardize_parameters(data.get("parameters", []))
    data["qualifierType_simple_name"] = data["qualifierType"].split('.')[-1]
    data["instance_name"] = data.get("qualifierName", data["qualifierType_simple_name"]).replace('this.', '').lower()
    
    # Cargar la plantilla
    try:
        plantilla = env.get_template('fuzzer.java.j2')
    except Exception as e:
        print(f"Error loading template 'fuzzer.java.j2' from {templates_dir}")
        print(f"Available templates: {list(templates_dir.glob('*.j2'))}")
        raise e
    
    # Generar el código
    codigo_generado = plantilla.render(data)

    # Crear el nombre del archivo y la ruta de salida
    class_name = data.get("className", data.get("qualifierType_simple_name"))
    artifact_name = data.get("artifactName", "Constructor")
    clase_fuzzer = f"{class_name}_{artifact_name.capitalize()}_Fuzzer"
    
    # Resolver la ruta de salida
    exit_path = Path(exit_directory).resolve()
    ruta_salida = exit_path / f"{clase_fuzzer}.java"

    # Crear el directorio si no existe
    if not exit_path.exists():
        exit_path.mkdir(parents=True, exist_ok=True)
        
    # Escribir el archivo
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(codigo_generado)
        
    print(f"Fuzzer generado en: {ruta_salida}")
    return ruta_salida
    return str(ruta_salida)