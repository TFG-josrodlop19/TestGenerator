package com.josrodlop19.javaAnalyzer;

import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.declaration.CtParameter;
import spoon.reflect.reference.CtTypeReference;

public class ParamsProcessor {
    public static List<Map<String, String>> extractParamsFromSpoonDeclaration(CtExecutable<?> functionDeclaration,
            List<CtExpression<?>> arguments) {
        List<Map<String, String>> paramsData = new ArrayList<>();
        for (int i = 0; i < arguments.size(); i++) {
            CtExpression<?> param = arguments.get(i);
            CtTypeReference<?> paramType = param.getType();

            Map<String, String> paramInfo = new HashMap<>();
            paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");

            List<CtParameter<?>> declarationParams = functionDeclaration.getParameters();
            if (i < declarationParams.size()) {
                CtTypeReference<?> declarationType = declarationParams.get(i).getType();
                paramInfo.put("parameterName", declarationParams.get(i).getSimpleName());
                paramInfo.put("typeAtDeclaration",
                        (declarationType != null) ? declarationType.getQualifiedName() : "UNRESOLVED_TYPE");
            } else {
                paramInfo.put("possibleArray", "true");
            }

            paramsData.add(paramInfo);
        }
        return paramsData;
    }

    public static List<Map<String, String>> extractParamsFromReflection(List<CtExpression<?>> arguments,
            CtInvocation<?> invocation, String targetName) {
        List<Map<String, String>> paramsData = new ArrayList<>();
        try {
            // Target = object on which the method is called. F.E: in
            // myObject.myMethod(arg1, arg2) target = myObject
            CtExpression<?> target = invocation.getTarget();
            if (target == null) {
                // Local call, no target
                extractParamsFromReflectionFallback(arguments, paramsData);
                return paramsData;
            }

            CtTypeReference<?> qualifierTypeRef = target.getType();
            if (qualifierTypeRef == null) {
                extractParamsFromReflectionFallback(arguments, paramsData);
                return paramsData;
            }

            String qualifierClassName = qualifierTypeRef.getQualifiedName();

            // Load class using Spoon's classloader
            Class<?> clazz = SpoonClassLoader.getInstance().getClassLoader().loadClass(qualifierClassName);

            // Get the types of the arguments to get the correct method
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

            // Look for the method in the class using reflection
            Method method = findMatchingMethod(clazz, targetName, argTypes);

            if (method != null) {
                Parameter[] parameters = method.getParameters();
                for (int i = 0; i < arguments.size(); i++) {
                    CtExpression<?> param = arguments.get(i);
                    CtTypeReference<?> paramType = param.getType();

                    Map<String, String> paramInfo = new HashMap<>();
                    paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");

                    if (i < parameters.length) {
                        Parameter reflectionParam = parameters[i];
                        paramInfo.put("parameterName", reflectionParam.getName());
                        paramInfo.put("typeAtDeclaration", reflectionParam.getType().getName());
                    } else {
                        paramInfo.put("possibleArray", "true");
                    }

                    paramsData.add(paramInfo);
                }
            } else {
                extractParamsFromReflectionFallback(arguments, paramsData);
            }

        } catch (Exception e) {
            System.err.println("Error usando reflection: " + e.getMessage());
            extractParamsFromReflectionFallback(arguments, paramsData);
        }
        return paramsData;
    }

    private static void extractParamsFromReflectionFallback(List<CtExpression<?>> arguments,
            List<Map<String, String>> paramsData) {
        for (int i = 0; i < arguments.size(); i++) {
            CtExpression<?> param = arguments.get(i);
            CtTypeReference<?> paramType = param.getType();

            Map<String, String> paramInfo = new HashMap<>();
            paramInfo.put("typeAtCall", (paramType != null) ? paramType.getQualifiedName() : "UNRESOLVED_TYPE");
            paramInfo.put("typeAtDeclaration", "UNRESOLVED_TYPE");
            paramInfo.put("parameterName", "param" + i);

            paramsData.add(paramInfo);
        }
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
            return isWrapperType(paramType, argType);
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
}
