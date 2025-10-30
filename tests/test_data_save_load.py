#!/usr/bin/env python3
"""
Тестовый скрипт для проверки сохранения/загрузки данных.
"""
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from ui.category_0_tab import Category0Tab
from calculations.category_0 import Category0Calculator

def test_save_load():
    """Тест сохранения и загрузки данных."""
    app = QApplication(sys.argv)

    # Создаём вкладку категории 0
    calc = Category0Calculator()
    tab = Category0Tab(calc)

    # Заполняем данные
    print("=== Заполнение данных ===")
    tab.input_postuplenie.setText("100.5")
    tab.input_otgruzka.setText("50.2")
    tab.input_zapas_nachalo.setText("10.0")
    tab.input_zapas_konets.setText("20.0")

    print(f"input_postuplenie: {tab.input_postuplenie.text()}")
    print(f"input_otgruzka: {tab.input_otgruzka.text()}")
    print(f"input_zapas_nachalo: {tab.input_zapas_nachalo.text()}")
    print(f"input_zapas_konets: {tab.input_zapas_konets.text()}")

    # Собираем данные
    print("\n=== Сбор данных через get_data() ===")
    data = tab.get_data()
    print(f"Собранные данные: {json.dumps(data, indent=2, ensure_ascii=False)}")

    # Очищаем поля
    print("\n=== Очистка полей ===")
    tab.clear_fields()
    print(f"input_postuplenie после clear: {tab.input_postuplenie.text()}")
    print(f"input_otgruzka после clear: {tab.input_otgruzka.text()}")

    # Загружаем данные обратно
    print("\n=== Загрузка данных через set_data() ===")
    tab.set_data(data)
    print(f"input_postuplenie после set_data: {tab.input_postuplenie.text()}")
    print(f"input_otgruzka после set_data: {tab.input_otgruzka.text()}")
    print(f"input_zapas_nachalo после set_data: {tab.input_zapas_nachalo.text()}")
    print(f"input_zapas_konets после set_data: {tab.input_zapas_konets.text()}")

    # Проверяем соответствие
    print("\n=== Проверка ===")
    if (tab.input_postuplenie.text() == "100.5" and
        tab.input_otgruzka.text() == "50.2" and
        tab.input_zapas_nachalo.text() == "10.0" and
        tab.input_zapas_konets.text() == "20.0"):
        print("✅ ТЕСТ ПРОЙДЕН: Все данные загружены корректно!")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН: Данные не совпадают!")

    app.quit()

if __name__ == '__main__':
    test_save_load()
