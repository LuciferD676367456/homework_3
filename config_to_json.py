import json
import re
import sys

def parse_constant_declaration(line, constants):
    """Обрабатывает объявление константы."""
    match = re.match(r"def\s+([a-z][a-z0-9_]*)\s*:=\s*(.+);", line)
    if not match:
        raise ValueError(f"Синтаксическая ошибка в строке: {line}")
    name, value = match.groups()
    constants[name] = parse_value(value, constants)

def parse_value(value, constants):
    """Парсит значение (число, массив, словарь, строку или константу)."""
    value = value.strip().rstrip(";")  # Удаляем ; в конце строки
    print(f"[DEBUG] Парсим значение: {value}")  # Отладочный вывод

    # Число
    if re.match(r"^-?\d+$", value):
        return int(value)

    # Строка
    if value.startswith("\"") and value.endswith("\""):
        return value[1:-1]

    # Массив
    if value.startswith("#(") and value.endswith(")"):
        elements = value[2:-1].strip()
        if not elements:
            return []  # Пустой массив
        return [parse_value(el.strip(), constants) for el in split_elements(elements)]

    # Словарь
    if value.startswith("$[") and value.endswith("]"):
        items = value[2:-1].strip()
        if not items:
            return {}  # Пустой словарь
        result = {}
        for item in split_elements(items, separator=","):
            key, val = item.split(":", 1)
            result[key.strip()] = parse_value(val.strip(), constants)
        return result

    # Константа
    constant_match = re.match(r"@{([a-z][a-z0-9_]*)}", value)
    if constant_match:
        constant_name = constant_match.group(1)
        if constant_name not in constants:
            raise ValueError(f"Константа '{constant_name}' не определена.")
        return constants[constant_name]

    raise ValueError(f"Неверный формат значения: {value}")

def split_elements(s, separator=","):
    """Разделяет элементы массива или словаря, учитывая вложенные структуры."""
    elements = []
    current = []
    brackets = 0
    parentheses = 0
    in_string = False

    for char in s:
        if char == '"' and (not current or current[-1] != '\\'):
            in_string = not in_string
        if not in_string:
            if char in "([":
                brackets += 1
            elif char in ")]":
                brackets -= 1
            elif char == '(':
                parentheses += 1
            elif char == ')':
                parentheses -= 1
            elif char == separator and brackets == 0 and parentheses == 0:
                elements.append(''.join(current).strip())
                current = []
                continue
        current.append(char)
    if current:
        elements.append(''.join(current).strip())
    return elements

def parse_multiline_structure(lines, start_index, initial_value):
    """Обрабатывает многострочные массивы или словари, начиная с initial_value."""
    structure_lines = [initial_value]
    open_brackets = initial_value.count("[") + initial_value.count("(") - initial_value.count("]") - initial_value.count(")")
    i = start_index

    while i < len(lines):
        line = lines[i].strip()
        structure_lines.append(line)
        open_brackets += line.count("[") + line.count("(") - line.count("]") - line.count(")")
        if open_brackets == 0:
            break
        i += 1

    if open_brackets != 0:
        raise ValueError("Незакрытая структура в многострочном значении.")

    full_structure = " ".join(structure_lines)
    print(f"[DEBUG] Полностью собранная структура: {full_structure}")  # Отладочный вывод
    return full_structure.strip(), i

def parse_input(input_text):
    """Парсит входной текст на учебном конфигурационном языке."""
    constants = {}
    config = {}

    lines = input_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        print(f"[DEBUG] Обрабатываем строку: {line}")  # Отладочный вывод

        if not line or line.startswith("#"):
            i += 1
            continue  # Пропуск пустых строк и комментариев

        if line.startswith("def"):
            # Обработка объявления константы
            parse_constant_declaration(line, constants)
        else:
            # Обработка ключ: значение
            if ':' not in line:
                raise ValueError(f"Ожидалась пара 'ключ: значение', но получено: {line}")
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith("$[") or value.startswith("#("):
                # Проверка, завершена ли структура на той же строке
                if (value.startswith("$[") and value.endswith("]")) or (value.startswith("#(") and value.endswith(")")):
                    # Однострочная структура
                    config[key] = parse_value(value, constants)
                else:
                    # Многострочная структура
                    value, end_index = parse_multiline_structure(lines, i + 1, initial_value=value)
                    print(f"[DEBUG] Многострочная структура для ключа '{key}': {value}")
                    config[key] = parse_value(value, constants)
                    i = end_index
            else:
                # Однострочное значение
                config[key] = parse_value(value, constants)

        i += 1

    return config

def main():
    """Главная функция для запуска из командной строки."""
    input_text = sys.stdin.read()
    try:
        result = parse_input(input_text)
        print(json.dumps(result, indent=4, ensure_ascii=False))
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
