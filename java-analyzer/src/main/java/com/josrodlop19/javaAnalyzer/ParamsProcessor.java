package com.josrodlop19.javaAnalyzer;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import spoon.reflect.code.CtAbstractInvocation;
import spoon.reflect.code.CtConstructorCall;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.declaration.CtParameter;
import spoon.reflect.reference.CtTypeReference;

public class ParamsProcessor {
    
    private static final int MAX_RECURSION_DEPTH = 5;
    
    public static List<Map<String, Object>> extractParamsFromSpoonDeclaration(CtExecutable<?> functionDeclaration,
            List<CtExpression<?>> arguments) {
        return extractParamsFromSpoonDeclaration(functionDeclaration, arguments, 0);
    }
    
    public static List<Map<String, Object>> extractParamsFromSpoonDeclaration(CtExecutable<?> functionDeclaration,
            List<CtExpression<?>> arguments, int recursionDepth) {
        List<Map<String, Object>> paramsData = new ArrayList<>();
        
        for (int i = 0; i < arguments.size(); i++) {
            CtExpression<?> param = arguments.get(i);
            CtTypeReference<?> paramType = param.getType();
            Map<String, Object> paramInfo = new LinkedHashMap<>();
            paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");
            
            List<CtParameter<?>> declarationParams = functionDeclaration.getParameters();
            if (i < declarationParams.size()) {
                CtTypeReference<?> declarationType = declarationParams.get(i).getType();
                paramInfo.put("parameterName", declarationParams.get(i).getSimpleName());
                paramInfo.put("typeAtDeclaration",
                        (declarationType != null) ? declarationType.getQualifiedName() : "UNRESOLVED_TYPE");
                
                // Extract recursive constructor info
                if (recursionDepth < MAX_RECURSION_DEPTH && declarationType != null) {
                    List<Map<String, Object>> constructorInfo = OutputDataBuilder.extractConstructorInfo(declarationType, recursionDepth + 1);
                    if (!constructorInfo.isEmpty()) {
                        paramInfo.put("parameterConstructors", constructorInfo.toString());
                    }
                }
            } else {
                paramInfo.put("possibleArray", "true");
            }
            
            // Also extract constructors of the type at call if different from declaration
            if (recursionDepth < MAX_RECURSION_DEPTH && paramType != null && 
                !paramInfo.get("typeAtCall").equals(paramInfo.get("typeAtDeclaration"))) {
                List<Map<String, Object>> callTypeConstructors = OutputDataBuilder.extractConstructorInfo(paramType, recursionDepth + 1);
                if (!callTypeConstructors.isEmpty()) {
                    paramInfo.put("callTypeConstructors", callTypeConstructors.toString());
                }
            }
            
            paramsData.add(paramInfo);
        }
        return paramsData;
    }

    public static List<Map<String, Object>> extractParamsFromReflection(List<CtExpression<?>> arguments,
            CtAbstractInvocation<?> invocation, String targetName) {
        return extractParamsFromReflection(arguments, invocation, targetName, 0);
    }
    
    public static List<Map<String, Object>> extractParamsFromReflection(List<CtExpression<?>> arguments,
            CtAbstractInvocation<?> invocation, String targetName, int recursionDepth) {
        List<Map<String, Object>> paramsData = new ArrayList<>();
        
        try {
            // Check the type of invocation
            if (invocation instanceof CtInvocation<?>) {
                return extractParamsFromMethodReflection(arguments, (CtInvocation<?>) invocation, targetName, recursionDepth);
            } else if (invocation instanceof CtConstructorCall<?>) {
                return extractParamsFromConstructorReflection(arguments, (CtConstructorCall<?>) invocation, targetName, recursionDepth);
            } else {
                // Fallback for unsupported types
                extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
                return paramsData;
            }
        } catch (Exception e) {
            System.err.println("Error usando reflection: " + e.getMessage());
            extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
        }
        
        return paramsData;
    }

    private static List<Map<String, Object>> extractParamsFromMethodReflection(List<CtExpression<?>> arguments,
            CtInvocation<?> invocation, String targetName, int recursionDepth) {
        List<Map<String, Object>> paramsData = new ArrayList<>();

        try {
            CtExpression<?> target = invocation.getTarget();
            if (target == null) {
                extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
                return paramsData;
            }
            
            CtTypeReference<?> qualifierTypeRef = target.getType();
            if (qualifierTypeRef == null) {
                extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
                return paramsData;
            }
            
            String qualifierClassName = qualifierTypeRef.getQualifiedName();
            Class<?> clazz = SpoonClassLoader.getInstance().getClassLoader().loadClass(qualifierClassName);
            
            Class<?>[] argTypes = new Class<?>[arguments.size()];
            for (int i = 0; i < arguments.size(); i++) {
                CtExpression<?> arg = arguments.get(i);
                CtTypeReference<?> argType = arg.getType();
                if (argType != null) {
                    try {
                        argTypes[i] = loadClassFromType(argType, SpoonClassLoader.getInstance().getClassLoader());
                    } catch (Exception e) {
                        argTypes[i] = Object.class;
                    }
                } else {
                    argTypes[i] = Object.class;
                }
            }
            
            Method method = findMatchingMethod(clazz, targetName, argTypes);
            if (method != null) {
                Parameter[] parameters = method.getParameters();
                for (int i = 0; i < arguments.size(); i++) {
                    CtExpression<?> param = arguments.get(i);
                    CtTypeReference<?> paramType = param.getType();
                    Map<String, Object> paramInfo = new LinkedHashMap<>();
                    paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");
                    
                    if (i < parameters.length) {
                        Parameter reflectionParam = parameters[i];
                        paramInfo.put("parameterName", reflectionParam.getName());
                        paramInfo.put("typeAtDeclaration", reflectionParam.getType().getName());
                        
                        // Extract recursive constructor info
                        if (recursionDepth < MAX_RECURSION_DEPTH) {
                            List<Map<String, Object>> constructorInfo = extractConstructorInfoFromClass(
                                reflectionParam.getType(), recursionDepth + 1);
                            if (!constructorInfo.isEmpty()) {
                                paramInfo.put("parameterConstructors", constructorInfo.toString());
                            }
                        }
                    } else {
                        paramInfo.put("possibleArray", "true");
                    }

                    // Also extract constructors of the type at call
                    if (recursionDepth < MAX_RECURSION_DEPTH && paramType != null) {
                        try {
                            Class<?> callTypeClass = loadClassFromType(paramType, SpoonClassLoader.getInstance().getClassLoader());
                            List<Map<String, Object>> callTypeConstructors = extractConstructorInfoFromClass(
                                callTypeClass, recursionDepth + 1);
                            if (!callTypeConstructors.isEmpty()) {
                                paramInfo.put("callTypeConstructors", callTypeConstructors.toString());
                            }
                        } catch (Exception e) {
                            // Ignore errors in extracting call type constructors
                        }
                    }
                    
                    paramsData.add(paramInfo);
                }
            } else {
                extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
            }
        } catch (Exception e) {
            System.err.println("Error usando reflection para método: " + e.getMessage());
            extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
        }
        
        return paramsData;
    }

    private static List<Map<String, Object>> extractParamsFromConstructorReflection(List<CtExpression<?>> arguments,
            CtConstructorCall<?> constructorCall, String targetName, int recursionDepth) {
        List<Map<String, Object>> paramsData = new ArrayList<>();
        
        try {
            CtTypeReference<?> constructedType = constructorCall.getType();
            if (constructedType == null) {
                extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
                return paramsData;
            }
            
            String className = constructedType.getQualifiedName();
            Class<?> clazz = SpoonClassLoader.getInstance().getClassLoader().loadClass(className);
            
            Class<?>[] argTypes = new Class<?>[arguments.size()];
            for (int i = 0; i < arguments.size(); i++) {
                CtExpression<?> arg = arguments.get(i);
                CtTypeReference<?> argType = arg.getType();
                if (argType != null) {
                    try {
                        argTypes[i] = loadClassFromType(argType, SpoonClassLoader.getInstance().getClassLoader());
                    } catch (Exception e) {
                        argTypes[i] = Object.class;
                    }
                } else {
                    argTypes[i] = Object.class;
                }
            }
            
            Constructor<?> constructor = findMatchingConstructor(clazz, argTypes);
            if (constructor != null) {
                Parameter[] parameters = constructor.getParameters();
                for (int i = 0; i < arguments.size(); i++) {
                    CtExpression<?> param = arguments.get(i);
                    CtTypeReference<?> paramType = param.getType();
                    Map<String, Object> paramInfo = new LinkedHashMap<>();
                    paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");
                    
                    if (i < parameters.length) {
                        Parameter reflectionParam = parameters[i];
                        paramInfo.put("parameterName", reflectionParam.getName());
                        paramInfo.put("typeAtDeclaration", reflectionParam.getType().getName());
                        
                        // Extract recursive constructor info
                        if (recursionDepth < MAX_RECURSION_DEPTH) {
                            List<Map<String, Object>> constructorInfo = extractConstructorInfoFromClass(
                                reflectionParam.getType(), recursionDepth + 1);
                            if (!constructorInfo.isEmpty()) {
                                paramInfo.put("parameterConstructors", constructorInfo.toString());
                            }
                        }
                    } else {
                        paramInfo.put("possibleArray", "true");
                    }

                    // Also extract constructors of the type at call
                    if (recursionDepth < MAX_RECURSION_DEPTH && paramType != null) {
                        try {
                            Class<?> callTypeClass = loadClassFromType(paramType, SpoonClassLoader.getInstance().getClassLoader());
                            List<Map<String, Object>> callTypeConstructors = extractConstructorInfoFromClass(
                                callTypeClass, recursionDepth + 1);
                            if (!callTypeConstructors.isEmpty()) {
                                paramInfo.put("callTypeConstructors", callTypeConstructors.toString());
                            }
                        } catch (Exception e) {
                            // Ignore errors in extracting call type constructors
                        }
                    }
                    
                    paramsData.add(paramInfo);
                }
            } else {
                extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
            }
        } catch (Exception e) {
            System.err.println("Error usando reflection para constructor: " + e.getMessage());
            extractParamsFromReflectionFallback(arguments, paramsData, recursionDepth);
        }
        
        return paramsData;
    }

    private static void extractParamsFromReflectionFallback(List<CtExpression<?>> arguments,
            List<Map<String, Object>> paramsData, int recursionDepth) {
        for (int i = 0; i < arguments.size(); i++) {
            CtExpression<?> param = arguments.get(i);
            CtTypeReference<?> paramType = param.getType();
            Map<String, Object> paramInfo = new LinkedHashMap<>();
            paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");
            paramInfo.put("typeAtDeclaration", "UNRESOLVED_TYPE");
            paramInfo.put("parameterName", "param" + i);
            
            // Try to extract constructors of the type at call
            if (recursionDepth < MAX_RECURSION_DEPTH && paramType != null) {
                List<Map<String, Object>> constructorInfo = OutputDataBuilder.extractConstructorInfo(paramType, recursionDepth + 1);
                if (!constructorInfo.isEmpty()) {
                    paramInfo.put("fallbackConstructors", constructorInfo.toString());
                }
            }
            
            paramsData.add(paramInfo);
        }
    }
    
    private static List<Map<String, Object>> extractConstructorInfoFromClass(Class<?> clazz, int recursionDepth) {
        List<Map<String, Object>> constructorsInfo = new ArrayList<>();
        
        if (clazz == null || recursionDepth >= MAX_RECURSION_DEPTH || isPrimitiveOrBasicType(clazz.getName())) {
            return constructorsInfo;
        }
        
        try {
            Constructor<?>[] constructors = clazz.getConstructors();
            
            for (Constructor<?> constructor : constructors) {
                Map<String, Object> constructorInfo = new LinkedHashMap<>();
                constructorInfo.put("className", clazz.getSimpleName());
                constructorInfo.put("qualifierType", clazz.getName());
                constructorInfo.put("isPublic", java.lang.reflect.Modifier.isPublic(constructor.getModifiers()));
                
                // Params details
                List<Map<String, Object>> paramDetails = new ArrayList<>();
                Parameter[] params = constructor.getParameters();
                
                for (Parameter param : params) {
                    Map<String, Object> paramInfo = new LinkedHashMap<>();
                    paramInfo.put("name", param.getName());
                    paramInfo.put("type", param.getType().getName());
                    
                    // Recursive extraction of constructor info for parameter types
                    if (!isPrimitiveOrBasicType(param.getType().getName())) {
                        List<Map<String, Object>> nestedConstructors = extractConstructorInfoFromClass(
                            param.getType(), recursionDepth + 1);
                        if (!nestedConstructors.isEmpty()) {
                            paramInfo.put("parameterConstructors", nestedConstructors);
                        }
                    }
                    
                    paramDetails.add(paramInfo);
                }
                
                constructorInfo.put("parameters", paramDetails);
                constructorsInfo.add(constructorInfo);
            }
        } catch (Exception e) {
            System.err.println("Error extracting constructor info from class " + clazz.getName() + ": " + e.getMessage());
        }
        
        return constructorsInfo;
    }

    // Auxiliary methods for reflection and type matching
    private static Constructor<?> findMatchingConstructor(Class<?> clazz, Class<?>[] argTypes) {
        try {
            // First try to find an exact match
            return clazz.getConstructor(argTypes);
        } catch (NoSuchMethodException e) {
            // If no exact match, look for a compatible one
            Constructor<?>[] constructors = clazz.getConstructors();
            for (Constructor<?> constructor : constructors) {
                Class<?>[] paramTypes = constructor.getParameterTypes();
                if (paramTypes.length == argTypes.length) {
                    boolean matches = true;
                    for (int i = 0; i < paramTypes.length; i++) {
                        if (!paramTypes[i].isAssignableFrom(argTypes[i]) && 
                            !argTypes[i].equals(Object.class) &&
                            !areCompatibleTypes(paramTypes[i], argTypes[i])) {
                            matches = false;
                            break;
                        }
                    }
                    if (matches) {
                        return constructor;
                    }
                }
            }
        }
        return null;
    }

    private static Class<?> loadClassFromType(CtTypeReference<?> typeRef, ClassLoader spoonClassLoader) throws ClassNotFoundException {
        String typeName = typeRef.getQualifiedName();
        switch (typeName) {
            case "int":
                return int.class;
            case "long":
                return long.class;
            case "double":
                return double.class;
            case "float":
                return float.class;
            case "boolean":
                return boolean.class;
            case "char":
                return char.class;
            case "byte":
                return byte.class;
            case "short":
                return short.class;
            default:
                return spoonClassLoader.loadClass(typeName);
        }
    }

    private static Method findMatchingMethod(Class<?> clazz, String methodName, Class<?>[] argTypes) {
        Method[] methods = clazz.getMethods();
        // Look for an exact match with parameter types
        for (Method method : methods) {
            if (method.getName().equals(methodName) &&
                    method.getParameterCount() == argTypes.length) {
                Class<?>[] paramTypes = method.getParameterTypes();
                boolean matches = true;
                for (int i = 0; i < paramTypes.length; i++) {
                    if (!paramTypes[i].isAssignableFrom(argTypes[i]) &&
                            !areCompatibleTypes(paramTypes[i], argTypes[i])) {
                        matches = false;
                        break;
                    }
                }
                if (matches) {
                    return method;
                }
            }
        }
        // If not found an exact match, look for a method with the same name and
        // parameter count
        for (Method method : methods) {
            if (method.getName().equals(methodName) &&
                    method.getParameterCount() == argTypes.length) {
                return method;
            }
        }
        return null;
    }

    private static boolean areCompatibleTypes(Class<?> paramType, Class<?> argType) {
        if (paramType.isPrimitive() && !argType.isPrimitive() || !paramType.isPrimitive() && argType.isPrimitive()) {
            return isWrapperType(paramType, argType) || isWrapperType(argType, paramType);
        }
        return paramType.equals(argType);
    }

    private static boolean isWrapperType(Class<?> primitive, Class<?> wrapper) {
        return (primitive == int.class && wrapper == Integer.class) ||
                (primitive == long.class && wrapper == Long.class) ||
                (primitive == double.class && wrapper == Double.class) ||
                (primitive == float.class && wrapper == Float.class) ||
                (primitive == boolean.class && wrapper == Boolean.class) ||
                (primitive == char.class && wrapper == Character.class) ||
                (primitive == byte.class && wrapper == Byte.class) ||
                (primitive == short.class && wrapper == Short.class);
    }

    private static boolean isPrimitiveOrBasicType(String typeName) {
        return typeName.equals("int") || typeName.equals("long") || typeName.equals("double") || 
               typeName.equals("float") || typeName.equals("boolean") || typeName.equals("char") ||
               typeName.equals("byte") || typeName.equals("short") || typeName.equals("void") ||
               typeName.equals("java.lang.String") || typeName.equals("java.lang.Integer") ||
               typeName.equals("java.lang.Long") || typeName.equals("java.lang.Double") ||
               typeName.equals("java.lang.Float") || typeName.equals("java.lang.Boolean") ||
               typeName.equals("java.lang.Character") || typeName.equals("java.lang.Byte") ||
               typeName.equals("java.lang.Short") || typeName.equals("java.lang.Object") ||
               typeName.startsWith("java.util.") || typeName.startsWith("java.io.") ||
               typeName.startsWith("java.net.") || typeName.startsWith("java.time.");
    }
}