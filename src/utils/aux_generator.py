
# TODO: ampliar a otros tipos de datos
# TODO: cambiar por un switch para mejorar la legibilidad
def select_fuzzing_parama_function(param_type, is_last: bool) -> str:
    fuzzing_function = "Consume" if is_last else "ConsumeRemainingAs"
    if param_type == "byte":
        # TODO: plantear si poner un limite de bytes o no
        fuzzing_function += "Bytes()"
    return fuzzing_function


def type_parser_to_java_type(param_type: str) -> str:
    match param_type:
        case "byte":
            return "byte[]"
        case "int":
            return "int"
        case "long":
            return "long"
        case "float":
            return "float"
        case "double":
            return "double"
        case "boolean":
            return "boolean"
        case _:
            return "Object"
    


def type_selector_function_for_fuzzing_param(params: list[dict]) -> str:
    parsed_params = []
    print(params)
    for param in params:
        print(param)
        parsed_params.append({
            "name": param["name"],
            "type": type_parser_to_java_type(param["type"]),
            "fuzzing_function": select_fuzzing_parama_function(param["type"], is_last=(param == params[-1]))
        })
    print(parsed_params)
    return parsed_params