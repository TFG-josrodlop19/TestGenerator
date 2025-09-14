import os
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from utils.file_writer import generate_path_repo
from vexgen_caller.vex_generator import generate_artifact_key
from database.models import Artifact, Fuzzer, TestStatus
from database.operations import save_artifacts_fuzzer

# El diccionario de tipos no cambia
TYPE_TO_FUZZ_FUNCTION = {
    # primitives
    "byte": "dataProvider.consumeByte()",
    "short": "dataProvider.consumeShort()",
    "int": "dataProvider.consumeInt()",
    "long": "dataProvider.consumeLong()",
    "float": "dataProvider.consumeFloat()",
    "double": "dataProvider.consumeDouble()",
    "char": "dataProvider.consumeChar()",
    "boolean": "dataProvider.consumeBoolean()",
    
    # wrappers and common classes
    "java.lang.Byte": "dataProvider.consumeByte()",
    "java.lang.Short": "dataProvider.consumeShort()",
    "java.lang.Integer": "dataProvider.consumeInt()",
    "java.lang.Long": "dataProvider.consumeLong()",
    "java.lang.Float": "dataProvider.consumeFloat()",
    "java.lang.Double": "dataProvider.consumeDouble()",
    "java.lang.Character": "dataProvider.consumeChar()",
    "java.lang.Boolean": "dataProvider.consumeBoolean()",
    
    # strings and arrays
    "java.lang.String": "dataProvider.consumeString(1000)",
    "String": "dataProvider.consumeString(1000)",
    "char[]": "dataProvider.consumeString(100).toCharArray()",
    "byte[]": "dataProvider.consumeBytes(4096)",
    "int[]": "dataProvider.consumeInts(100)",
    "long[]": "dataProvider.consumeLongs(100)",
    "short[]": "dataProvider.consumeShorts(100)",
    "float[]": "dataProvider.consumeFloats(100)",
    "double[]": "dataProvider.consumeDoubles(100)",
    "boolean[]": "dataProvider.consumeBooleans(100)",
    "java.lang.String[]": "new String[]{dataProvider.consumeString(100), dataProvider.consumeString(100)}",
    
    # special numbers
    "java.math.BigInteger": "new java.math.BigInteger(dataProvider.consumeString(50))",
    "java.math.BigDecimal": "new java.math.BigDecimal(dataProvider.consumeDouble())",
    "java.util.concurrent.atomic.AtomicInteger": "new java.util.concurrent.atomic.AtomicInteger(dataProvider.consumeInt())",
    "java.util.concurrent.atomic.AtomicLong": "new java.util.concurrent.atomic.AtomicLong(dataProvider.consumeLong())",
    "java.util.concurrent.atomic.AtomicBoolean": "new java.util.concurrent.atomic.AtomicBoolean(dataProvider.consumeBoolean())",
    
    # date
    "java.util.Date": "new java.util.Date(dataProvider.consumeLong())",
    "java.time.LocalDate": "java.time.LocalDate.ofEpochDay(dataProvider.consumeInt(1, 365000))",
    "java.time.LocalTime": "java.time.LocalTime.ofSecondOfDay(dataProvider.consumeInt(0, 86400))",
    "java.time.LocalDateTime": "java.time.LocalDateTime.ofEpochSecond(dataProvider.consumeLong(), 0, java.time.ZoneOffset.UTC)",
    "java.time.Instant": "java.time.Instant.ofEpochSecond(dataProvider.consumeLong())",
    "java.time.ZonedDateTime": "java.time.ZonedDateTime.ofInstant(java.time.Instant.ofEpochSecond(dataProvider.consumeLong()), java.time.ZoneId.systemDefault())",
    "java.time.Duration": "java.time.Duration.ofSeconds(dataProvider.consumeLong())",
    "java.time.Period": "java.time.Period.ofDays(dataProvider.consumeInt())",
    "java.sql.Date": "new java.sql.Date(dataProvider.consumeLong())",
    "java.sql.Time": "new java.sql.Time(dataProvider.consumeLong())",
    "java.sql.Timestamp": "new java.sql.Timestamp(dataProvider.consumeLong())",
    "java.util.Calendar": "java.util.Calendar.getInstance()",
    
    # collections
    "java.util.List": "java.util.Arrays.asList(dataProvider.consumeString(100), dataProvider.consumeString(100))",
    "java.util.ArrayList": "new java.util.ArrayList<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.LinkedList": "new java.util.LinkedList<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.Vector": "new java.util.Vector<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.Stack": "new java.util.Stack<>()",
    "java.util.Set": "new java.util.HashSet<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.HashSet": "new java.util.HashSet<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.LinkedHashSet": "new java.util.LinkedHashSet<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.TreeSet": "new java.util.TreeSet<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.EnumSet": "java.util.EnumSet.noneOf(java.time.DayOfWeek.class)",
    "java.util.Map": "java.util.Collections.singletonMap(dataProvider.consumeString(50), dataProvider.consumeString(50))",
    "java.util.HashMap": "new java.util.HashMap<String, String>() {{ put(dataProvider.consumeString(50), dataProvider.consumeString(50)); }}",
    "java.util.LinkedHashMap": "new java.util.LinkedHashMap<String, String>() {{ put(dataProvider.consumeString(50), dataProvider.consumeString(50)); }}",
    "java.util.TreeMap": "new java.util.TreeMap<String, String>() {{ put(dataProvider.consumeString(50), dataProvider.consumeString(50)); }}",
    "java.util.Hashtable": "new java.util.Hashtable<String, String>() {{ put(dataProvider.consumeString(50), dataProvider.consumeString(50)); }}",
    "java.util.Properties": "new java.util.Properties() {{ setProperty(dataProvider.consumeString(50), dataProvider.consumeString(50)); }}",
    "java.util.Queue": "new java.util.LinkedList<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.Deque": "new java.util.ArrayDeque<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.ArrayDeque": "new java.util.ArrayDeque<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.PriorityQueue": "new java.util.PriorityQueue<>(java.util.Arrays.asList(dataProvider.consumeString(100)))",
    "java.util.concurrent.BlockingQueue": "new java.util.concurrent.ArrayBlockingQueue<>(10)",
    "java.util.concurrent.LinkedBlockingQueue": "new java.util.concurrent.LinkedBlockingQueue<>()",
    
    # streams
    "java.io.InputStream": "new java.io.ByteArrayInputStream(dataProvider.consumeBytes(1024))",
    "java.io.OutputStream": "new java.io.ByteArrayOutputStream()",
    "java.io.Reader": "new java.io.StringReader(dataProvider.consumeString(1000))",
    "java.io.Writer": "new java.io.StringWriter()",
    "java.io.File": "new java.io.File(dataProvider.consumeString(100))",
    "java.nio.file.Path": "java.nio.file.Paths.get(dataProvider.consumeString(100))",
    "java.net.URL": "new java.net.URL(\"http://example.com/\" + dataProvider.consumeString(50))",
    "java.net.URI": "java.net.URI.create(\"http://example.com/\" + dataProvider.consumeString(50))",
    
    # buffers
    "java.nio.ByteBuffer": "java.nio.ByteBuffer.wrap(dataProvider.consumeBytes(1024))",
    "java.nio.CharBuffer": "java.nio.CharBuffer.wrap(dataProvider.consumeString(100))",
    "java.nio.IntBuffer": "java.nio.IntBuffer.wrap(dataProvider.consumeInts(100))",
    "java.nio.LongBuffer": "java.nio.LongBuffer.wrap(dataProvider.consumeLongs(100))",
    "java.nio.FloatBuffer": "java.nio.FloatBuffer.wrap(dataProvider.consumeFloats(100))",
    "java.nio.DoubleBuffer": "java.nio.DoubleBuffer.wrap(dataProvider.consumeDoubles(100))",
    
    # utils
    "java.util.UUID": "java.util.UUID.fromString(String.format(\"%08x-%04x-%04x-%04x-%012x\", dataProvider.consumeInt(), dataProvider.consumeShort(), dataProvider.consumeShort(), dataProvider.consumeShort(), dataProvider.consumeLong()))",
    "java.util.Locale": "new java.util.Locale(dataProvider.consumeString(2))",
    "java.util.TimeZone": "java.util.TimeZone.getTimeZone(\"GMT\" + dataProvider.consumeInt(-12, 12))",
    "java.util.Currency": "java.util.Currency.getInstance(\"USD\")",
    "java.util.Random": "new java.util.Random(dataProvider.consumeLong())",
    "java.security.SecureRandom": "new java.security.SecureRandom()",
    
    # regex
    "java.util.regex.Pattern": "java.util.regex.Pattern.compile(dataProvider.consumeString(50))",
    "java.util.regex.Matcher": "java.util.regex.Pattern.compile(\".*\").matcher(dataProvider.consumeString(100))",
    
    # optionals
    "java.util.Optional": "java.util.Optional.ofNullable(dataProvider.consumeString(100))",
    "java.util.OptionalInt": "java.util.OptionalInt.of(dataProvider.consumeInt())",
    "java.util.OptionalLong": "java.util.OptionalLong.of(dataProvider.consumeLong())",
    "java.util.OptionalDouble": "java.util.OptionalDouble.of(dataProvider.consumeDouble())",

    # reflection
    "java.lang.Class": "String.class",
    "java.lang.reflect.Method": "String.class.getMethods()[0]",
    "java.lang.reflect.Field": "String.class.getFields().length > 0 ? String.class.getFields()[0] : null",
    "java.lang.reflect.Constructor": "String.class.getConstructors()[0]",
    
    # exceptions
    "java.lang.Exception": "new java.lang.Exception(dataProvider.consumeString(100))",
    "java.lang.RuntimeException": "new java.lang.RuntimeException(dataProvider.consumeString(100))",
    "java.lang.IllegalArgumentException": "new java.lang.IllegalArgumentException(dataProvider.consumeString(100))",
    "java.lang.IllegalStateException": "new java.lang.IllegalStateException(dataProvider.consumeString(100))",
    "java.lang.NullPointerException": "new java.lang.NullPointerException(dataProvider.consumeString(100))",
    
    # generic
    "java.lang.Object": "dataProvider.consumeString(100)",
    "java.io.Serializable": "dataProvider.consumeString(100)",
    "java.lang.Comparable": "dataProvider.consumeString(100)",
    "java.lang.CharSequence": "dataProvider.consumeString(100)",
    
    # common enums
    "java.time.DayOfWeek": "java.time.DayOfWeek.values()[dataProvider.consumeInt(0, 6)]",
    "java.time.Month": "java.time.Month.values()[dataProvider.consumeInt(0, 11)]",
    "java.nio.file.StandardOpenOption": "java.nio.file.StandardOpenOption.CREATE",
    "java.util.concurrent.TimeUnit": "java.util.concurrent.TimeUnit.values()[dataProvider.consumeInt(0, java.util.concurrent.TimeUnit.values().length - 1)]",
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

def format_java_file(file_path: str):
    """
    Formatea un archivo Java usando Google Java Format.
    
    Args:
        file_path (str): Ruta del archivo Java a formatear
    """
    try:
        # Obtener la ruta del proyecto (donde está este archivo)
        root_path = Path(__file__).parent.parent.parent  # src/test_generator/generator.py -> proyecto raíz
        google_format_jar = root_path / "libraries" / "google-java-format-1.28.0-all-deps.jar"

        if not google_format_jar.exists():
            print("Google Java Format JAR not found")
            return
        
        # Ejecutar el formatter
        result = subprocess.run([
            "java", "-jar", str(google_format_jar),
            "--replace", str(file_path)
        ], timeout=30)
        
        if result.returncode != 0:
            print(f"Error formatting: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("Timeout formatting code")
    except Exception as e:
        print(f"Unexpected error formatting: {e}")

def generate_fuzzers(owner: str, repo_name: str, artifacts_data: dict):
    # Generate tests output directory if not exists
    dest_path = Path(generate_path_repo(owner, repo_name))
    test_dir = dest_path / "src" / "test" / "java"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    tests_already_generated = {}
    for artifact_dict in artifacts_data:
        if artifact_dict != {}:
            all_call_paths = artifact_dict.get("allCallPaths", [])
            artifact_data = artifact_dict.get("artifactData")
            artifact = Artifact(
                filePath=artifact_data.get("filePath"),
                name=artifact_data.get("artifactName"),
                line=artifact_data.get("lineNumber")
            )            
            
            if all_call_paths and len(all_call_paths) > 0:
                for call_path in all_call_paths:
                    
                    for i in range(len(call_path) - 1, -1, -1):
                        # Entry data for the current fuzzer generation
                        entry_data = call_path[i]
                        call_path_artifact_key = generate_artifact_key(entry_data.get("filePath"), entry_data.get("artifactName"), entry_data.get("lineNumber"))

                        if call_path_artifact_key not in tests_already_generated:
                            fuzzer = None
                            try:
                                
                                test_path = generate_fuzzer(
                                    data=entry_data,
                                    exit_directory=str(test_dir)
                                )
                                uses_parameters = entry_data.get("usesParameters")
                                fuzzer = Fuzzer(
                                    testPath=str(test_path),
                                    name=test_path.stem,
                                    status=TestStatus.CREATED,
                                    usesParameters=uses_parameters
                                )

                            except Exception as e:
                                print(f"Error generating fuzzer: {e}")
                                fuzzer = Fuzzer(
                                    testPath="",
                                    name="",
                                    status=TestStatus.ERROR_GENERATING
                                )
                            tests_already_generated[call_path_artifact_key] = fuzzer
                            artifact.fuzzers.add(fuzzer)
                        else:
                            artifact.fuzzers.add(tests_already_generated[call_path_artifact_key])
                save_artifacts_fuzzer(owner, repo_name, artifact)
            else:
                print(f"No valid call paths found for artifact.")


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
    
    # NUEVO: Procesar también los parámetros del constructor
    if "constructorParameters" in data and data["constructorParameters"]:
        for constructor_info in data["constructorParameters"]:
            if "parameters" in constructor_info:
                standardize_parameters(constructor_info["parameters"])
    
    data["qualifierType_simple_name"] = data["qualifierType"].split('.')[-1]
    data["instance_name"] = data.get("qualifierName", data["qualifierType_simple_name"]).replace('this.', '').lower()
    
    # Cargar la plantilla
    try:
        plantilla = env.get_template('fuzzer.java.j2')
    except Exception as e:
        print(f"Error loading template 'fuzzer.java.j2' from {templates_dir}")
        raise e
    
    # Generar el código
    codigo_generado = plantilla.render(data)

    # Crear el nombre del archivo y la ruta de salida
    class_name = data.get("className", data.get("qualifierType_simple_name"))
    artifact_name = data.get("artifactName", "Constructor")
    clase_fuzzer = f"{class_name}{artifact_name.capitalize()}Fuzzer"
    
    # Resolver la ruta de salida
    exit_path = Path(exit_directory).resolve()
    ruta_salida = exit_path / f"{clase_fuzzer}.java"

    # Crear el directorio si no existe
    if not exit_path.exists():
        exit_path.mkdir(parents=True, exist_ok=True)
        
    # Escribir el archivo
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(codigo_generado)
    
    # Formatear el código Java usando Google Java Format
    format_java_file(ruta_salida)

    return ruta_salida

