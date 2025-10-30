#!/usr/bin/env python3
"""
Тест сохранения/загрузки данных для Category1Tab (Стац. сжигание).
"""
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent))

from ui.category_1_tab import Category1Tab
from calculations.calculator_factory_extended import ExtendedCalculatorFactory

def test_category1_save_load():
    """Тест сохранения и загрузки данных Category1."""
    app = QApplication(sys.argv)

    # Создаём фабрику и получаем калькулятор
    factory = ExtendedCalculatorFactory()
    calc = factory.get_calculator("Category1")
    tab = Category1Tab(calc)

    with open('category1_debug.txt', 'w', encoding='utf-8') as f:
        f.write("=== ТЕСТ CATEGORY 1 (Стац. сжигание) ===\n\n")

        # Найдем все поля ввода
        f.write("=== Шаг 1: Поиск всех полей ввода ===\n")
        input_fields = [attr for attr in dir(tab) if attr.endswith('_input') and not attr.startswith('_')]
        f.write(f"Найдено полей с суффиксом '_input': {len(input_fields)}\n")
        for field_name in input_fields[:10]:  # первые 10
            f.write(f"  - {field_name}\n")

        # Заполняем первые несколько полей
        f.write("\n=== Шаг 2: Заполнение данных ===\n")
        test_data = {}
        for i, field_name in enumerate(input_fields[:5]):
            field = getattr(tab, field_name)
            if hasattr(field, 'setText'):
                value = f"{(i+1) * 10}.5"
                field.setText(value)
                test_data[field_name] = value
                f.write(f"{field_name}: {value}\n")

        # Собираем данные через get_data()
        f.write("\n=== Шаг 3: Сбор данных через get_data() ===\n")
        saved_data = tab.get_data()
        f.write(f"Структура данных:\n")
        f.write(json.dumps(saved_data, indent=2, ensure_ascii=False)[:1000] + "...\n")

        # Проверяем, что данные сохранились
        f.write("\n=== Шаг 4: Проверка сохраненных данных ===\n")
        fields_data = saved_data.get('fields', {})
        f.write(f"Всего полей в fields: {len(fields_data)}\n")

        for field_name, expected_value in test_data.items():
            if field_name in fields_data:
                actual_value = fields_data[field_name]
                status = "✅" if actual_value == expected_value else "❌"
                f.write(f"{status} {field_name}: ожидалось '{expected_value}', получено '{actual_value}'\n")
            else:
                f.write(f"❌ {field_name}: НЕ НАЙДЕНО в saved_data\n")

        # Очищаем поля
        f.write("\n=== Шаг 5: Очистка полей ===\n")
        tab.clear_fields()
        for field_name in test_data.keys():
            field = getattr(tab, field_name)
            value = field.text() if hasattr(field, 'text') else str(field.value())
            f.write(f"{field_name} после clear: '{value}'\n")

        # Загружаем данные обратно
        f.write("\n=== Шаг 6: Загрузка данных через set_data() ===\n")
        tab.set_data(saved_data)

        all_ok = True
        for field_name, expected_value in test_data.items():
            field = getattr(tab, field_name)
            actual_value = field.text() if hasattr(field, 'text') else str(field.value())
            status = "✅" if actual_value == expected_value else "❌"
            if actual_value != expected_value:
                all_ok = False
            f.write(f"{status} {field_name}: ожидалось '{expected_value}', получено '{actual_value}'\n")

        # Итоговый результат
        f.write("\n=== ИТОГОВЫЙ РЕЗУЛЬТАТ ===\n")
        if all_ok:
            f.write("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ: Данные сохраняются и загружаются корректно!\n")
        else:
            f.write("❌ ТЕСТЫ НЕ ПРОЙДЕНЫ: Некоторые данные не загружаются!\n")

    print("Результаты записаны в category1_debug.txt")
    app.quit()

if __name__ == '__main__':
    test_category1_save_load()
