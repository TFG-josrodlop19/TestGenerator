#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/josue/universidad/TFG/code/TestGenerator/src')

from test_generator.generator import generate_fuzzer

# Datos de prueba con mal formateo intencional
test_data = {
    "nodeType": "CtMethodImpl",
    "artifactName": "testMethod",
    "className": "TestClass",
    "qualifierName": "TestClass", 
    "qualifierType": "com.example.TestClass",
    "packageName": "package com.example;",
    "parameters": [
        {
            "name": "param1",
            "type": "java.lang.String"
        }
    ],
    "isStatic": False,
    "isPublic": True,
    "constructorParameters": []
}

print("=== GENERANDO FUZZER DE PRUEBA CON FORMATEO ===")
result = generate_fuzzer(test_data, "/tmp/test_format")
print(f"\nFuzzer generado en: {result}")

print("\n=== CONTENIDO DEL FUZZER FORMATEADO ===")
with open(result, 'r') as f:
    content = f.read()
    print(content)
