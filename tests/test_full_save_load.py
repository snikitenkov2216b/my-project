#!/usr/bin/env python3
"""
Полный тест сохранения и загрузки проекта.
"""
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window_extended import ExtendedMainWindow

def test_full_save_load():
    """Тест полного цикла сохранения/загрузки."""
    app = QApplication(sys.argv)

    window = ExtendedMainWindow()

    with open('save_load_debug.txt', 'w', encoding='utf-8') as f:
        # Заполняем первую вкладку выбросов (Категория 0)
        f.write("=== Шаг 1: Заполнение данных в Категории 0 ===\n")
        tab0 = window.emissions_tabs.widget(0)
        tab0.input_postuplenie.setText("100.5")
        tab0.input_otgruzka.setText("50.2")
        tab0.input_zapas_nachalo.setText("10.0")
        tab0.input_zapas_konets.setText("20.0")

        # Выполняем расчет
        tab0._perform_calculation()

        f.write(f"postuplenie: {tab0.input_postuplenie.text()}\n")
        f.write(f"otgruzka: {tab0.input_otgruzka.text()}\n")
        f.write(f"zapas_nachalo: {tab0.input_zapas_nachalo.text()}\n")
        f.write(f"zapas_konets: {tab0.input_zapas_konets.text()}\n")
        f.write(f"result: {tab0.result_label.text()[:50]}...\n")

        # Сохраняем проект
        f.write("\n=== Шаг 2: Сбор данных (эмуляция сохранения) ===\n")
        emissions_data = window._collect_emissions_data()

        tab_name = window.emissions_tabs.tabText(0)
        f.write(f"Имя вкладки: '{tab_name}'\n")
        f.write(f"Ключ существует: {tab_name in emissions_data}\n")

        if tab_name in emissions_data:
            data = emissions_data[tab_name]
            f.write(f"Данные для '{tab_name}':\n")
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
            f.write("\n")

        # Эмулируем загрузку: очищаем поля
        f.write("\n=== Шаг 3: Очистка полей (эмуляция _clear_all_fields) ===\n")
        tab0.clear_fields()
        f.write(f"postuplenie после clear: '{tab0.input_postuplenie.text()}'\n")
        f.write(f"otgruzka после clear: '{tab0.input_otgruzka.text()}'\n")
        f.write(f"result после clear: '{tab0.result_label.text()[:50]}'\n")

        # Эмулируем загрузку: восстанавливаем данные
        f.write("\n=== Шаг 4: Загрузка данных (эмуляция _load_emissions_data) ===\n")
        if tab_name in emissions_data:
            f.write(f"Вызываем tab.set_data() для '{tab_name}'\n")
            tab0.set_data(emissions_data[tab_name])

            f.write(f"postuplenie после set_data: '{tab0.input_postuplenie.text()}'\n")
            f.write(f"otgruzka после set_data: '{tab0.input_otgruzka.text()}'\n")
            f.write(f"zapas_nachalo после set_data: '{tab0.input_zapas_nachalo.text()}'\n")
            f.write(f"zapas_konets после set_data: '{tab0.input_zapas_konets.text()}'\n")
            f.write(f"result после set_data: '{tab0.result_label.text()[:50]}'\n")

        # Проверка
        f.write("\n=== Шаг 5: Проверка ===\n")
        if (tab0.input_postuplenie.text() == "100.5" and
            tab0.input_otgruzka.text() == "50.2" and
            tab0.input_zapas_nachalo.text() == "10.0" and
            tab0.input_zapas_konets.text() == "20.0"):
            f.write("✅ ВХОДНЫЕ ДАННЫЕ: ОК\n")
        else:
            f.write("❌ ВХОДНЫЕ ДАННЫЕ: ОШИБКА\n")
            f.write(f"   postuplenie: ожидалось '100.5', получено '{tab0.input_postuplenie.text()}'\n")
            f.write(f"   otgruzka: ожидалось '50.2', получено '{tab0.input_otgruzka.text()}'\n")

        result_text = tab0.result_label.text()
        if result_text and result_text != "Результат появится здесь после расчета":
            f.write("✅ РЕЗУЛЬТАТЫ: ОК (сохранены)\n")
        else:
            f.write("❌ РЕЗУЛЬТАТЫ: ОШИБКА (не сохранены)\n")

    print("Результаты записаны в save_load_debug.txt")
    app.quit()

if __name__ == '__main__':
    test_full_save_load()
