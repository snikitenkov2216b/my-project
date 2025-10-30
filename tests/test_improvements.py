#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшений.
"""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from ui.main_window_extended import ExtendedMainWindow


def test_improvements():
    """Тест улучшений сохранения и отображения."""
    app = QApplication(sys.argv)
    window = ExtendedMainWindow()

    print("=" * 60)
    print("TEST: Data Collection and Display")
    print("=" * 60)

    # Тест 1: Категория 0 (выбросы)
    print("\n[TEST 1] Category 0 Tab")
    emissions_tab = window.emissions_tabs.widget(0)
    if hasattr(emissions_tab, 'input_postuplenie'):
        emissions_tab.input_postuplenie.setText("100.5")
        emissions_tab.input_otgruzka.setText("50.0")
        emissions_tab.input_zapas_nachalo.setText("30.0")
        emissions_tab.input_zapas_konets.setText("20.0")
        print("  - Test data set")

        # Выполним расчет
        if hasattr(emissions_tab, '_perform_calculation'):
            emissions_tab._perform_calculation()
            print("  - Calculation performed")

    # Собираем данные
    emissions_data = window._collect_emissions_data()
    first_cat = list(emissions_data.keys())[0] if emissions_data else None
    if first_cat:
        data = emissions_data[first_cat]
        fields = data.get('fields', {})
        print(f"  - Collected {len(fields)} fields")
        print(f"  - Has result: {'Yes' if data.get('result') else 'No'}")

        # Выводим некоторые поля
        field_count = 0
        for field_name, value in fields.items():
            if value:
                print(f"    * {field_name}: {value}")
                field_count += 1
                if field_count >= 3:
                    break

    # Тест 2: Вкладки поглощения
    print("\n[TEST 2] Absorption Tabs")
    absorption_tab = window.absorption_tabs.widget(0)
    if absorption_tab:
        print(f"  - Tab class: {absorption_tab.__class__.__name__}")
        print(f"  - Has get_data: {hasattr(absorption_tab, 'get_data')}")
        print(f"  - Has set_data: {hasattr(absorption_tab, 'set_data')}")
        print(f"  - Has _append_result: {hasattr(absorption_tab, '_append_result')}")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

    app.quit()
    return True


if __name__ == '__main__':
    try:
        result = test_improvements()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
