# tests/test_custom_formula.py
"""
Тесты для модуля custom_formula_evaluator.
Проверяет парсинг пользовательских формул и вычисление блоков суммирования.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from calculations.custom_formula_evaluator import CustomFormulaEvaluator


class TestCustomFormulaEvaluator:
    """Тесты для CustomFormulaEvaluator"""

    def test_simple_formula_parsing(self):
        """Проверка парсинга простой формулы"""
        evaluator = CustomFormulaEvaluator()
        formula = "E_CO2 = a * b + c"
        variables = evaluator.parse_variables(formula)

        assert variables == {'a', 'b', 'c'}, f"Ожидались переменные {{a, b, c}}, получены {variables}"

    def test_simple_formula_evaluation(self):
        """Проверка вычисления простой формулы: a * b + c"""
        evaluator = CustomFormulaEvaluator()
        formula = "a * b + c"
        result = evaluator.evaluate(formula, {'a': 10, 'b': 2, 'c': 5})

        assert result == 25.0, f"Ожидалось 25.0, получено {result}"

    def test_complex_formula_with_division(self):
        """Проверка формулы с делением: (a + b) / c"""
        evaluator = CustomFormulaEvaluator()
        formula = "(a + b) / c"
        result = evaluator.evaluate(formula, {'a': 100, 'b': 50, 'c': 3})

        expected = 150 / 3
        assert abs(result - expected) < 1e-6, f"Ожидалось {expected}, получено {result}"

    def test_power_operation(self):
        """Проверка возведения в степень: a**2 + b**3"""
        evaluator = CustomFormulaEvaluator()
        formula = "a**2 + b**3"
        result = evaluator.evaluate(formula, {'a': 3, 'b': 2})

        expected = 3**2 + 2**3  # 9 + 8 = 17
        assert result == expected, f"Ожидалось {expected}, получено {result}"

    def test_latex_notation_parsing(self):
        """Проверка парсинга LaTeX нотации: FC_j_y * EF_CO2_j_y"""
        evaluator = CustomFormulaEvaluator()
        formula = "FC_j_y * EF_CO2_j_y"
        variables = evaluator.parse_variables(formula)

        assert 'FC_j_y' in variables and 'EF_CO2_j_y' in variables, \
            f"Переменные не распознаны правильно: {variables}"

    def test_sum_block_evaluation(self):
        """
        Проверка блока суммирования: Sum_{j=1}^{3} (FC_j * EF_j)
        FC_1 = 10, EF_1 = 2  =>  10 * 2 = 20
        FC_2 = 15, EF_2 = 3  =>  15 * 3 = 45
        FC_3 = 20, EF_3 = 1  =>  20 * 1 = 20
        Сумма = 20 + 45 + 20 = 85
        """
        evaluator = CustomFormulaEvaluator()
        expression_template = "FC_j * EF_j"

        variables_by_index = [
            {'FC_1': 10, 'EF_1': 2},
            {'FC_2': 15, 'EF_2': 3},
            {'FC_3': 20, 'EF_3': 1}
        ]

        result = evaluator.evaluate_sum_block(expression_template, variables_by_index)
        expected = 10*2 + 15*3 + 20*1  # 20 + 45 + 20 = 85

        assert result == expected, f"Ожидалось {expected}, получено {result}"

    def test_complex_sum_block(self):
        """
        Проверка сложного блока суммирования: Sum (a_j + b_j) * c_j
        """
        evaluator = CustomFormulaEvaluator()
        expression_template = "(a_j + b_j) * c_j"

        variables_by_index = [
            {'a_1': 5, 'b_1': 3, 'c_1': 2},   # (5+3)*2 = 16
            {'a_2': 10, 'b_2': 2, 'c_2': 3},  # (10+2)*3 = 36
        ]

        result = evaluator.evaluate_sum_block(expression_template, variables_by_index)
        expected = (5+3)*2 + (10+2)*3  # 16 + 36 = 52

        assert result == expected, f"Ожидалось {expected}, получено {result}"

    def test_invalid_formula_raises_error(self):
        """Проверка, что некорректная формула вызывает ошибку"""
        evaluator = CustomFormulaEvaluator()

        with pytest.raises(ValueError, match="Некорректный синтаксис"):
            evaluator.parse_variables("a ** ** b")  # Некорректный синтаксис

    def test_missing_variable_raises_error(self):
        """Проверка, что отсутствие переменной вызывает ошибку"""
        evaluator = CustomFormulaEvaluator()

        with pytest.raises(ValueError, match="Ошибка при вычислении формулы"):
            evaluator.evaluate("a * b", {'a': 10})  # b отсутствует

    def test_real_world_emissions_formula(self):
        """
        Реальный пример: E_CO2_y = FC_y * EF_CO2_y * OF_y
        FC_y = 1000 т
        EF_CO2_y = 2.5 т CO2/т
        OF_y = 0.98
        E_CO2_y = 1000 * 2.5 * 0.98 = 2450 т CO2
        """
        evaluator = CustomFormulaEvaluator()
        formula = "E_CO2_y = FC_y * EF_CO2_y * OF_y"

        result = evaluator.evaluate(formula, {
            'FC_y': 1000,
            'EF_CO2_y': 2.5,
            'OF_y': 0.98
        })

        expected = 1000 * 2.5 * 0.98
        assert abs(result - expected) < 1e-6, f"Ожидалось {expected}, получено {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
