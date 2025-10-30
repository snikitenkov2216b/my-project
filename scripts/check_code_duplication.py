"""
Скрипт для поиска дублирования кода в проекте
"""
import re
import os
import sys
from pathlib import Path
from collections import defaultdict
import hashlib

# Установка кодировки UTF-8 для вывода
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def extract_methods(filepath):
    """Извлекает методы из Python файла"""
    methods = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

            # Ищем определения методов
            method_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*(?:->.*?)?:'
            for match in re.finditer(method_pattern, content):
                methods.append(match.group(1))

    except Exception as e:
        print(f"Ошибка при чтении {filepath}: {e}")

    return methods

def extract_imports(filepath):
    """Извлекает импорты из файла"""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
    except:
        pass
    return imports

def find_similar_code_blocks(project_root, min_lines=10):
    """Ищет похожие блоки кода"""
    ui_dir = project_root / "ui"
    calc_dir = project_root / "calculations"

    # Хэши блоков кода
    code_blocks = defaultdict(list)

    for directory in [ui_dir, calc_dir]:
        for filepath in directory.glob("*.py"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Разбиваем на блоки по min_lines строк
                for i in range(len(lines) - min_lines + 1):
                    block = ''.join(lines[i:i+min_lines])
                    # Удаляем пробелы и комментарии для сравнения
                    normalized = re.sub(r'#.*$', '', block, flags=re.MULTILINE)
                    normalized = re.sub(r'\s+', ' ', normalized).strip()

                    if len(normalized) > 50:  # Игнорируем слишком короткие блоки
                        block_hash = hashlib.md5(normalized.encode()).hexdigest()
                        code_blocks[block_hash].append((filepath, i+1, min_lines))
            except:
                pass

    # Находим дубликаты
    duplicates = {k: v for k, v in code_blocks.items() if len(v) > 1}
    return duplicates

def main():
    project_root = Path(__file__).parent.parent

    print("="*80)
    print("АНАЛИЗ ДУБЛИРОВАНИЯ КОДА")
    print("="*80)
    print()

    # 1. Проверка повторяющихся импортов
    print("1. АНАЛИЗ ИМПОРТОВ")
    print("="*80)

    ui_dir = project_root / "ui"
    calc_dir = project_root / "calculations"

    all_imports = defaultdict(list)

    for directory in [ui_dir, calc_dir]:
        for filepath in directory.glob("*.py"):
            imports = extract_imports(filepath)
            for imp in imports:
                all_imports[imp].append(filepath.name)

    # Наиболее часто используемые импорты
    common_imports = {k: v for k, v in all_imports.items() if len(v) > 10}
    print(f"\nИмпорты, используемые в >10 файлах:")
    for imp, files in sorted(common_imports.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"  {len(files):2d} файлов: {imp}")

    # 2. Проверка повторяющихся методов
    print("\n\n2. АНАЛИЗ ПОВТОРЯЮЩИХСЯ ИМЕН МЕТОДОВ")
    print("="*80)

    all_methods = defaultdict(list)

    for directory in [ui_dir, calc_dir]:
        for filepath in directory.glob("*.py"):
            methods = extract_methods(filepath)
            for method in methods:
                all_methods[method].append(filepath.name)

    # Методы с одинаковыми именами в разных файлах
    duplicate_names = {k: v for k, v in all_methods.items() if len(v) > 1}
    print(f"\nМетоды с одинаковыми именами в разных файлах (топ-20):")
    for method, files in sorted(duplicate_names.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
        print(f"  {method:30s} - {len(files)} файлов")
        if len(files) <= 5:
            print(f"    Файлы: {', '.join(set(files))}")

    # 3. Поиск похожих блоков кода
    print("\n\n3. ПОИСК ПОХОЖИХ БЛОКОВ КОДА (10+ строк)")
    print("="*80)

    duplicates = find_similar_code_blocks(project_root, min_lines=10)

    if duplicates:
        print(f"\nНайдено {len(duplicates)} групп дублированного кода:")
        for i, (hash_val, locations) in enumerate(list(duplicates.items())[:10], 1):
            print(f"\n  Группа {i}:")
            for filepath, line_num, num_lines in locations:
                print(f"    - {filepath.name}:{line_num} ({num_lines} строк)")
    else:
        print("\n✓ Значительного дублирования кода не обнаружено")

    # 4. Специфичный анализ для UI вкладок
    print("\n\n4. АНАЛИЗ UI ВКЛАДОК")
    print("="*80)

    # Проверяем категории выбросов
    category_tabs = list(ui_dir.glob("category_*_tab.py"))
    print(f"\nНайдено {len(category_tabs)} вкладок категорий выбросов")

    # Проверяем вкладки поглощения
    absorption_tabs = [
        "forest_restoration_tab.py",
        "land_reclamation_tab.py",
        "permanent_forest_tab.py",
        "protective_forest_tab.py",
        "agricultural_absorption_tab.py",
        "land_conversion_tab.py",
    ]

    existing_absorption = [f for f in absorption_tabs if (ui_dir / f).exists()]
    print(f"Найдено {len(existing_absorption)} вкладок поглощения")

    # Проверяем базовые классы
    base_classes = ["base_tab.py", "absorption_base_tab.py"]
    existing_bases = [f for f in base_classes if (ui_dir / f).exists()]
    print(f"\nБазовые классы: {existing_bases}")

    # 5. Проверка использования валидации
    print("\n\n5. АНАЛИЗ СИСТЕМЫ ВАЛИДАЦИИ")
    print("="*80)

    validation_patterns = {
        "create_line_edit": 0,
        "QDoubleValidator": 0,
        "validator_params": 0,
        "ValidationType": 0,
    }

    for filepath in ui_dir.glob("*.py"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in validation_patterns:
                    validation_patterns[pattern] += content.count(pattern)
        except:
            pass

    print("\nИспользование валидации:")
    for pattern, count in sorted(validation_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern:25s}: {count} раз")

    # 6. Рекомендации
    print("\n\n6. РЕКОМЕНДАЦИИ ПО РЕФАКТОРИНГУ")
    print("="*80)

    recommendations = []

    # Анализ повторяющихся методов
    calculate_methods = [m for m in duplicate_names.keys() if 'calculate' in m.lower()]
    if len(calculate_methods) > 5:
        recommendations.append(
            f"⚠ Обнаружено {len(calculate_methods)} методов с 'calculate' в имени. "
            "Рассмотрите создание базового класса Calculator с общими методами."
        )

    # Анализ импортов
    if len(common_imports) > 20:
        recommendations.append(
            f"⚠ {len(common_imports)} импортов используются очень часто. "
            "Рассмотрите создание общего модуля с часто используемыми импортами."
        )

    # Анализ дублирования
    if len(duplicates) > 20:
        recommendations.append(
            f"⚠ Обнаружено {len(duplicates)} блоков дублированного кода. "
            "Рекомендуется выделить общую логику в отдельные функции/классы."
        )

    # Анализ вкладок
    if len(category_tabs) > 20:
        recommendations.append(
            "⚠ Большое количество вкладок категорий. "
            "Рекомендуется использовать наследование от базового класса для уменьшения дублирования."
        )

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
    else:
        print("\n✓ Критичных проблем с дублированием кода не обнаружено")

    # Сохранение отчета
    report_path = project_root / "docs" / "CODE_DUPLICATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Отчет об анализе дублирования кода\n\n")
        f.write(f"**Дата:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## Статистика\n\n")
        f.write(f"- Вкладок категорий: {len(category_tabs)}\n")
        f.write(f"- Вкладок поглощения: {len(existing_absorption)}\n")
        f.write(f"- Методов с повторяющимися именами: {len(duplicate_names)}\n")
        f.write(f"- Групп дублированного кода: {len(duplicates)}\n\n")

        f.write("## Часто используемые импорты\n\n")
        for imp, files in sorted(common_imports.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
            f.write(f"- `{imp}` - {len(files)} файлов\n")

        f.write("\n## Методы с повторяющимися именами (топ-15)\n\n")
        for method, files in sorted(duplicate_names.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
            f.write(f"- `{method}` - {len(files)} файлов\n")

        f.write("\n## Рекомендации\n\n")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n\n")
        else:
            f.write("Критичных проблем не обнаружено.\n")

    print(f"\n\n✓ Отчет сохранен в: {report_path}")

if __name__ == "__main__":
    main()
