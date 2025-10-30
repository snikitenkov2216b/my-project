"""
Скрипт для тестирования работоспособности расчетов
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

def test_forest_restoration():
    """Тест расчетов лесовосстановления"""
    from calculations.absorption_forest_restoration import ForestRestorationCalculator

    calc = ForestRestorationCalculator()

    # Тест Ф.1 - Суммарное изменение запасов углерода
    result_f1 = calc.calculate_carbon_stock_change(
        biomass_change=100,     # т C/год
        deadwood_change=10,     # т C/год
        litter_change=5,        # т C/год
        soil_change=20          # т C/год
    )
    expected_f1 = 100 + 10 + 5 + 20
    print(f"Ф.1 Изменение запасов C: {result_f1:.4f} т C/год (ожидается {expected_f1:.4f})")
    assert abs(result_f1 - expected_f1) < 0.01, "Ф.1 расчет некорректен!"

    # Тест Ф.2 - Изменение биомассы
    result_f2 = calc.calculate_biomass_change(
        carbon_after=50,    # т C/га
        carbon_before=30,   # т C/га
        area=100,           # га
        period_years=10     # лет
    )
    expected_f2 = (50 - 30) * 100 / 10
    print(f"Ф.2 Изменение биомассы: {result_f2:.4f} т C/год (ожидается {expected_f2:.4f})")
    assert abs(result_f2 - expected_f2) < 0.01, "Ф.2 расчет некорректен!"

    # Тест Ф.11 - Конверсия углерода в CO2
    result_f11 = calc.carbon_to_co2_conversion(100)  # 100 т C
    expected_f11 = 100 * (44/12)
    print(f"Ф.11 C->CO2: {result_f11:.4f} т CO2 (ожидается {expected_f11:.4f})")
    assert abs(result_f11 - expected_f11) < 0.01, "Ф.11 расчет некорректен!"

    return True

def test_permanent_forest():
    """Тест расчетов постоянных лесов"""
    from calculations.absorption_permanent_forest import PermanentForestCalculator

    calc = PermanentForestCalculator()

    # Тест Ф.27 - Общее изменение запасов углерода
    result_f27 = calc.calculate_total_carbon_stock_change(
        biomass_change=100,     # т C/год
        deadwood_change=10,     # т C/год
        litter_change=5,        # т C/год
        soil_change=20          # т C/год
    )
    expected_f27 = 100 + 10 + 5 + 20
    print(f"Ф.27 Общее изменение C: {result_f27:.4f} т C/год (ожидается {expected_f27:.4f})")
    assert abs(result_f27 - expected_f27) < 0.01, "Ф.27 расчет некорректен!"

    # Тест Ф.28 - Изменение запасов углерода в биомассе
    result_f28 = calc.calculate_carbon_stock_change_biomass(
        carbon_after=1000,  # т C
        carbon_before=800,  # т C
        area=10,            # га
        period_years=5      # лет
    )
    expected_f28 = (1000 - 800) / 10 / 5
    print(f"Ф.28 Изменение запасов C: {result_f28:.4f} т C/га/год (ожидается {expected_f28:.4f})")
    assert abs(result_f28 - expected_f28) < 0.01, "Ф.28 расчет некорректен!"

    return True

def test_land_conversion():
    """Тест расчетов конверсии земель"""
    from calculations.land_conversion import LandConversionCalculator

    calc = LandConversionCalculator()

    # Тест Ф.91 - Изменение запасов углерода при конверсии
    result_f91 = calc.calculate_carbon_stock_change_conversion(
        c_after_sum=500,   # т C
        c_before_sum=800,  # т C
        area=20,           # га
        period=10          # лет
    )
    expected_f91 = (500 - 800) / 20 / 10
    print(f"Ф.91 Изменение C конверсия: {result_f91:.4f} т C/га/год (ожидается {expected_f91:.4f})")
    assert abs(result_f91 - expected_f91) < 0.01, "Ф.91 расчет некорректен!"

    # Тест Ф.96 - Изменение запасов углерода в минеральных почвах
    result_f96 = calc.calculate_mineral_soil_carbon_change(
        c_fert=10,    # т C/год
        c_plant=100,  # т C/год
        c_manure=20,  # т C/год
        c_resp=30,    # т C/год
        c_erosion=15, # т C/год
        c_hay=25      # т C/год
    )
    expected_f96 = 10 + 100 + 20 - 30 - 15 - 25
    print(f"Ф.96 Изменение C минер.почв: {result_f96:.4f} т C/год (ожидается {expected_f96:.4f})")
    assert abs(result_f96 - expected_f96) < 0.01, "Ф.96 расчет некорректен!"

    return True

def test_gwp_conversion():
    """Тест конверсии в CO2-эквивалент"""
    from calculations.forest_restoration import ForestRestorationCalculator

    calc = ForestRestorationCalculator()

    # Тест конверсии CH4
    result_ch4 = calc.ghg_to_co2_equivalent(10, "CH4")  # 10 т CH4
    expected_ch4 = 10 * 28  # GWP для CH4 = 28
    print(f"Конверсия CH4: {result_ch4:.4f} т CO2-экв (ожидается {expected_ch4:.4f})")
    assert abs(result_ch4 - expected_ch4) < 0.01, "Конверсия CH4 некорректна!"

    # Тест конверсии N2O
    result_n2o = calc.ghg_to_co2_equivalent(5, "N2O")  # 5 т N2O
    expected_n2o = 5 * 265  # GWP для N2O = 265
    print(f"Конверсия N2O: {result_n2o:.4f} т CO2-экв (ожидается {expected_n2o:.4f})")
    assert abs(result_n2o - expected_n2o) < 0.01, "Конверсия N2O некорректна!"

    return True

def main():
    print("="*80)
    print("ТЕСТИРОВАНИЕ РАБОТОСПОСОБНОСТИ РАСЧЕТОВ")
    print("="*80)
    print()

    tests = [
        ("Лесовосстановление", test_forest_restoration),
        ("Постоянные леса", test_permanent_forest),
        ("Конверсия земель", test_land_conversion),
        ("Конверсия GWP", test_gwp_conversion),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n--- Тест: {test_name} ---")
        try:
            result = test_func()
            if result:
                print(f"✓ {test_name}: PASSED")
                passed += 1
            else:
                print(f"✗ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"✗ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("="*80)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
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
