# calculations/custom_formula_evaluator.py
"""
Модуль для безопасного парсинга и вычисления пользовательских формул.
Полностью переработанная версия с надежной обработкой математических выражений.

Автор: GHG Calculator Team
Версия: 2.0
"""

import logging
import re
from typing import Dict, Set, List
from sympy import sympify, Symbol, SympifyError, sqrt, exp, log, sin, cos, tan, pi, E
from sympy.core.expr import Expr
import math


class CustomFormulaEvaluator:
    """
    Безопасный эвалюатор математических формул с поддержкой:
    - Смешанного синтаксиса (LaTeX + обычная запись)
    - Блоков суммирования с индексацией
    - Валидации входных данных
    - Подробного логирования ошибок
    """

    def __init__(self):
        """Инициализация эвалюатора."""
        self.logger = logging.getLogger(__name__)
        
    def _preprocess_formula(self, formula_text: str) -> str:
        """
        Предобработка формулы: конвертация в синтаксис SymPy.
        
        Поддерживаемые преобразования:
        - E = ... → извлечение правой части
        - \\times, \\cdot → *
        - \\frac{a}{b} → (a)/(b)
        - \\sqrt{x} → sqrt(x)
        - var_{index} → var_index
        
        Args:
            formula_text: Исходная формула
            
        Returns:
            Обработанная формула в синтаксисе SymPy
        """
        # Удаляем пробелы в начале и конце
        formula_text = formula_text.strip()
        
        # Если есть знак равенства, берем правую часть
        if '=' in formula_text:
            parts = formula_text.split('=', 1)
            expression_part = parts[1].strip()
        else:
            expression_part = formula_text
        
        # Замены LaTeX → обычный синтаксис
        replacements = [
            (r'\\times', '*'),
            (r'\\cdot', '*'),
            (r'\\div', '/'),
        ]
        
        processed = expression_part
        for latex, replacement in replacements:
            processed = processed.replace(latex, replacement)
        
        # \\frac{числитель}{знаменатель} → (числитель)/(знаменатель)
        processed = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', processed)
        
        # \\sqrt{x} → sqrt(x)
        processed = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', processed)
        
        # Индексы: переменная_{индекс} → переменная_индекс (без фигурных скобок)
        # Но нужно сохранить индексы для правильного парсинга
        processed = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)_\{([a-zA-Z0-9,]+)\}', r'\1_\2', processed)
        
        self.logger.debug(f"Preprocessed formula: '{formula_text}' → '{processed}'")
        return processed

    def parse_variables(self, formula_text: str) -> Set[str]:
        """
        Извлекает все переменные из формулы.
        
        Args:
            formula_text: Формула для анализа
            
        Returns:
            Множество имен переменных
            
        Raises:
            ValueError: При ошибке парсинга формулы
        """
        try:
            processed_formula = self._preprocess_formula(formula_text)
            expression = sympify(processed_formula, evaluate=False)
            
            # Получаем все свободные символы (переменные)
            variables = expression.free_symbols
            var_names = {str(v) for v in variables}
            
            self.logger.debug(f"Parsed variables: {var_names}")
            return var_names
            
        except SympifyError as e:
            error_msg = f"Ошибка парсинга формулы: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Неожиданная ошибка при парсинге: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def evaluate(self, formula_text: str, variables: Dict[str, float]) -> float:
        """
        Вычисляет значение формулы с заданными переменными.
        
        Args:
            formula_text: Формула для вычисления
            variables: Словарь значений переменных
            
        Returns:
            Результат вычисления
            
        Raises:
            ValueError: При ошибке вычисления
        """
        try:
            processed_formula = self._preprocess_formula(formula_text)
            expression = sympify(processed_formula, evaluate=False)
            
            # Проверяем наличие всех необходимых переменных
            required_vars = {str(v) for v in expression.free_symbols}
            missing_vars = required_vars - set(variables.keys())
            
            if missing_vars:
                raise ValueError(
                    f"Отсутствуют значения для переменных: {', '.join(missing_vars)}"
                )
            
            # Подставляем значения переменных
            subs_dict = {Symbol(key): value for key, value in variables.items()}
            result = expression.subs(subs_dict)
            
            # Вычисляем численное значение
            numeric_result = float(result.evalf())
            
            self.logger.info(
                f"Formula evaluated: '{formula_text}' = {numeric_result:.6f}"
            )
            return numeric_result
            
        except ValueError:
            raise  # Пробрасываем ValueError дальше
        except Exception as e:
            error_msg = f"Ошибка при вычислении формулы: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def evaluate_sum_block(
        self,
        expression_template: str,
        variables_by_index: List[Dict[str, float]]
    ) -> float:
        """
        Вычисляет блок суммирования: Σ(выражение_j) для j=1..n.
        
        Выражение должно содержать индексированные переменные с суффиксом '_j',
        которые заменяются на '_1', '_2', ... '_n' для каждого элемента.
        
        Args:
            expression_template: Шаблон выражения с '_j' (например, 'a_j * b_j')
            variables_by_index: Список словарей значений для каждого индекса
            
        Returns:
            Сумма всех вычисленных выражений
            
        Raises:
            ValueError: При ошибке вычисления
            
        Example:
            >>> evaluator = CustomFormulaEvaluator()
            >>> template = "FC_j * EF_j"
            >>> variables = [
            ...     {'FC_1': 100, 'EF_1': 2.5},
            ...     {'FC_2': 200, 'EF_2': 3.0}
            ... ]
            >>> result = evaluator.evaluate_sum_block(template, variables)
            >>> # result = 100*2.5 + 200*3.0 = 850.0
        """
        if not variables_by_index:
            raise ValueError("Список переменных для суммирования пуст")
        
        total_sum = 0.0
        
        for i, variables in enumerate(variables_by_index, start=1):
            # Заменяем '_j' на '_i' в шаблоне выражения
            current_expression = expression_template.replace('_j', f'_{i}')
            
            try:
                # Вычисляем текущий элемент суммы
                element_result = self.evaluate(current_expression, variables)
                total_sum += element_result
                
                self.logger.debug(
                    f"Sum block element {i}: {current_expression} = {element_result:.6f}"
                )
                
            except Exception as e:
                raise ValueError(
                    f"Ошибка при вычислении элемента {i} блока суммирования: {e}"
                )
        
        self.logger.info(
            f"Sum block total: {expression_template} (n={len(variables_by_index)}) = {total_sum:.6f}"
        )
        return total_sum

    def extract_variables(self, formula_text: str) -> Set[str]:
        """
        Извлекает переменные из выражения (алиас для parse_variables).

        Args:
            formula_text: Формула для анализа

        Returns:
            Множество имен переменных
        """
        return self.parse_variables(formula_text)

    # ==================== СПЕЦИАЛИЗИРОВАННЫЕ ФУНКЦИИ ДЛЯ ПГ ====================

    def calculate_co2_from_fuel(self, fuel_consumption: float, emission_factor: float,
                                oxidation_factor: float = 1.0) -> float:
        """
        Расчет выбросов CO2 от сжигания топлива.

        Формула: E_CO2 = FC * EF * OF

        Args:
            fuel_consumption: Расход топлива (т, м³)
            emission_factor: Коэффициент эмиссии (т CO2/т топлива)
            oxidation_factor: Коэффициент окисления (по умолчанию 1.0)

        Returns:
            Выбросы CO2 в тоннах
        """
        return fuel_consumption * emission_factor * oxidation_factor

    def calculate_ch4_n2o(self, fuel_consumption: float, emission_factor: float,
                         gwp: float = 1.0) -> float:
        """
        Расчет выбросов CH4 или N2O с учетом потенциала глобального потепления.

        Формула: E_gas = FC * EF * GWP

        Args:
            fuel_consumption: Расход топлива (т, м³)
            emission_factor: Коэффициент эмиссии (кг газа/т топлива)
            gwp: Потенциал глобального потепления (CH4=25, N2O=298)

        Returns:
            Выбросы в CO2-эквиваленте (т)
        """
        return (fuel_consumption * emission_factor * gwp) / 1000  # кг → т

    def calculate_carbon_content(self, carbon_fraction: float, mass: float) -> float:
        """
        Расчет содержания углерода в материале.

        Формула: C = mass * carbon_fraction

        Args:
            carbon_fraction: Доля углерода (0-1)
            mass: Масса материала (т)

        Returns:
            Масса углерода (т)
        """
        return carbon_fraction * mass

    def calculate_co2_from_carbon(self, carbon_mass: float) -> float:
        """
        Преобразование массы углерода в массу CO2.

        Формула: CO2 = C * (44/12)

        Args:
            carbon_mass: Масса углерода (т)

        Returns:
            Масса CO2 (т)
        """
        return carbon_mass * (44.0 / 12.0)

    def calculate_weighted_average(self, values: List[float], weights: List[float]) -> float:
        """
        Расчет взвешенного среднего.

        Формула: avg = Σ(value_i * weight_i) / Σ(weight_i)

        Args:
            values: Список значений
            weights: Список весов

        Returns:
            Взвешенное среднее

        Raises:
            ValueError: Если длины списков не совпадают или веса равны 0
        """
        if len(values) != len(weights):
            raise ValueError("Длины списков values и weights должны совпадать")

        total_weight = sum(weights)
        if total_weight == 0:
            raise ValueError("Сумма весов не может быть равна 0")

        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / total_weight

    def interpolate_linear(self, x: float, x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Линейная интерполяция между двумя точками.

        Формула: y = y1 + (y2-y1) * (x-x1) / (x2-x1)

        Args:
            x: Значение для интерполяции
            x1, y1: Первая точка
            x2, y2: Вторая точка

        Returns:
            Интерполированное значение y
        """
        if x2 == x1:
            return y1
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

    def calculate_decay_exponential(self, initial: float, rate: float, time: float) -> float:
        """
        Экспоненциальный распад (например, для метана на свалках).

        Формула: N(t) = N0 * exp(-rate * t)

        Args:
            initial: Начальное значение
            rate: Константа скорости распада
            time: Время

        Returns:
            Значение после распада
        """
        return initial * math.exp(-rate * time)

    def validate_formula_syntax(self, formula_text: str) -> tuple[bool, str]:
        """
        Проверяет синтаксическую корректность формулы.
        
        Args:
            formula_text: Формула для проверки
            
        Returns:
            Кортеж (is_valid, error_message)
        """
        try:
            processed = self._preprocess_formula(formula_text)
            sympify(processed, evaluate=False)
            return True, ""
        except Exception as e:
            return False, str(e)


# ==================== ТЕСТЫ ====================

def _run_tests():
    """Внутренние тесты модуля."""
    evaluator = CustomFormulaEvaluator()
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ CustomFormulaEvaluator")
    print("=" * 60)
    
    # Тест 1: Простая формула
    print("\n[ТЕСТ 1] Простая формула: a * b + c")
    result = evaluator.evaluate("a * b + c", {'a': 10, 'b': 2, 'c': 5})
    assert result == 25.0, f"Ожидалось 25.0, получено {result}"
    print(f"✓ Результат: {result}")
    
    # Тест 2: Формула с делением
    print("\n[ТЕСТ 2] Деление: (a + b) / c")
    result = evaluator.evaluate("(a + b) / c", {'a': 100, 'b': 50, 'c': 3})
    expected = 50.0
    assert abs(result - expected) < 1e-6, f"Ожидалось {expected}, получено {result}"
    print(f"✓ Результат: {result:.6f}")
    
    # Тест 3: Степень
    print("\n[ТЕСТ 3] Степень: a**2 + b**3")
    result = evaluator.evaluate("a**2 + b**3", {'a': 3, 'b': 2})
    expected = 9 + 8
    assert result == expected, f"Ожидалось {expected}, получено {result}"
    print(f"✓ Результат: {result}")
    
    # Тест 4: Блок суммирования
    print("\n[ТЕСТ 4] Блок суммирования: Σ(a_j * b_j)")
    variables = [
        {'a_1': 5, 'b_1': 2},
        {'a_2': 10, 'b_2': 3},
        {'a_3': 15, 'b_3': 4}
    ]
    result = evaluator.evaluate_sum_block("a_j * b_j", variables)
    expected = 5*2 + 10*3 + 15*4  # 10 + 30 + 60 = 100
    assert result == expected, f"Ожидалось {expected}, получено {result}"
    print(f"✓ Результат: {result}")
    
    # Тест 5: Реальная формула выбросов
    print("\n[ТЕСТ 5] Реальная формула: E_CO2 = FC * EF * OF")
    result = evaluator.evaluate(
        "E_CO2_y = FC_y * EF_CO2_y * OF_y",
        {'FC_y': 1000, 'EF_CO2_y': 2.5, 'OF_y': 0.98}
    )
    expected = 1000 * 2.5 * 0.98
    assert abs(result - expected) < 1e-6, f"Ожидалось {expected}, получено {result}"
    print(f"✓ Результат: {result:.2f} т CO2")
    
    # Тест 6: Парсинг переменных
    print("\n[ТЕСТ 6] Парсинг переменных из формулы")
    vars_set = evaluator.parse_variables("E = FC_1 * EF_CO2 + Sum_Block_1 * k_factor")
    expected_vars = {'FC_1', 'EF_CO2', 'Sum_Block_1', 'k_factor'}
    assert vars_set == expected_vars, f"Ожидалось {expected_vars}, получено {vars_set}"
    print(f"✓ Найдены переменные: {vars_set}")
    
    print("\n" + "=" * 60)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! ✓")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    _run_tests()
