# tests/test_validation_ranges.py
"""
Тесты для проверки диапазонов валидации в UI компонентах.
"""
import pytest
from ui.validation_ranges import (
    ValidationType,
    ValidationRanges,
    FIELD_VALIDATION_MAP,
    get_validation_for_field
)


class TestValidationType:
    """Тесты для ValidationType enum."""

    def test_fraction_range(self):
        """Проверка диапазона для долей."""
        min_val, max_val, decimals = ValidationType.FRACTION.value
        assert min_val == 0.0
        assert max_val == 1.0
        assert decimals == 4

    def test_oxidation_factor_range(self):
        """Проверка диапазона для коэффициента окисления."""
        min_val, max_val, decimals = ValidationType.OXIDATION_FACTOR.value
        assert min_val == 0.0
        assert max_val == 1.0
        assert decimals == 4

    def test_combustion_factor_range(self):
        """Проверка диапазона для коэффициента сгорания."""
        min_val, max_val, decimals = ValidationType.COMBUSTION_FACTOR.value
        assert min_val == 0.0
        assert max_val == 1.0
        assert decimals == 4

    def test_percent_range(self):
        """Проверка диапазона для процентов."""
        min_val, max_val, decimals = ValidationType.PERCENT.value
        assert min_val == 0.0
        assert max_val == 100.0
        assert decimals == 4

    def test_carbon_change_allows_negative(self):
        """Проверка что изменения углерода могут быть отрицательными."""
        min_val, max_val, decimals = ValidationType.CARBON_CHANGE.value
        assert min_val < 0
        assert max_val > 0

    def test_area_positive(self):
        """Проверка что площадь строго положительная."""
        min_val, max_val, _ = ValidationType.AREA_POSITIVE.value
        assert min_val > 0


class TestValidationRanges:
    """Тесты для класса ValidationRanges."""

    def test_get_returns_correct_tuple(self):
        """Проверка что get возвращает правильный кортеж."""
        result = ValidationRanges.get(ValidationType.OXIDATION_FACTOR)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result == (0.0, 1.0, 4)

    def test_get_tooltip_for_fraction(self):
        """Проверка подсказки для долей."""
        tooltip = ValidationRanges.get_tooltip(ValidationType.FRACTION)
        assert "0.0" in tooltip or "0" in tooltip
        assert "1.0" in tooltip or "1" in tooltip
        assert "доля" in tooltip.lower()

    def test_get_tooltip_for_percent(self):
        """Проверка подсказки для процентов."""
        tooltip = ValidationRanges.get_tooltip(ValidationType.PERCENT)
        assert "%" in tooltip
        assert "100" in tooltip

    def test_get_tooltip_for_carbon_change(self):
        """Проверка подсказки для изменений углерода."""
        tooltip = ValidationRanges.get_tooltip(ValidationType.CARBON_CHANGE)
        assert "отрицательн" in tooltip.lower()

    def test_get_custom(self):
        """Проверка создания пользовательского диапазона."""
        result = ValidationRanges.get_custom(5.0, 10.0, 2)
        assert result == (5.0, 10.0, 2)

    def test_validate_value_within_range(self):
        """Проверка валидации значения в допустимом диапазоне."""
        is_valid, error = ValidationRanges.validate_value(0.5, ValidationType.OXIDATION_FACTOR)
        assert is_valid is True
        assert error is None

    def test_validate_value_below_minimum(self):
        """Проверка валидации значения ниже минимума."""
        is_valid, error = ValidationRanges.validate_value(-0.1, ValidationType.OXIDATION_FACTOR)
        assert is_valid is False
        assert error is not None
        assert "меньше" in error

    def test_validate_value_above_maximum(self):
        """Проверка валидации значения выше максимума."""
        is_valid, error = ValidationRanges.validate_value(1.5, ValidationType.OXIDATION_FACTOR)
        assert is_valid is False
        assert error is not None
        assert "больше" in error

    def test_validate_value_at_boundaries(self):
        """Проверка валидации граничных значений."""
        # Минимум
        is_valid, _ = ValidationRanges.validate_value(0.0, ValidationType.OXIDATION_FACTOR)
        assert is_valid is True

        # Максимум
        is_valid, _ = ValidationRanges.validate_value(1.0, ValidationType.OXIDATION_FACTOR)
        assert is_valid is True


class TestFieldValidationMap:
    """Тесты для отображения полей на типы валидации."""

    def test_oxidation_factor_mapping(self):
        """Проверка отображения для oxidation_factor."""
        assert 'oxidation_factor' in FIELD_VALIDATION_MAP
        assert FIELD_VALIDATION_MAP['oxidation_factor'] == ValidationType.OXIDATION_FACTOR

    def test_combustion_factor_mapping(self):
        """Проверка отображения для combustion_factor."""
        assert 'combustion_factor' in FIELD_VALIDATION_MAP
        assert FIELD_VALIDATION_MAP['combustion_factor'] == ValidationType.COMBUSTION_FACTOR

    def test_area_mapping(self):
        """Проверка отображения для area."""
        assert 'area' in FIELD_VALIDATION_MAP
        assert FIELD_VALIDATION_MAP['area'] == ValidationType.AREA_SMALL

    def test_delta_c_mapping(self):
        """Проверка отображения для delta_c."""
        assert 'delta_c' in FIELD_VALIDATION_MAP
        assert FIELD_VALIDATION_MAP['delta_c'] == ValidationType.CARBON_CHANGE


class TestGetValidationForField:
    """Тесты для функции get_validation_for_field."""

    def test_get_validation_for_known_field(self):
        """Проверка получения валидации для известного поля."""
        result = get_validation_for_field('oxidation_factor')
        assert result == (0.0, 1.0, 4)

    def test_get_validation_for_unknown_field(self):
        """Проверка получения валидации для неизвестного поля."""
        result = get_validation_for_field('unknown_field')
        # Должен вернуть ANY_POSITIVE по умолчанию
        assert result == ValidationType.ANY_POSITIVE.value


class TestValidationConsistency:
    """Тесты для проверки консистентности диапазонов."""

    def test_all_fraction_types_have_same_range(self):
        """Проверка что все типы долей имеют диапазон 0.0-1.0."""
        fraction_types = [
            ValidationType.FRACTION,
            ValidationType.OXIDATION_FACTOR,
            ValidationType.COMBUSTION_FACTOR,
            ValidationType.CARBON_CONTENT,
            ValidationType.EFFICIENCY,
        ]

        for vtype in fraction_types:
            min_val, max_val, _ = vtype.value
            assert min_val == 0.0, f"{vtype} имеет некорректный минимум"
            assert max_val == 1.0, f"{vtype} имеет некорректный максимум"

    def test_all_percent_types_have_same_range(self):
        """Проверка что все типы процентов имеют диапазон 0-100."""
        percent_types = [
            ValidationType.PERCENT,
            ValidationType.PERCENT_STRICT,
            ValidationType.ORGANIC_MATTER,
            ValidationType.MOISTURE,
            ValidationType.ASH_CONTENT,
        ]

        for vtype in percent_types:
            min_val, max_val, _ = vtype.value
            assert min_val == 0.0, f"{vtype} имеет некорректный минимум"
            assert max_val == 100.0, f"{vtype} имеет некорректный максимум"

    def test_positive_strict_types_minimum_above_zero(self):
        """Проверка что строгие положительные типы имеют минимум > 0."""
        strict_types = [
            ValidationType.AREA_POSITIVE,
            ValidationType.VOLUME_POSITIVE,
            ValidationType.MASS_POSITIVE,
            ValidationType.POSITIVE_STRICT,
        ]

        for vtype in strict_types:
            min_val, _, _ = vtype.value
            assert min_val > 0, f"{vtype} должен иметь минимум > 0"


class TestRealWorldScenarios:
    """Тесты для реальных сценариев использования."""

    def test_oxidation_factor_typical_values(self):
        """Проверка типичных значений коэффициента окисления."""
        typical_values = [
            0.95,  # Твердое топливо
            0.99,  # Жидкое топливо
            0.995, # Газообразное топливо
        ]

        for value in typical_values:
            is_valid, _ = ValidationRanges.validate_value(value, ValidationType.OXIDATION_FACTOR)
            assert is_valid, f"Типичное значение {value} должно быть валидным"

    def test_combustion_factor_fire_values(self):
        """Проверка значений коэффициента сгорания для пожаров."""
        fire_values = {
            'верховой': 0.43,
            'низовой': 0.15,
        }

        for fire_type, value in fire_values.items():
            is_valid, _ = ValidationRanges.validate_value(value, ValidationType.COMBUSTION_FACTOR)
            assert is_valid, f"Коэффициент сгорания для {fire_type} пожара ({value}) должен быть валидным"

    def test_organic_matter_realistic_range(self):
        """Проверка реалистичных значений органического вещества."""
        realistic_values = [0.5, 1.0, 5.0, 10.0, 25.0, 50.0, 75.0]

        for value in realistic_values:
            is_valid, _ = ValidationRanges.validate_value(value, ValidationType.ORGANIC_MATTER)
            assert is_valid, f"Реалистичное значение органического вещества {value}% должно быть валидным"

    def test_carbon_change_negative_values(self):
        """Проверка что изменения углерода могут быть отрицательными (потери)."""
        negative_value = -100.5  # Потеря углерода

        is_valid, _ = ValidationRanges.validate_value(negative_value, ValidationType.CARBON_CHANGE)
        assert is_valid, "Отрицательное изменение углерода (потеря) должно быть валидным"

    def test_invalid_oxidation_factor_rejected(self):
        """Проверка что некорректные коэффициенты окисления отклоняются."""
        invalid_values = [-0.1, 1.5, 2.0]

        for value in invalid_values:
            is_valid, _ = ValidationRanges.validate_value(value, ValidationType.OXIDATION_FACTOR)
            assert not is_valid, f"Некорректное значение {value} должно быть отклонено"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
