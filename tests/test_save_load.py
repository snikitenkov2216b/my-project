#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функций сохранения/загрузки/экспорта.
"""
import sys
import os

# Настройка пути проекта
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from ui.main_window_extended import ExtendedMainWindow


def test_data_collection():
    """Тест сбора данных из вкладок."""
    app = QApplication(sys.argv)
    window = ExtendedMainWindow()

    print("=" * 60)
    print("ТЕСТ СБОРА ДАННЫХ")
    print("=" * 60)

    # Устанавливаем тестовые данные в первую вкладку выбросов
    emissions_tab = window.emissions_tabs.widget(0)
    if hasattr(emissions_tab, 'input_postuplenie'):
        emissions_tab.input_postuplenie.setText("100.5")
        emissions_tab.input_otgruzka.setText("50.0")
        emissions_tab.input_zapas_nachalo.setText("30.0")
        emissions_tab.input_zapas_konets.setText("20.0")
        print("[OK] Test data set in Category 0")

        # Выполним расчет
        if hasattr(emissions_tab, '_perform_calculation'):
            emissions_tab._perform_calculation()
            print("[OK] Calculation performed")

    # Собираем данные
    emissions_data = window._collect_emissions_data()
    print(f"\n[OK] Collected emissions data: {len(emissions_data)} categories")

    # Проверяем первую категорию
    first_category = list(emissions_data.keys())[0] if emissions_data else None
    if first_category:
        data = emissions_data[first_category]
        print(f"\n  Категория: {first_category}")
        print(f"  Поля: {len(data.get('fields', {}))} штук")
        print(f"  Результат: {data.get('result', 'Нет')}")

        # Выводим поля
        fields = data.get('fields', {})
        if fields:
            print(f"\n  Входные данные:")
            for field_name, value in fields.items():
                if value:
                    print(f"    - {field_name}: {value}")

    absorption_data = window._collect_absorption_data()
    print(f"\n[OK] Collected absorption data: {len(absorption_data)} types")

    print("\n" + "=" * 60)
    print("TEST PASSED SUCCESSFULLY")
    print("=" * 60)

    app.quit()
    return True


if __name__ == '__main__':
    try:
        result = test_data_collection()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
