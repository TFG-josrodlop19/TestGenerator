package com.josrodlop19.javaAnalyzer;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import spoon.Launcher;
import spoon.SpoonAPI;
import spoon.reflect.CtModel;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.visitor.filter.TypeFilter;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class SpecificArtifactAnalyzer {

    public static void main(String[] args) {
        if (args.length < 3) {
            System.err.println("Uso: java -jar analyzer.jar <ruta_al_fichero> <numero_linea> <nombre_artefacto>");
            System.exit(1);
        }
        String filePath = args[0];
        int targetLine = Integer.parseInt(args[1]);
        String targetName = args[2];

        // 1. Configurar Spoon
        SpoonAPI spoon = new Launcher();
        spoon.addInputResource(filePath);
        spoon.getEnvironment().setNoClasspath(true);
        
        // 2. Construir el modelo AST
        CtModel model = spoon.buildModel();
        
        // 3. Filtrar para encontrar TODAS las invocaciones de método
        List<CtInvocation<?>> allInvocations = model.getElements(new TypeFilter<>(CtInvocation.class));

        Map<String, Object> artifactData = null;

        // 4. Buscar el artefacto específico
        // ... dentro del método main, después de obtener allInvocations

        for (CtInvocation<?> invocation : allInvocations) {
            if (invocation.getPosition().isValidPosition() && 
                invocation.getPosition().getLine() == targetLine &&
                invocation.getExecutable().getSimpleName().equals(targetName)) {
                
                artifactData = new LinkedHashMap<>();
                artifactData.put("artifactType", invocation.getClass().getSimpleName());
                artifactData.put("methodName", invocation.getExecutable().getSimpleName());
                
                // --- CORRECCIÓN 1: TIPO DE RETORNO ---
                spoon.reflect.reference.CtTypeReference<?> returnTypeRef = invocation.getType();
                String returnType = (returnTypeRef != null) ? returnTypeRef.getQualifiedName() : "UNRESOLVED_TYPE";
                artifactData.put("returnType", returnType);

                // --- CORRECCIÓN 2: TIPO DEL QUALIFIER ---
                CtExpression<?> target = invocation.getTarget();
                if (target != null) {
                    spoon.reflect.reference.CtTypeReference<?> qualifierTypeRef = target.getType();
                    String qualifierType = (qualifierTypeRef != null) ? qualifierTypeRef.getQualifiedName() : "UNRESOLVED_TYPE";
                    artifactData.put("qualifierType", qualifierType);
                    artifactData.put("qualifierExpression", target.toString());
                } else {
                    artifactData.put("qualifierType", "static_implicit");
                }
                
                // --- CORRECCIÓN 3: TIPOS DE LOS ARGUMENTOS ---
                List<Map<String, String>> arguments = new ArrayList<>();
                for (CtExpression<?> arg : invocation.getArguments()) {
                    Map<String, String> argInfo = new LinkedHashMap<>();
                    argInfo.put("argumentExpression", arg.toString());
                    
                    spoon.reflect.reference.CtTypeReference<?> argTypeRef = arg.getType();
                    String argumentType = (argTypeRef != null) ? argTypeRef.getQualifiedName() : "UNRESOLVED_TYPE";
                    argInfo.put("argumentType", argumentType);
                    arguments.add(argInfo);
                }
                artifactData.put("arguments", arguments);

                break;
            }
        }

        // 5. Convertir el mapa a JSON e imprimirlo
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String jsonOutput = gson.toJson(artifactData);
        System.out.println(jsonOutput);
    }
}