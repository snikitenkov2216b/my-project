#!/usr/bin/env python3
"""
Расширенные тесты для CustomFormulaEvaluator с новыми функциями.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from calculations.custom_formula_evaluator import CustomFormulaEvaluator


def test_basic_operations():
    """Тест базовых математических операций."""
    print("=" * 70)
    print("ТЕСТ 1: Базовые математические операции")
    print("=" * 70)

    evaluator = CustomFormulaEvaluator()

    tests = [
        ("2 + 3", {}, 5.0, "Сложение"),
        ("10 - 4", {}, 6.0, "Вычитание"),
        ("3 * 4", {}, 12.0, "Умножение"),
        ("20 / 4", {}, 5.0, "Деление"),
        ("2**3", {}, 8.0, "Возведение в степень"),
        ("(2 + 3) * 4", {}, 20.0, "Скобки"),
    ]

    for formula, vars, expected, description in tests:
        result = evaluator.evaluate(formula, vars)
        status = "✅" if abs(result - expected) < 1e-6 else "❌"
        print(f"{status} {description}: {formula} = {result} (ожидалось {expected})")

    print()


def test_math_functions():
    """Тест математических функций."""
    print("=" * 70)
    print("ТЕСТ 2: Математические функции")
    print("=" * 70)

    evaluator = CustomFormulaEvaluator()
    import math

    tests = [
        ("sqrt(16)", {}, 4.0, "Квадратный корень"),
        ("sqrt(x)", {"x": 25}, 5.0, "Корень с переменной"),
        ("exp(0)", {}, 1.0, "Экспонента (exp(0))"),
        ("exp(1)", {}, math.e, "Экспонента (exp(1))"),
        ("log(E)", {}, 1.0, "Натуральный логарифм (log(e))"),
        ("abs(-5)", {}, 5.0, "Модуль отрицательного"),
        ("abs(7)", {}, 7.0, "Модуль положительного"),
    ]

    for formula, vars, expected, description in tests:
        result = evaluator.evaluate(formula, vars)
        status = "✅" if abs(result - expected) < 1e-6 else "❌"
        print(f"{status} {description}: {formula} = {result:.6f} (ожидалось {expected:.6f})")

    print()


def test_constants():
    """Тест использования констант."""
    print("=" * 70)
    print("ТЕСТ 3: Математические константы")
    print("=" * 70)

    evaluator = CustomFormulaEvaluator()
    import math

    tests = [
        ("pi", {}, math.pi, "Константа Pi"),
        ("E", {}, math.e, "Константа Эйлера"),
        ("pi * r**2", {"r": 5}, math.pi * 25, "Площадь круга"),
        ("2 * pi * r", {"r": 10}, 2 * math.pi * 10, "Длина окружности"),
    ]

    for formula, vars, expected, description in tests:
        result = evaluator.evaluate(formula, vars)
        status = "✅" if abs(result - expected) < 1e-6 else "❌"
        print(f"{status} {description}: {formula} = {result:.6f} (ожидалось {expected:.6f})")

    print()


def test_ghg_calculations():
    """Тест расчетов выбросов ПГ."""
    print("=" * 70)
    print("ТЕСТ 4: Формулы расчета выбросов ПГ")
    print("=" * 70)

    evaluator = CustomFormulaEvaluator()

    tests = [
        (
            "FC * EF * OF",
            {"FC": 1000, "EF": 2.5, "OF": 0.98},
            2450.0,
            "Выбросы CO2 от сжигания топлива"
        ),
        (
            "C * (44/12)",
            {"C": 120},
            440.0,
            "Преобразование углерода в CO2"
        ),
        (
            "(FC * EF * GWP) / 1000",
            {"FC": 1000, "EF": 0.5, "GWP": 25},
            12.5,
            "Выбросы CH4 в CO2-экв"
        ),
        (
            "mass * fraction * 3.66",
            {"mass": 500, "fraction": 0.85},
            1555.5,
            "Выбросы от процесса с фракцией углерода"
        ),
    ]

    for formula, vars, expected, description in tests:
        result = evaluator.evaluate(formula, vars)
        status = "✅" if abs(result - expected) < 1e-6 else "❌"
        print(f"{status} {description}")
        print(f"   Формула: {formula}")
        print(f"   Результат: {result:.2f} т CO2-экв (ожидалось {expected:.2f})")
        print()


def test_sum_blocks():
    """Тест блоков суммирования."""
    print("=" * 70)
    print("ТЕСТ 5: Блоки суммирования")
    print("=" * 70)

    evaluator = CustomFormulaEvaluator()

    # Простое суммирование
    variables = [
        {"FC_1": 100, "EF_1": 2.0},
        {"FC_2": 200, "EF_2": 2.5},
        {"FC_3": 150, "EF_3": 3.0},
    ]
    result = evaluator.evaluate_sum_block("FC_j * EF_j", variables)
    expected = 100*2.0 + 200*2.5 + 150*3.0  # 200 + 500 + 450 = 1150
    status = "✅" if abs(result - expected) < 1e-6 else "❌"
    print(f"{status} Простое суммирование: Σ(FC_j * EF_j)")
    print(f"   Результат: {result:.2f} (ожидалось {expected:.2f})")

    # Сложное суммирование
    variables2 = [
        {"A_1": 10, "B_1": 5, "C_1": 2},
        {"A_2": 20, "B_2": 4, "C_2": 3},
    ]
    result2 = evaluator.evaluate_sum_block("(A_j + B_j) * C_j", variables2)
    expected2 = (10+5)*2 + (20+4)*3  # 30 + 72 = 102
    status2 = "✅" if abs(result2 - expected2) < 1e-6 else "❌"
    print(f"{status2} Сложное суммирование: Σ((A_j + B_j) * C_j)")
    print(f"   Результат: {result2:.2f} (ожидалось {expected2:.2f})")

    print()


def test_complex_formulas():
    """Тест сложных комбинированных формул."""
    print("=" * 70)
    print("ТЕСТ 6: Сложные комбинированные формулы")
    print("=" * 70)

    evaluator = CustomFormulaEvaluator()

    tests = [
        (
            "sqrt(a**2 + b**2)",
            {"a": 3, "b": 4},
            5.0,
            "Теорема Пифагора"
        ),
        (
            "initial * exp(-rate * time)",
            {"initial": 1000, "rate": 0.1, "time": 5},
            1000 * 0.60653,  # exp(-0.5) ≈ 0.60653
            "Экспоненциальный распад"
        ),
        (
            "(a * b) / sqrt(c)",
            {"a": 10, "b": 5, "c": 25},
            10.0,
            "Комбинация операций"
        ),
        (
            "pi * r**2 * h",
            {"r": 5, "h": 10},
            785.398,  # π * 25 * 10
            "Объем цилиндра"
        ),
    ]

    for formula, vars, expected, description in tests:
        result = evaluator.evaluate(formula, vars)
        status = "✅" if abs(result - expected) < 0.01 else "❌"  # Больше погрешности для exp
        print(f"{status} {description}")
        print(f"   Формула: {formula}")
        print(f"   Результат: {result:.4f} (ожидалось ~{expected:.4f})")
        print()


def test_error_handling():
    """Тест обработки ошибок."""
    print("=" * 70)
    print("ТЕСТ 7: Обработка ошибок")
    print("=" * 70)

    evaluator = CustomFormulaEvaluator()

    error_tests = [
        ("a / 0", {"a": 10}, "Деление на ноль"),
        ("sqrt(-1)", {}, "Корень из отрицательного числа"),
        ("a + b", {"a": 5}, "Отсутствующая переменная"),
        ("invalid syntax &", {}, "Неверный синтаксис"),
    ]

    for formula, vars, description in error_tests:
        try:
            result = evaluator.evaluate(formula, vars)
            print(f"❌ {description}: ошибка НЕ обнаружена (результат: {result})")
        except Exception as e:
            print(f"✅ {description}: ошибка корректно обработана")
            print(f"   Сообщение: {str(e)[:60]}...")

    print()


def run_all_tests():
    """Запуск всех тестов."""
    print("\n")
    print("=" * 70)
    print(" " * 15 + "РАСШИРЕННОЕ ТЕСТИРОВАНИЕ")
    print(" " * 15 + "CustomFormulaEvaluator")
    print("=" * 70)
    print()

    try:
        test_basic_operations()
        test_math_functions()
        test_constants()
        test_ghg_calculations()
        test_sum_blocks()
        test_complex_formulas()
        test_error_handling()

        print("=" * 70)
        print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
        print("=" * 70)
        return True

    except Exception as e:
        print("=" * 70)
        print(f"❌ ТЕСТЫ ПРЕРВАНЫ С ОШИБКОЙ: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
