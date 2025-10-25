# tests/test_formulas_basic.py
"""
Модульные тесты для проверки корректности формул в калькуляторах категорий.
Тестируют математическую правильность расчётов и граничные случаи.
"""

import pytest
import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CARBON_TO_CO2_FACTOR, N2O_N_TO_N2O_FACTOR
from calculations.category_0 import Category0Calculator
from calculations.category_1 import Category1Calculator
from calculations.gwp_constants import get_co2_equivalent, carbon_to_co2, nitrogen_to_n2o


class TestConstants:
    """Тесты констант проекта"""

    def test_carbon_to_co2_factor_precision(self):
        """Проверка точности константы CARBON_TO_CO2_FACTOR"""
        # Точное значение с обновленной молярной массой CO2: 44.009 / 12.011 = 3.6640579...
        expected = 44.009 / 12.011
        assert abs(CARBON_TO_CO2_FACTOR - expected) < 1e-6, \
            f"CARBON_TO_CO2_FACTOR должен быть {expected}, получен {CARBON_TO_CO2_FACTOR}"

    def test_n2o_factor_precision(self):
        """Проверка точности константы N2O_N_TO_N2O_FACTOR"""
        # Точное значение: 44.013 / 28.014 = 1.5712896...
        expected = 44.013 / 28.014
        assert abs(N2O_N_TO_N2O_FACTOR - expected) < 1e-6, \
            f"N2O_N_TO_N2O_FACTOR должен быть {expected}, получен {N2O_N_TO_N2O_FACTOR}"


class TestCategory0:
    """Тесты для Category0Calculator (Расчет расхода по балансу)"""

    def test_basic_consumption(self):
        """Проверка базового расчета расхода: M_расход = M_пост - M_отгр + M_запас_нач - M_запас_кон"""
        calc = Category0Calculator()
        # Пример: поступило 1000 т, отгружено 100 т, запас в начале 200 т, в конце 150 т
        # Расход = 1000 - 100 + 200 - 150 = 950 т
        result = calc.calculate_consumption(
            поступление=1000.0,
            отгрузка=100.0,
            запас_начало=200.0,
            запас_конец=150.0
        )
        assert result == 950.0, f"Ожидалось 950.0, получено {result}"

    def test_zero_consumption(self):
        """Проверка случая с нулевым расходом"""
        calc = Category0Calculator()
        # Баланс: 100 - 0 + 0 - 100 = 0
        result = calc.calculate_consumption(
            поступление=100.0,
            отгрузка=0.0,
            запас_начало=0.0,
            запас_конец=100.0
        )
        assert result == 0.0

    def test_negative_values_raise_error(self):
        """Проверка, что отрицательные значения вызывают ошибку"""
        calc = Category0Calculator()
        with pytest.raises(ValueError, match="не могут быть отрицательными"):
            calc.calculate_consumption(
                поступление=-100.0,
                отгрузка=50.0,
                запас_начало=0.0,
                запас_конец=0.0
            )


class TestCategory1:
    """Тесты для Category1Calculator (Стационарное сжигание топлива)"""

    def test_total_emissions_formula(self):
        """
        Проверка формулы 1.1: E_CO2 = FC * EF_CO2 * OF
        Пример: 100 т топлива, EF = 2.5 т CO2/т, OF = 0.98
        Результат: 100 * 2.5 * 0.98 = 245 т CO2
        """
        from unittest.mock import Mock
        data_service = Mock()
        calc = Category1Calculator(data_service)

        result = calc.calculate_total_emissions(
            fuel_consumption=100.0,
            emission_factor=2.5,
            oxidation_factor=0.98
        )
        expected = 100.0 * 2.5 * 0.98
        assert abs(result - expected) < 1e-6, f"Ожидалось {expected}, получено {result}"

    def test_carbon_content_in_coke(self):
        """
        Проверка формулы 1.6: W_C = (100 - A - V - S) / 100
        Пример: зола 10%, летучие 5%, сера 2%
        Углерод: (100 - 10 - 5 - 2) / 100 = 0.83
        """
        from unittest.mock import Mock
        data_service = Mock()
        calc = Category1Calculator(data_service)

        result = calc.calculate_carbon_in_coke(ash=10.0, volatiles=5.0, sulfur=2.0)
        expected = 0.83
        assert abs(result - expected) < 1e-6, f"Ожидалось {expected}, получено {result}"

    def test_oxidation_factor_from_heat_loss(self):
        """
        Проверка формулы 1.8: OF = (100 - q4) / 100
        Пример: потери тепла q4 = 2%
        OF = (100 - 2) / 100 = 0.98
        """
        from unittest.mock import Mock
        data_service = Mock()
        calc = Category1Calculator(data_service)

        result = calc.calculate_of_from_heat_loss(heat_loss_q4=2.0)
        expected = 0.98
        assert abs(result - expected) < 1e-6, f"Ожидалось {expected}, получено {result}"


class TestGWPConstants:
    """Тесты для функций GWP констант"""

    def test_co2_equivalent_ch4(self):
        """Проверка перевода CH4 в CO2-эквивалент: 10 т CH4 * GWP(28) = 280 т CO2-экв"""
        result = get_co2_equivalent(10.0, "CH4")
        assert result == 280.0, f"Ожидалось 280.0, получено {result}"

    def test_co2_equivalent_n2o(self):
        """Проверка перевода N2O в CO2-эквивалент: 5 т N2O * GWP(265) = 1325 т CO2-экв"""
        result = get_co2_equivalent(5.0, "N2O")
        assert result == 1325.0, f"Ожидалось 1325.0, получено {result}"

    def test_carbon_to_co2_absorption(self):
        """Проверка перевода углерода в CO2 (поглощение): 100 т C * 3.6640579 * (-1) ≈ -366.41 т CO2"""
        result = carbon_to_co2(100.0, absorption=True)
        expected = -100.0 * (44.009 / 12.011)
        assert abs(result - expected) < 1e-2, f"Ожидалось {expected}, получено {result}"

    def test_nitrogen_to_n2o(self):
        """Проверка перевода азота в N2O: 10 т N * 1.5713 ≈ 15.713 т N2O"""
        result = nitrogen_to_n2o(10.0)
        expected = 10.0 * (44.013 / 28.014)
        assert abs(result - expected) < 1e-2, f"Ожидалось {expected}, получено {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
