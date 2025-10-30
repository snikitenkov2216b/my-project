#!/usr/bin/env python3
"""
Проверяем имена вкладок при сохранении/загрузке.
"""
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window_extended import ExtendedMainWindow

def test_tab_names():
    """Проверка имен вкладок."""
    app = QApplication(sys.argv)

    window = ExtendedMainWindow()

    with open('tab_names_debug.txt', 'w', encoding='utf-8') as f:
        f.write("=== Имена вкладок выбросов ===\n")
        for i in range(window.emissions_tabs.count()):
            tab_name = window.emissions_tabs.tabText(i)
            f.write(f"{i}: '{tab_name}' (len={len(tab_name)})\n")
            f.write(f"    Bytes: {tab_name.encode('utf-8')}\n")

        f.write("\n=== Сбор данных ===\n")
        emissions_data = window._collect_emissions_data()
        f.write(f"Ключи в emissions_data:\n")
        for key in list(emissions_data.keys())[:5]:  # первые 5
            f.write(f"  '{key}' (len={len(key)})\n")
            f.write(f"    Bytes: {key.encode('utf-8')}\n")

        f.write(f"\nВсего категорий: {len(emissions_data)}\n")

    print("Результаты записаны в tab_names_debug.txt")
    app.quit()

if __name__ == '__main__':
    test_tab_names()
