# calculations/custom_formula_evaluator.py
# Модуль для безопасного парсинга и вычисления пользовательских формул.
# Финальная версия с надежной обработкой смешанного синтаксиса и блоков суммирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
import re
from sympy import sympify, Symbol

class CustomFormulaEvaluator:
    """
    Безопасно парсит и вычисляет математические выражения, записанные 
    в смешанном формате, и обрабатывает блоки суммирования.
    """

    def _preprocess_formula(self, formula_text: str) -> str:
        """
        Подготавливает строку формулы к парсингу, преобразуя ее в синтаксис,
        понятный для SymPy.
        """
        if '=' in formula_text:
            expression_part = formula_text.split('=', 1)[1].strip()
        else:
            expression_part = formula_text
        
        processed = expression_part.replace(r'\times', '*')
        processed = processed.replace(r'\cdot', '*')
        processed = re.sub(r'\\frac{([^}]+)}{([^}]+)}', r'(\1)/(\2)', processed)
        processed = re.sub(r'\\sqrt{([^}]+)}', r'sqrt(\1)', processed)
        processed = re.sub(r'([a-zA-Z]+)_{([a-zA-Z0-9,]+)}', r'\1_\2', processed)
        
        return processed

    def parse_variables(self, formula_text: str) -> set:
        """
        Парсит строку и возвращает множество имен всех переменных.
        """
        try:
            processed_formula = self._preprocess_formula(formula_text)
            expression = sympify(processed_formula)
            variables = expression.free_symbols
            return {str(v) for v in variables}
        except Exception as e:
            logging.error(f"Ошибка парсинга для поиска переменных: {e}")
            raise ValueError(f"Некорректный синтаксис: {e}")

    def evaluate_sum_block(self, expression_template: str, variables_by_index: list) -> float:
        """
        Вычисляет сумму выражения для набора индексированных переменных.
        """
        total_sum = 0.0
        for i, variables in enumerate(variables_by_index, 1):
            current_expression_str = expression_template.replace('_j', f'_{i}')
            total_sum += self.evaluate(current_expression_str, variables)
        return total_sum

    def evaluate(self, formula_text: str, variables: dict) -> float:
        """
        Безопасно вычисляет формулу с заданными переменными.
        """
        try:
            processed_formula = self._preprocess_formula(formula_text)
            expression = sympify(processed_formula)
            
            subs_dict = {sympify(key): value for key, value in variables.items()}
            result = expression.evalf(subs=subs_dict)
            
            return float(result)
        except Exception as e:
            logging.error(f"Ошибка вычисления формулы: {e}")
            raise ValueError(f"Ошибка при вычислении формулы: {e}")