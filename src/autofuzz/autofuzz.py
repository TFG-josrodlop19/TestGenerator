import os
import subprocess
import sys
from pathlib import Path
from utils.file_writer import generate_path_repo, read_test_info_from_json, update_test_status
from utils.classes import TestStatus

def build_tests(owner: str, name: str):
    """
    Ejecuta el build de fuzzers usando OSS-Fuzz helper.py
    """
    repo_path = generate_path_repo(owner, name)
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    project = Path(repo_path).name
    
    
    # Cambiar al directorio de OSS-Fuzz (2 niveles arriba del proyecto)
    oss_fuzz_root = Path(repo_path).parent.parent
    if not oss_fuzz_root.exists():
        raise FileNotFoundError(f"OSS-Fuzz root does not exist: {oss_fuzz_root}")
    
    try:
        # Ejecutar el comando build_fuzzers usando Python del venv
        print(f"Building fuzzers for project: {project}")
        
        print(f"Command: {sys.executable} infra/helper.py build_fuzzers {project}")
        
        result = subprocess.run([
            sys.executable,  # Usar Python del entorno virtual activo
            "infra/helper.py", 
            "build_fuzzers", 
            project
        ], 
        cwd=oss_fuzz_root,  # Cambiar directorio de trabajo
        capture_output=True, 
        text=True, 
        check=True
        )
        
        print("Build successful!")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        check_compilation_failures(owner, name)
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed with return code: {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error during build: {e}")
        return False

def check_compilation_failures(owner: str, name: str):
    repo_path = generate_path_repo(owner, name)
    project = Path(repo_path).name
    
    # Directorio donde OSS-Fuzz guarda los binarios compilados
    oss_fuzz_root = Path(repo_path).parent.parent
    build_out_dir = oss_fuzz_root / "build" / "out" / project
    
    # Obtener información de tests generados
    try:
        info = read_test_info_from_json(owner, name)
    except FileNotFoundError:
        print(f"No test info found for {owner}/{name}")
        return {}
    
    for artifact in info:
        if artifact:
            tests = info[artifact].get("tests", [])
            for test_group in tests:
                if test_group and test_group != []:
                    for test in test_group:
                        if test and test.get("test_path"):
                            test_path = test.get("test_path")
                            compiled_fuzzer_name = Path(test_path).stem + ".class"
                            files = list(build_out_dir.rglob(compiled_fuzzer_name))
                            if not files:
                                update_test_status(owner, name, artifact, test_path, TestStatus.ERROR_BUILDING.value)


def execute_tests(owner, name):
    repo_path = generate_path_repo(owner, name)
    project = Path(repo_path).name
    
    # Directorio donde OSS-Fuzz guarda los binarios compilados
    oss_fuzz_root = Path(repo_path).parent.parent
    build_out_dir = oss_fuzz_root / "build" / "out" / project
    
    # Obtener información de tests generados
    try:
        info = read_test_info_from_json(owner, name)
    except FileNotFoundError:
        print(f"No test info found for {owner}/{name}")
        return {}
    
    # TODO: paralelizar ejecución de tests
    for artifact in info:
        if artifact:
            tests = info[artifact].get("tests", [])
            for test_group in tests:
                if test_group and test_group != []:
                    for test in test_group:
                        if test and test.get("test_path"):
                            test_path = test.get("test_path")
                            test_status = test.get("test_status")
                            if test_status == "created":
                                fuzzer_name = Path(test_path).stem
                                print(f"Ejecutando fuzzer: {fuzzer_name}")
                                try:
                                    # Ejecutar fuzzer individual usando OSS-Fuzz
                                    result = subprocess.run([
                                        sys.executable,
                                        "infra/helper.py", 
                                        "run_fuzzer", 
                                        project,
                                        fuzzer_name,
                                        "--",
                                        "-max_total_time=100",    # 10 minutos máximo
                                        "-print_final_stats=1"    # Mostrar estadísticas al final
                                    ], 
                                    cwd=oss_fuzz_root,
                                    capture_output=True, 
                                    text=True
                                    )
                                    
                                    # Analizar resultado
                                    output = result.stdout + result.stderr
                                    
                                    if result.returncode == 0:
                                        # Fuzzer ejecutó sin crashes
                                        print(f"✅ {fuzzer_name}: Completado sin issues")
                                        update_test_status(owner, name, artifact, test_path, TestStatus.NOT_VULNERABLE.value)
                                    else:
                                        # Fuzzer encontró algo o falló
                                        if any(keyword in output for keyword in ["ASAN", "heap-buffer-overflow", "AddressSanitizer", "SEGV", "abrt", "FuzzerSecurityIssue", "DEDUP_TOKEN"]):
                                            print(f"{fuzzer_name}: VULNERABILIDAD ENCONTRADA!")
                                            update_test_status(owner, name, artifact, test_path, TestStatus.VULNERABLE.value)
                                        else:
                                            print(f"{fuzzer_name}: Error de ejecución")
                                            update_test_status(owner, name, artifact, test_path, TestStatus.ERROR_EXECUTING.value)
                                    
                                    # Guardar output para análisis
                                    print(f"Output preview: {output[:200]}...")
                                    
                                except Exception as e:
                                    print(f"💥 {fuzzer_name}: Error inesperado: {e}")
                                    update_test_status(owner, name, artifact, test_path, TestStatus.ERROR_EXECUTING.value)

