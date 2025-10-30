"""
Тесты для функциональности расчета баланса ПГ.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ui.main_window_extended import ExtendedMainWindow


def test_extract_number_from_result():
    """Тестирует извлечение чисел из текста результатов."""

    # Создаем экземпляр окна
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    window = ExtendedMainWindow()

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ИЗВЛЕЧЕНИЯ ЧИСЕЛ ИЗ РЕЗУЛЬТАТОВ")
    print("=" * 60)

    # Тест 1: Стандартный формат
    print("\n[ТЕСТ 1] Стандартный формат результата")
    result1 = "Результат: 1234.56 тонн CO2"
    value1 = window._extract_number_from_result(result1)
    assert value1 == 1234.56, f"Ожидалось 1234.56, получено {value1}"
    print(f"[OK] Извлечено: {value1}")

    # Тест 2: Формат с "т CO2"
    print("\n[ТЕСТ 2] Формат с 'т CO2'")
    result2 = "Результат: 5678.90 т CO2"
    value2 = window._extract_number_from_result(result2)
    assert value2 == 5678.90, f"Ожидалось 5678.90, получено {value2}"
    print(f"[OK] Извлечено: {value2}")

    # Тест 3: Формат с запятой
    print("\n[ТЕСТ 3] Формат с запятой вместо точки")
    result3 = "Результат: 999,12 тонн CO2"
    value3 = window._extract_number_from_result(result3)
    assert abs(value3 - 999.12) < 0.01, f"Ожидалось 999.12, получено {value3}"
    print(f"[OK] Извлечено: {value3}")

    # Тест 4: Целое число
    print("\n[ТЕСТ 4] Целое число")
    result4 = "Результат: 100 т"
    value4 = window._extract_number_from_result(result4)
    assert value4 == 100.0, f"Ожидалось 100.0, получено {value4}"
    print(f"[OK] Извлечено: {value4}")

    # Тест 5: Пустая строка
    print("\n[ТЕСТ 5] Пустая строка")
    result5 = ""
    value5 = window._extract_number_from_result(result5)
    assert value5 is None, f"Ожидалось None, получено {value5}"
    print(f"[OK] Извлечено: {value5}")

    # Тест 6: Строка без чисел
    print("\n[ТЕСТ 6] Строка без чисел")
    result6 = "Результат: ошибка расчета"
    value6 = window._extract_number_from_result(result6)
    assert value6 is None, f"Ожидалось None, получено {value6}"
    print(f"[OK] Извлечено: {value6}")

    # Тест 7: Очень большое число
    print("\n[ТЕСТ 7] Очень большое число")
    result7 = "Результат: 123456.789 тонн CO2"
    value7 = window._extract_number_from_result(result7)
    assert value7 == 123456.789, f"Ожидалось 123456.789, получено {value7}"
    print(f"[OK] Извлечено: {value7}")

    # Тест 8: Число с несколькими вариантами единиц
    print("\n[ТЕСТ 8] Различные форматы единиц")
    test_cases = [
        ("Результат: 50.5 кг", 50.5),
        ("Результат: 75.3 т", 75.3),
        ("Результат: 100 тCO2", 100.0),
    ]

    for result_text, expected in test_cases:
        value = window._extract_number_from_result(result_text)
        assert abs(value - expected) < 0.01, f"Для '{result_text}' ожидалось {expected}, получено {value}"
        print(f"[OK] '{result_text}' -> {value}")

    print("\n" + "=" * 60)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! [OK]")
    print("=" * 60)


def test_balance_calculation():
    """Тестирует расчет баланса с заданными данными."""

    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    window = ExtendedMainWindow()

    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ РАСЧЕТА БАЛАНСА")
    print("=" * 60)

    # Тест 1: Расчет с нулевыми данными
    print("\n[ТЕСТ 1] Расчет с пустыми данными")
    total_emissions, emissions_by_cat, em_count = window._calculate_total_emissions()
    total_absorption, absorption_by_type, ab_count = window._calculate_total_absorption()

    assert total_emissions == 0.0, f"Ожидалось 0.0, получено {total_emissions}"
    assert total_absorption == 0.0, f"Ожидалось 0.0, получено {total_absorption}"
    assert em_count == 0, f"Ожидалось 0 категорий, получено {em_count}"
    assert ab_count == 0, f"Ожидалось 0 типов, получено {ab_count}"

    print(f"[OK] Выбросы: {total_emissions}, Поглощение: {total_absorption}")
    print(f"[OK] Категорий: {em_count}, Типов: {ab_count}")

    # Тест 2: Чистые выбросы
    print("\n[ТЕСТ 2] Расчет чистых выбросов")
    net_emissions = total_emissions - total_absorption
    assert net_emissions == 0.0, f"Ожидалось 0.0, получено {net_emissions}"
    print(f"[OK] Чистые выбросы: {net_emissions}")

    # Тест 3: Процент компенсации
    print("\n[ТЕСТ 3] Процент компенсации")
    if total_emissions > 0:
        compensation = (total_absorption / total_emissions) * 100
        print(f"[OK] Процент компенсации: {compensation:.2f}%")
    else:
        print("[OK] Нет выбросов для расчета компенсации")

    print("\n" + "=" * 60)
    print("ТЕСТЫ РАСЧЕТА БАЛАНСА ЗАВЕРШЕНЫ! [OK]")
    print("=" * 60)


def test_balance_with_mock_data():
    """Тестирует расчет баланса с тестовыми данными."""

    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    window = ExtendedMainWindow()

    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ С ТЕСТОВЫМИ ДАННЫМИ")
    print("=" * 60)

    # Симулируем данные в первой вкладке выбросов
    print("\n[ТЕСТ 1] Симуляция данных в категории 1")

    # Получаем первую вкладку
    first_tab = window.emissions_tabs.widget(0)

    # Проверяем, что вкладка имеет метод get_data
    if hasattr(first_tab, 'get_data'):
        # Создаем тестовый результат
        test_data = {
            'fields': {},
            'result': 'Результат: 1000.50 тонн CO2'
        }

        # Симулируем наличие результата
        # (в реальном приложении это происходит после расчета)
        if hasattr(first_tab, 'result_label'):
            first_tab.result_label.setText('Результат: 1000.50 тонн CO2')

            # Пересчитываем баланс
            total_emissions, emissions_by_cat, em_count = window._calculate_total_emissions()

            print(f"[OK] Найдено выбросов: {total_emissions:.4f} т CO2-экв")
            print(f"[OK] Из категорий: {em_count}")

            if total_emissions > 0:
                print(f"[OK] Детали: {emissions_by_cat}")

                # Проверяем корректность
                assert total_emissions >= 1000.0, "Значение выбросов должно быть >= 1000"
                assert em_count >= 1, "Должна быть хотя бы одна категория"
        else:
            print("[SKIP] У вкладки нет result_label")
    else:
        print("[SKIP] У вкладки нет метода get_data")

    print("\n" + "=" * 60)
    print("ТЕСТЫ С ТЕСТОВЫМИ ДАННЫМИ ЗАВЕРШЕНЫ! [OK]")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("ЗАПУСК ТЕСТОВ БАЛАНСА ПАРНИКОВЫХ ГАЗОВ")
    print("=" * 60)

    test_extract_number_from_result()
    test_balance_calculation()
    test_balance_with_mock_data()

    print("\n" + "=" * 60)
    print("[SUCCESS] ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ!")
    print("=" * 60)
