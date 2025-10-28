# tests/test_absorption_ui.py
"""
Тесты для улучшенного интерфейса вкладок поглощения.
Проверка работы AbsorptionBaseTab и производных классов.
"""
import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit, QPushButton
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from ui.forest_restoration_tab_improved import ForestRestorationTabImproved
from calculations.absorption_forest_restoration import ForestRestorationCalculator


@pytest.fixture(scope="module")
def qapp():
    """Создает QApplication для тестов UI."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def calculator():
    """Создает калькулятор для лесовосстановления."""
    return ForestRestorationCalculator()


@pytest.fixture
def tab(qapp, calculator):
    """Создает улучшенную вкладку лесовосстановления."""
    return ForestRestorationTabImproved(calculator)


class TestAbsorptionBaseTab:
    """Тесты базового класса AbsorptionBaseTab."""

    def test_tab_creation(self, tab, calculator):
        """Тест создания вкладки."""
        assert tab is not None
        assert tab.calculator == calculator
        assert hasattr(tab, '_input_fields')
        assert isinstance(tab._input_fields, list)

    def test_input_fields_tracked(self, tab):
        """Тест отслеживания полей ввода."""
        assert len(tab._input_fields) > 0
        for field in tab._input_fields:
            assert isinstance(field, QLineEdit)

    def test_result_area_exists(self, tab):
        """Тест наличия области результатов."""
        assert hasattr(tab, 'result_text')
        assert tab.result_text is not None

    def test_clear_button_exists(self, tab):
        """Тест наличия кнопки очистки."""
        clear_buttons = [
            widget for widget in tab.findChildren(QPushButton)
            if "Очистить" in widget.text()
        ]
        assert len(clear_buttons) == 1

    def test_clear_all_fields(self, tab):
        """Тест функции очистки всех полей."""
        # Заполняем поля значениями
        tab.f1_biomass.setText("100.5")
        tab.f1_deadwood.setText("20.3")
        tab.f1_litter.setText("15.7")
        tab.f1_soil.setText("50.2")

        # Очищаем все поля
        tab._clear_all_fields()

        # Проверяем, что поля очищены
        assert tab.f1_biomass.text() == "0.0"
        assert tab.f1_deadwood.text() == "0.0"
        assert tab.f1_litter.text() == "0.0"
        assert tab.f1_soil.text() == "0.0"

    def test_result_area_cleared(self, tab):
        """Тест очистки области результатов."""
        # Устанавливаем результат
        tab.result_text.setText("Test result")
        assert tab.result_text.text() == "Test result"

        # Очищаем
        tab._clear_all_fields()
        assert tab.result_text.text() == ""


class TestForestRestorationTabImproved:
    """Тесты улучшенной вкладки лесовосстановления."""

    def test_formula1_fields_exist(self, tab):
        """Тест наличия полей для формулы 1."""
        assert hasattr(tab, 'f1_biomass')
        assert hasattr(tab, 'f1_deadwood')
        assert hasattr(tab, 'f1_litter')
        assert hasattr(tab, 'f1_soil')

    def test_formula2_fields_exist(self, tab):
        """Тест наличия полей для формулы 2."""
        assert hasattr(tab, 'f2_c_after')
        assert hasattr(tab, 'f2_c_before')
        assert hasattr(tab, 'f2_area')
        assert hasattr(tab, 'f2_period')

    def test_formula3_fields_exist(self, tab):
        """Тест наличия полей для формулы 3."""
        assert hasattr(tab, 'f3_species')
        assert hasattr(tab, 'f3_diameter')
        assert hasattr(tab, 'f3_height')
        assert hasattr(tab, 'f3_count')

    def test_formula5_fields_exist(self, tab):
        """Тест наличия полей для формулы 5."""
        assert hasattr(tab, 'f5_org_percent')
        assert hasattr(tab, 'f5_depth_cm')
        assert hasattr(tab, 'f5_bulk_density')

    def test_formula6_fields_exist(self, tab):
        """Тест наличия полей для формулы 6."""
        assert hasattr(tab, 'f6_area')
        assert hasattr(tab, 'f6_fuel_mass')
        assert hasattr(tab, 'f6_comb_factor')
        assert hasattr(tab, 'f6_gas_type')

    def test_calculate_f1(self, tab):
        """Тест расчета по формуле 1."""
        tab.f1_biomass.setText("100.0")
        tab.f1_deadwood.setText("20.0")
        tab.f1_litter.setText("15.0")
        tab.f1_soil.setText("50.0")

        tab._calculate_f1()

        result_text = tab.result_text.text()
        assert "185" in result_text or "185.0" in result_text

    def test_calculate_f2(self, tab):
        """Тест расчета по формуле 2."""
        tab.f2_c_after.setText("150.0")
        tab.f2_c_before.setText("50.0")
        tab.f2_area.setText("100.0")
        tab.f2_period.setText("5.0")

        tab._calculate_f2()

        result_text = tab.result_text.text()
        assert "2000" in result_text

    def test_calculate_f3(self, tab):
        """Тест расчета по формуле 3."""
        tab.f3_species.setCurrentText("Сосна")
        tab.f3_diameter.setText("30.0")
        tab.f3_height.setText("20.0")
        tab.f3_count.setValue(10)

        tab._calculate_f3()

        result_text = tab.result_text.text()
        assert "Биомасса" in result_text
        assert "Углерод" in result_text

    def test_calculate_f5(self, tab):
        """Тест расчета по формуле 5."""
        tab.f5_org_percent.setText("5.0")
        tab.f5_depth_cm.setText("30.0")
        tab.f5_bulk_density.setText("1.2")

        tab._calculate_f5()

        result_text = tab.result_text.text()
        assert result_text != ""

    def test_calculate_f6(self, tab):
        """Тест расчета по формуле 6."""
        tab.f6_area.setText("1000.0")
        tab.f6_fuel_mass.setText("121.4")
        tab.f6_comb_factor.setText("0.43")
        tab.f6_gas_type.setCurrentText("CO2")

        tab._calculate_f6()

        result_text = tab.result_text.text()
        assert "CO2" in result_text

    def test_invalid_input_handling(self, tab):
        """Тест обработки некорректного ввода."""
        tab.f1_biomass.setText("")  # Пустое поле
        tab.f1_deadwood.setText("20.0")
        tab.f1_litter.setText("15.0")
        tab.f1_soil.setText("50.0")

        tab._calculate_f1()

        result_text = tab.result_text.text()
        assert "Ошибка" in result_text or "error" in result_text.lower()

    def test_default_values(self, tab):
        """Тест значений по умолчанию."""
        # Формула 2: период по умолчанию = 5
        assert tab.f2_period.text() == "5"

        # Формула 5: глубина по умолчанию = 30
        assert tab.f5_depth_cm.text() == "30"

        # Формула 6: масса топлива по умолчанию = 121.4
        assert tab.f6_fuel_mass.text() == "121.4"

        # Формула 6: коэффициент сгорания по умолчанию = 0.43
        assert tab.f6_comb_factor.text() == "0.43"

    def test_species_combobox(self, tab):
        """Тест комбобокса пород деревьев."""
        species_list = [tab.f3_species.itemText(i) for i in range(tab.f3_species.count())]

        # Проверяем наличие основных пород
        assert any("сосна" in s.lower() for s in species_list)
        assert any("ель" in s.lower() for s in species_list)
        assert any("береза" in s.lower() for s in species_list)

    def test_gas_type_combobox(self, tab):
        """Тест комбобокса типов газов."""
        gas_types = [tab.f6_gas_type.itemText(i) for i in range(tab.f6_gas_type.count())]

        assert "CO2" in gas_types
        assert "CH4" in gas_types
        assert "N2O" in gas_types

    def test_multiple_calculations(self, tab):
        """Тест последовательных расчетов."""
        # Первый расчет
        tab.f1_biomass.setText("100.0")
        tab.f1_deadwood.setText("20.0")
        tab.f1_litter.setText("15.0")
        tab.f1_soil.setText("50.0")
        tab._calculate_f1()

        result1 = tab.result_text.text()
        assert "185" in result1

        # Второй расчет
        tab.f2_c_after.setText("150.0")
        tab.f2_c_before.setText("50.0")
        tab.f2_area.setText("100.0")
        tab.f2_period.setText("5.0")
        tab._calculate_f2()

        result2 = tab.result_text.text()
        assert "2000" in result2
        # Результат должен обновиться
        assert result1 != result2


class TestUIIntegration:
    """Интеграционные тесты UI."""

    def test_full_workflow_formula1(self, tab):
        """Тест полного рабочего процесса для формулы 1."""
        # 1. Заполнить поля
        tab.f1_biomass.setText("100.0")
        tab.f1_deadwood.setText("20.0")
        tab.f1_litter.setText("15.0")
        tab.f1_soil.setText("50.0")

        # 2. Рассчитать
        tab._calculate_f1()
        result1 = tab.result_text.text()
        assert result1 != ""

        # 3. Очистить
        tab._clear_all_fields()
        assert tab.f1_biomass.text() == "0.0"
        assert tab.result_text.text() == ""

        # 4. Новый расчет
        tab.f1_biomass.setText("200.0")
        tab.f1_deadwood.setText("40.0")
        tab.f1_litter.setText("30.0")
        tab.f1_soil.setText("100.0")
        tab._calculate_f1()
        result2 = tab.result_text.text()

        assert result2 != ""
        assert result1 != result2

    def test_validator_limits(self, tab):
        """Тест валидации пределов значений."""
        # Формула 3: диаметр должен быть от 0.1 до 1000
        validator = tab.f3_diameter.validator()
        assert validator is not None

        # Проверяем, что валидатор настроен
        assert hasattr(validator, 'bottom')
        assert hasattr(validator, 'top')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
