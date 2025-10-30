"""
Простая проверка работоспособности расчетов
"""
import sys
from pathlib import Path

# Установка кодировки UTF-8 для вывода
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Проверка что все модули импортируются"""
    print("Проверка импорта модулей...")

    try:
        from calculations.absorption_forest_restoration import ForestRestorationCalculator
        print("  ✓ ForestRestorationCalculator")
    except Exception as e:
        print(f"  ✗ ForestRestorationCalculator: {e}")
        return False

    try:
        from calculations.absorption_permanent_forest import PermanentForestCalculator
        print("  ✓ PermanentForestCalculator")
    except Exception as e:
        print(f"  ✗ PermanentForestCalculator: {e}")
        return False

    try:
        from calculations.absorption_agricultural import AgriculturalAbsorptionCalculator
        print("  ✓ AgriculturalAbsorptionCalculator")
    except Exception as e:
        print(f"  ✗ AgriculturalAbsorptionCalculator: {e}")
        return False

    try:
        from calculations.custom_formula_evaluator import CustomFormulaEvaluator
        print("  ✓ CustomFormulaEvaluator")
    except Exception as e:
        print(f"  ✗ CustomFormulaEvaluator: {e}")
        return False

    return True

def test_basic_calculations():
    """Тест базовых расчетов"""
    print("\nТестирование базовых расчетов...")

    from calculations.absorption_forest_restoration import ForestRestorationCalculator

    calc = ForestRestorationCalculator()

    # Тест Ф.1
    result = calc.calculate_carbon_stock_change(100, 10, 5, 20)
    expected = 135.0
    if abs(result - expected) < 0.01:
        print(f"  ✓ Ф.1 Изменение запасов C: {result:.2f} т C/год")
    else:
        print(f"  ✗ Ф.1: получено {result}, ожидалось {expected}")
        return False

    # Тест Ф.2
    result = calc.calculate_biomass_change(50, 30, 100, 10)
    expected = 200.0
    if abs(result - expected) < 0.01:
        print(f"  ✓ Ф.2 Изменение биомассы: {result:.2f} т C/год")
    else:
        print(f"  ✗ Ф.2: получено {result}, ожидалось {expected}")
        return False

    # Тест Ф.11
    result = calc.carbon_to_co2_conversion(100)
    expected = 100 * (44/12)
    if abs(result - expected) < 0.01:
        print(f"  ✓ Ф.11 C->CO2: {result:.2f} т CO2")
    else:
        print(f"  ✗ Ф.11: получено {result}, ожидалось {expected}")
        return False

    # Тест Ф.12 (GWP конверсия)
    result = calc.ghg_to_co2_equivalent(10, "CH4")
    expected = 10 * 28  # GWP CH4 = 28
    if abs(result - expected) < 0.01:
        print(f"  ✓ Ф.12 CH4->CO2-экв: {result:.2f} т CO2-экв")
    else:
        print(f"  ✗ Ф.12: получено {result}, ожидалось {expected}")
        return False

    return True

def test_custom_formulas():
    """Тест пользовательских формул"""
    print("\nТестирование пользовательских формул...")

    from calculations.custom_formula_evaluator import CustomFormulaEvaluator

    evaluator = CustomFormulaEvaluator()

    # Простая формула
    formula = "E = FC * EF"
    variables = {"FC": 100, "EF": 1.5}

    try:
        result = evaluator.evaluate(formula, variables)
        expected = 150.0
        if abs(result - expected) < 0.01:
            print(f"  ✓ Простая формула: {result:.2f}")
        else:
            print(f"  ✗ Результат {result} != {expected}")
            return False
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return False

    # Формула с математическими функциями
    formula = "E = sqrt(A) * 10"
    variables = {"A": 25}

    try:
        result = evaluator.evaluate(formula, variables)
        expected = 50.0
        if abs(result - expected) < 0.01:
            print(f"  ✓ Формула с sqrt: {result:.2f}")
        else:
            print(f"  ✗ Результат {result} != {expected}")
            return False
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return False

    return True

def main():
    print("="*80)
    print("ТЕСТИРОВАНИЕ РАБОТОСПОСОБНОСТИ РАСЧЕТОВ")
    print("="*80)
    print()

    tests = [
        ("Импорт модулей", test_imports),
        ("Базовые расчеты", test_basic_calculations),
        ("Пользовательские формулы", test_custom_formulas),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"Тест: {test_name}")
        print(f"{'='*80}")
        try:
            if test_func():
                print(f"\n✓ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n✗ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"\n✗ {test_name}: ERROR")
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("="*80)
    print("ИТОГИ")
    print("="*80)
    print(f"Успешно: {passed}/{len(tests)}")
    print(f"Провалено: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ Все расчеты работают корректно!")
        return 0
    else:
        print(f"\n✗ Обнаружены проблемы в {failed} тестах")
        return 1

if __name__ == "__main__":
    sys.exit(main())
