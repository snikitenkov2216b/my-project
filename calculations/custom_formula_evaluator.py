# calculations/custom_formula_evaluator.py
# Модуль для безопасного парсинга и вычисления пользовательских формул в формате LaTeX.
# Код обновлен для автоматической замены \times на *
# Комментарии на русском. Поддержка UTF-8.

import logging
from sympy.parsing.latex import parse_latex
from sympy import sympify

class CustomFormulaEvaluator:
    """
    Безопасно парсит и вычисляет математические выражения, записанные в формате LaTeX,
    используя библиотеку SymPy. Поддерживает формулы с присваиванием (напр., A = ...).
    """

    def _preprocess_formula(self, formula_latex: str) -> str:
        """
        Подготавливает строку формулы к парсингу:
        1. Отделяет правую часть уравнения, если оно есть.
        2. Заменяет LaTeX-команду \times на оператор *.
        """
        if '=' in formula_latex:
            expression_part = formula_latex.split('=', 1)[1].strip()
        else:
            expression_part = formula_latex
        
        # Заменяем LaTeX команду умножения на стандартный оператор
        return expression_part.replace(r'\times', '*')

    def parse_variables(self, formula_latex: str) -> set:
        """
        Парсит строку LaTeX и возвращает множество имен всех переменных.
        
        :param formula_latex: Строка с формулой в формате LaTeX.
        :return: Множество уникальных имен переменных (sympy.Symbol).
        """
        try:
            processed_formula = self._preprocess_formula(formula_latex)
            # Преобразуем строку в выражение SymPy
            expression = parse_latex(processed_formula)
            # Находим все "свободные символы" - это и есть наши переменные
            variables = expression.free_symbols
            return variables
        except Exception as e:
            logging.error(f"Ошибка парсинга LaTeX для поиска переменных: {e}")
            raise ValueError(f"Некорректный синтаксис LaTeX: {e}")

    def evaluate(self, formula_latex: str, variables: dict) -> float:
        """
        Безопасно вычисляет LaTeX-формулу с заданными переменными.
        
        :param formula_latex: Строка с математическим выражением в формате LaTeX.
        :param variables: Словарь, где ключи - это имена переменных (строки),
                          а значения - их числовые значения.
        :return: Результат вычисления в виде числа с плавающей точкой.
        """
        try:
            processed_formula = self._preprocess_formula(formula_latex)
            # Парсим LaTeX-строку в математическое выражение
            expression = parse_latex(processed_formula)
            
            # Создаем словарь для подстановки, преобразуя строковые ключи в символы SymPy
            subs_dict = {sympify(key): value for key, value in variables.items()}

            # Подставляем значения и вычисляем результат
            result = expression.evalf(subs=subs_dict)
            
            return float(result)
        except Exception as e:
            logging.error(f"Ошибка вычисления LaTeX-формулы: {e}")
            raise ValueError(f"Ошибка при вычислении формулы: {e}")