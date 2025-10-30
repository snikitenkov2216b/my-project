#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для проверки наличия всех 143 формул из Приказа Минприроды РФ от 27.05.2022 N 371
"""

import re
import os
from pathlib import Path

# Определение диапазонов формул по документу
FORMULA_RANGES = {
    # Выбросы (Categories 0-24)
    "Category 0-24": {
        "description": "Выбросы парниковых газов по категориям",
        "files": [f"ui/category_{i}_tab.py" for i in range(25)],
        "expected_count": "~100+ формул (в категориях)"
    },

    # Поглощение - Лесовосстановление (Ф. 1-12)
    "Forest Restoration": {
        "description": "Лесовосстановление и лесоразведение",
        "files": ["ui/forest_restoration_tab.py"],
        "formulas": list(range(1, 13)),
        "expected_count": 12
    },

    # Поглощение - Рекультивация (Ф. 13-26)
    "Land Reclamation": {
        "description": "Рекультивация нарушенных земель",
        "files": ["ui/land_reclamation_tab.py"],
        "formulas": list(range(13, 27)),
        "expected_count": 14
    },

    # Поглощение - Постоянные леса (Ф. 27-59)
    "Permanent Forest": {
        "description": "Постоянные лесные насаждения",
        "files": ["ui/permanent_forest_tab.py"],
        "formulas": list(range(27, 60)),
        "expected_count": 33
    },

    # Поглощение - Защитные лесополосы (Ф. 60-76)
    "Protective Forest": {
        "description": "Защитные лесные полосы",
        "files": ["ui/protective_forest_tab.py"],
        "formulas": list(range(60, 77)),
        "expected_count": 17
    },

    # Поглощение - Сельхоз земли (Ф. 75-90, 77-79)
    "Agricultural": {
        "description": "Сельскохозяйственные земли",
        "files": ["ui/agricultural_absorption_tab.py"],
        "formulas": [75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90],
        "expected_count": 16
    },

    # Поглощение - Конверсия земель (Ф. 91-100)
    "Land Conversion": {
        "description": "Конверсия земель",
        "files": ["ui/land_conversion_tab.py"],
        "formulas": list(range(91, 101)),
        "expected_count": 10
    },

    # Дополнительные формулы (101-143)
    "Additional": {
        "description": "Дополнительные формулы",
        "files": [],  # Нужно найти где они
        "formulas": list(range(101, 144)),
        "expected_count": 43
    }
}

def find_formulas_in_file(filepath):
    """Ищет упоминания формул в файле"""
    if not os.path.exists(filepath):
        return set()

    formulas_found = set()

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

        # Поиск упоминаний формул в разных форматах
        patterns = [
            r'Ф\.\s*(\d+)',  # Ф. 123
            r'Формула\s+(\d+)',  # Формула 123
            r'f(\d+)_',  # f123_result
            r'\(Ф\.\s*(\d+)\)',  # (Ф. 123)
            r'F(\d+)',  # F123
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            formulas_found.update(int(m) for m in matches if m.isdigit())

    return formulas_found

def check_all_formulas():
    """Проверяет наличие всех формул в проекте"""
    print("=" * 80)
    print("ПРОВЕРКА НАЛИЧИЯ ФОРМУЛ В ИНТЕРФЕЙСЕ")
    print("=" * 80)
    print()

    total_expected = 0
    total_found = 0
    all_found_formulas = set()

    for section_name, section_info in FORMULA_RANGES.items():
        print(f"\n{'='*60}")
        print(f"Раздел: {section_name}")
        print(f"Описание: {section_info['description']}")
        print(f"Ожидается формул: {section_info['expected_count']}")
        print(f"{'='*60}")

        section_formulas = set()

        for filepath in section_info['files']:
            if os.path.exists(filepath):
                found = find_formulas_in_file(filepath)
                section_formulas.update(found)
                print(f"  ✓ {filepath}: найдено {len(found)} формул")
            else:
                print(f"  ✗ {filepath}: ФАЙЛ НЕ НАЙДЕН")

        # Проверка ожидаемых формул
        if 'formulas' in section_info:
            expected = set(section_info['formulas'])
            missing = expected - section_formulas
            extra = section_formulas - expected

            if missing:
                print(f"\n  ⚠ ОТСУТСТВУЮТ формулы: {sorted(missing)}")
            if extra:
                print(f"  ℹ Дополнительные формулы: {sorted(extra)}")

            if not missing:
                print(f"  ✓ Все ожидаемые формулы присутствуют!")

        print(f"\n  Итого в разделе: {len(section_formulas)} формул")
        all_found_formulas.update(section_formulas)

        if isinstance(section_info['expected_count'], int):
            total_expected += section_info['expected_count']

    # Итоговая статистика
    print(f"\n\n{'='*80}")
    print("ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*80}")
    print(f"Всего найдено уникальных формул: {len(all_found_formulas)}")
    print(f"Диапазон формул: {min(all_found_formulas) if all_found_formulas else 0} - {max(all_found_formulas) if all_found_formulas else 0}")

    # Проверка на пропущенные формулы в диапазоне 1-143
    all_expected = set(range(1, 144))
    missing_global = all_expected - all_found_formulas

    if missing_global:
        print(f"\n⚠ ОТСУТСТВУЮТ формулы из диапазона 1-143:")
        print(f"  Всего отсутствует: {len(missing_global)}")
        print(f"  Список: {sorted(missing_global)}")
    else:
        print("\n✓ ВСЕ 143 ФОРМУЛЫ ПРИСУТСТВУЮТ В ИНТЕРФЕЙСЕ!")

    return all_found_formulas, missing_global

if __name__ == "__main__":
    found, missing = check_all_formulas()

    # Сохранение результатов
    with open('docs/formula_check_report.txt', 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ О ПРОВЕРКЕ ФОРМУЛ\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Найдено формул: {len(found)}\n")
        f.write(f"Список найденных: {sorted(found)}\n\n")
        if missing:
            f.write(f"Отсутствуют: {sorted(missing)}\n")

    print(f"\n\nОтчет сохранен в docs/formula_check_report.txt")
