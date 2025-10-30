"""
Скрипт для проверки покрытия всех 143 формул в интерфейсе
"""
import re
import os
import sys
from pathlib import Path
from collections import defaultdict

# Установка кодировки UTF-8 для вывода
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def extract_formulas_from_file(filepath):
    """Извлекает упоминания формул из файла"""
    formulas = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ищем Ф.XX
            matches = re.findall(r'Ф\.(\d+)', content)
            formulas.update(int(m) for m in matches)
    except Exception as e:
        print(f"Ошибка при чтении {filepath}: {e}")
    return formulas

def main():
    # Путь к проекту
    project_root = Path(__file__).parent.parent
    ui_dir = project_root / "ui"

    # Словарь для отслеживания формул по файлам
    formula_locations = defaultdict(list)
    all_found_formulas = set()

    # Список файлов для проверки
    files_to_check = [
        "forest_restoration_tab.py",
        "land_reclamation_tab.py",
        "permanent_forest_tab.py",
        "protective_forest_tab.py",
        "agricultural_absorption_tab.py",
        "land_conversion_tab.py",
    ]

    # Также проверим все категории выбросов
    for i in range(25):
        files_to_check.append(f"category_{i}_tab.py")

    print("="*80)
    print("ПРОВЕРКА ПОКРЫТИЯ ФОРМУЛ В ИНТЕРФЕЙСЕ")
    print("="*80)
    print()

    # Проверяем каждый файл
    for filename in files_to_check:
        filepath = ui_dir / filename
        if filepath.exists():
            formulas = extract_formulas_from_file(filepath)
            if formulas:
                for formula_num in formulas:
                    formula_locations[formula_num].append(filename)
                    all_found_formulas.add(formula_num)
                print(f"✓ {filename}: найдено формул {len(formulas)}")
                if formulas:
                    sorted_formulas = sorted(formulas)
                    print(f"  Формулы: {sorted_formulas}")

    print()
    print("="*80)
    print("СТАТИСТИКА ПОКРЫТИЯ")
    print("="*80)
    print()

    # Анализ по диапазонам
    ranges = [
        (1, 12, "Лесовосстановление"),
        (13, 26, "Рекультивация земель"),
        (27, 59, "Постоянные леса"),
        (60, 76, "Защитные лесополосы"),
        (77, 90, "Сельскохозяйственные земли"),
        (91, 100, "Конверсия земель"),
        (101, 143, "Водно-болотные экосистемы и др."),
    ]

    total_found = 0
    total_missing = 0

    for start, end, name in ranges:
        found_in_range = [f for f in all_found_formulas if start <= f <= end]
        expected = list(range(start, end + 1))
        missing = [f for f in expected if f not in found_in_range]

        coverage = len(found_in_range) / len(expected) * 100 if expected else 0

        print(f"\n{name} (Ф.{start}-{end}):")
        print(f"  Найдено: {len(found_in_range)}/{len(expected)} ({coverage:.1f}%)")

        if found_in_range:
            print(f"  ✓ Реализованы: {sorted(found_in_range)}")

        if missing:
            print(f"  ✗ Отсутствуют: {missing}")
            total_missing += len(missing)

        total_found += len(found_in_range)

    print()
    print("="*80)
    print("ОБЩАЯ СТАТИСТИКА")
    print("="*80)
    print(f"Всего формул в стандарте: 143")
    print(f"Найдено в коде: {total_found}")
    print(f"Отсутствует: {total_missing}")
    print(f"Общее покрытие: {total_found/143*100:.1f}%")
    print()

    # Список всех найденных формул
    print("="*80)
    print("ПОЛНЫЙ СПИСОК НАЙДЕННЫХ ФОРМУЛ")
    print("="*80)
    sorted_all = sorted(all_found_formulas)
    print(f"Найдены формулы: {sorted_all}")
    print(f"Количество: {len(sorted_all)}")
    print()

    # Проверка дублирования
    print("="*80)
    print("ПРОВЕРКА ДУБЛИРОВАНИЯ ФОРМУЛ")
    print("="*80)
    duplicates_found = False
    for formula_num in sorted(formula_locations.keys()):
        locations = formula_locations[formula_num]
        if len(locations) > 1:
            print(f"⚠ Ф.{formula_num} используется в нескольких файлах: {locations}")
            duplicates_found = True

    if not duplicates_found:
        print("✓ Дублирования не обнаружено - каждая формула в своем файле")
    print()

    # Проверка отсутствующих диапазонов
    print("="*80)
    print("КРИТИЧЕСКИЕ ЗАМЕЧАНИЯ")
    print("="*80)

    # Проверим диапазон 101-143
    missing_101_143 = [f for f in range(101, 144) if f not in all_found_formulas]
    if missing_101_143:
        print(f"\n⚠ КРИТИЧНО: Формулы 101-143 ({len(missing_101_143)} шт.) не найдены в интерфейсе!")
        print(f"   Отсутствуют: {missing_101_143}")
        print(f"   Эти формулы относятся к водно-болотным экосистемам и другим категориям")

    # Сохранение отчета
    report_path = project_root / "docs" / "FORMULA_COVERAGE_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Отчет о покрытии формул\n\n")
        f.write(f"**Дата:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Общая статистика\n\n")
        f.write(f"- Всего формул в стандарте: **143**\n")
        f.write(f"- Найдено в коде: **{total_found}**\n")
        f.write(f"- Отсутствует: **{total_missing}**\n")
        f.write(f"- Общее покрытие: **{total_found/143*100:.1f}%**\n\n")

        f.write("## Покрытие по категориям\n\n")
        for start, end, name in ranges:
            found_in_range = [f for f in all_found_formulas if start <= f <= end]
            expected = list(range(start, end + 1))
            missing = [f for f in expected if f not in found_in_range]
            coverage = len(found_in_range) / len(expected) * 100 if expected else 0

            f.write(f"### {name} (Ф.{start}-{end})\n\n")
            f.write(f"- Покрытие: **{coverage:.1f}%** ({len(found_in_range)}/{len(expected)})\n")
            if found_in_range:
                f.write(f"- ✓ Реализованы: {sorted(found_in_range)}\n")
            if missing:
                f.write(f"- ✗ Отсутствуют: {missing}\n")
            f.write("\n")

        f.write("## Отсутствующие формулы\n\n")
        all_missing = [f for f in range(1, 144) if f not in all_found_formulas]
        if all_missing:
            f.write(f"Всего отсутствует: **{len(all_missing)}** формул\n\n")
            f.write(f"Список: {all_missing}\n")
        else:
            f.write("Все формулы реализованы!\n")

    print(f"\n✓ Отчет сохранен в: {report_path}")

if __name__ == "__main__":
    main()
