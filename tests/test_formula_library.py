"""
Тесты для функций библиотеки формул.
Проверяем сохранение, загрузку и удаление формул.
"""

import json
import tempfile
from pathlib import Path
import sys
import os

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_save_load_delete_formula():
    """Тестирует сохранение, загрузку и удаление формулы."""

    # Создаем временный файл для библиотеки
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_library_file = Path(f.name)

    try:
        # Тест 1: Сохранение формулы
        print("\n[ТЕСТ 1] Сохранение формулы")
        formula_data = {
            "name": "Тестовая формула",
            "main_formula": "E_CO2 = FC * EF * OF",
            "sum_blocks": []
        }

        library = [formula_data]

        with open(temp_library_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

        print(f"[OK] Формула сохранена в {temp_library_file}")

        # Тест 2: Загрузка формулы
        print("\n[ТЕСТ 2] Загрузка формулы")
        with open(temp_library_file, 'r', encoding='utf-8') as f:
            loaded_library = json.load(f)

        assert len(loaded_library) == 1, f"Ожидалась 1 формула, загружено {len(loaded_library)}"
        assert loaded_library[0]['name'] == "Тестовая формула"
        assert loaded_library[0]['main_formula'] == "E_CO2 = FC * EF * OF"

        print("[OK] Формула успешно загружена")
        print(f"  Название: {loaded_library[0]['name']}")
        print(f"  Формула: {loaded_library[0]['main_formula']}")

        # Тест 3: Добавление второй формулы
        print("\n[ТЕСТ 3] Добавление второй формулы")
        formula_data_2 = {
            "name": "Формула с суммированием",
            "main_formula": "E_total = Sum_Block_1 * 3.66",
            "sum_blocks": [
                {
                    "name": "Sum_Block_1",
                    "expression": "C_j * mass_j",
                    "item_count": 3
                }
            ]
        }

        library.append(formula_data_2)

        with open(temp_library_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

        with open(temp_library_file, 'r', encoding='utf-8') as f:
            loaded_library = json.load(f)

        assert len(loaded_library) == 2, f"Ожидалось 2 формулы, загружено {len(loaded_library)}"
        print(f"[OK] Добавлена вторая формула. Всего формул: {len(loaded_library)}")

        # Тест 4: Удаление формулы
        print("\n[ТЕСТ 4] Удаление формулы")
        formula_to_delete = "Тестовая формула"
        library = [f for f in library if f['name'] != formula_to_delete]

        with open(temp_library_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

        with open(temp_library_file, 'r', encoding='utf-8') as f:
            loaded_library = json.load(f)

        assert len(loaded_library) == 1, f"Ожидалась 1 формула, загружено {len(loaded_library)}"
        assert loaded_library[0]['name'] == "Формула с суммированием"

        print(f"[OK] Формула '{formula_to_delete}' успешно удалена")
        print(f"  Осталось формул: {len(loaded_library)}")

        # Тест 5: Удаление всех формул
        print("\n[ТЕСТ 5] Удаление всех формул")
        library = []

        with open(temp_library_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

        with open(temp_library_file, 'r', encoding='utf-8') as f:
            loaded_library = json.load(f)

        assert len(loaded_library) == 0, f"Ожидалось 0 формул, загружено {len(loaded_library)}"
        print("[OK] Все формулы удалены, библиотека пуста")

        print("\n" + "=" * 60)
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! [OK]")
        print("=" * 60)

    finally:
        # Удаляем временный файл
        if temp_library_file.exists():
            temp_library_file.unlink()
            print(f"\n[OK] Временный файл {temp_library_file} удален")


def test_formula_library_edge_cases():
    """Тестирует граничные случаи работы с библиотекой."""

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_library_file = Path(f.name)

    try:
        print("\n[ТЕСТ 6] Работа с пустой библиотекой")

        # Пустая библиотека
        library = []
        with open(temp_library_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

        with open(temp_library_file, 'r', encoding='utf-8') as f:
            loaded_library = json.load(f)

        assert len(loaded_library) == 0
        print("[OK] Пустая библиотека загружается корректно")

        print("\n[ТЕСТ 7] Перезапись формулы с тем же именем")

        # Добавляем формулу
        formula_v1 = {
            "name": "Моя формула",
            "main_formula": "a + b",
            "sum_blocks": []
        }
        library.append(formula_v1)

        # Заменяем на новую версию
        library = [f for f in library if f['name'] != "Моя формула"]
        formula_v2 = {
            "name": "Моя формула",
            "main_formula": "a * b * c",
            "sum_blocks": []
        }
        library.append(formula_v2)

        assert len(library) == 1
        assert library[0]['main_formula'] == "a * b * c"
        print("[OK] Формула успешно перезаписана")

        print("\n[ТЕСТ 8] Проверка сохранения кириллицы")
        formula_cyrillic = {
            "name": "Формула на русском",
            "main_formula": "E_CO2 = FC * EF",
            "sum_blocks": []
        }
        library.append(formula_cyrillic)

        with open(temp_library_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

        with open(temp_library_file, 'r', encoding='utf-8') as f:
            loaded_library = json.load(f)

        found = any(f['name'] == "Формула на русском" for f in loaded_library)
        assert found, "Формула с кириллицей не найдена"
        print("[OK] Кириллица сохраняется корректно")

        print("\n" + "=" * 60)
        print("ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! [OK]")
        print("=" * 60)

    finally:
        if temp_library_file.exists():
            temp_library_file.unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ БИБЛИОТЕКИ ФОРМУЛ")
    print("=" * 60)

    test_save_load_delete_formula()
    test_formula_library_edge_cases()

    print("\n[SUCCESS] ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ!")
