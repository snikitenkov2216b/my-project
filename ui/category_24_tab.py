# ui/category_24_tab.py - Виджет вкладки для расчетов по Категории 24.
# Реализует интерфейс для расчета выбросов N2O из сточных вод.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_24 import Category24Calculator

class Category24Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 24 "Выбросы закиси азота из сточных вод".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category24Calculator(self.data_service)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        """Инициализирует все элементы пользовательского интерфейса на вкладке."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Группа для расчета азота ---
        nitrogen_group = QGroupBox("Расчет общего количества азота в сточных водах (Формула 4.8)")
        nitrogen_layout = QFormLayout(nitrogen_group)
        
        self.population_input = self._create_line_edit((0, 1_000_000_000, 0))
        nitrogen_layout.addRow("Численность населения (P, чел):", self.population_input)

        self.protein_input = self._create_line_edit((0.0, 1000.0, 4), "30.0")
        self.protein_input.setToolTip("Среднегодовое потребление белка на душу населения. Стандартное значение: 30 кг/чел/год.")
        nitrogen_layout.addRow("Потребление протеина (кг/чел/год):", self.protein_input)

        self.fnpr_input = self._create_line_edit((0.0, 1.0, 4), "0.16")
        self.fnpr_input.setToolTip("Доля азота в белке. Стандартное значение: 0.16 кг N/кг белка.")
        nitrogen_layout.addRow("Доля азота в протеине (F_NPR):", self.fnpr_input)

        self.fnon_con_input = self._create_line_edit((0.0, 10.0, 4), "1.1")
        self.fnon_con_input.setToolTip("Коэффициент, учитывающий белок в продуктах, не предназначенных для потребления человеком. Стандартное значение: 1.1.")
        nitrogen_layout.addRow("Коэф. для непотребленного протеина (F_NON-CON):", self.fnon_con_input)

        self.find_com_input = self._create_line_edit((0.0, 10.0, 4), "1.25")
        self.find_com_input.setToolTip("Коэффициент, учитывающий промышленный и коммерческий сброс белка в канализацию. Стандартное значение: 1.25.")
        nitrogen_layout.addRow("Коэф. для пром. и комм. протеина (F_IND-COM):", self.find_com_input)

        self.sludge_nitrogen_input = self._create_line_edit((0.0, 1e12, 6), "0.0")
        self.sludge_nitrogen_input.setToolTip("Общее количество азота, удаленное с осадком сточных вод за год.")
        nitrogen_layout.addRow("Азот, удаленный с отстоем (N_ОТСТОЙ, кг N/год):", self.sludge_nitrogen_input)

        main_layout.addWidget(nitrogen_group)

        # --- Группа для расчета выбросов N2O ---
        emission_group = QGroupBox("Расчет выбросов N2O (Формула 4.7)")
        emission_layout = QFormLayout(emission_group)

        self.emission_factor_input = self._create_line_edit((0.0, 1.0, 6), "0.005")
        self.emission_factor_input.setToolTip("Коэффициент выбросов для N2O из сточных вод. Стандартное значение: 0.005 кг N2O-N/кг N.")
        emission_layout.addRow("Коэффициент выбросов (EF_сток, кг N2O-N/кг N):", self.emission_factor_input)
        
        main_layout.addWidget(emission_group)

        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы N2O")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, validator_params, default_text=""):
        """Вспомогательная функция для создания поля ввода с валидатором."""
        line_edit = QLineEdit(default_text)
        validator = QDoubleValidator(*validator_params, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        return line_edit

    def _get_float(self, line_edit, field_name):
        """Вспомогательная функция для получения числового значения из поля ввода."""
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            # Сбор данных для расчета азота
            population = self._get_float(self.population_input, "Численность населения")
            protein = self._get_float(self.protein_input, "Потребление протеина")
            fnpr = self._get_float(self.fnpr_input, "Доля азота в протеине")
            fnon_con = self._get_float(self.fnon_con_input, "Коэф. для непотребленного протеина")
            find_com = self._get_float(self.find_com_input, "Коэф. для пром. и комм. протеина")
            sludge_nitrogen = self._get_float(self.sludge_nitrogen_input, "Азот, удаленный с отстоем")
            
            # Вызов метода расчета азота
            nitrogen_in_effluent = self.calculator.calculate_nitrogen_in_effluent(
                population=int(population),
                protein_per_capita=protein,
                fnpr=fnpr,
                fnon_con=fnon_con,
                find_com=find_com,
                sludge_nitrogen_removed=sludge_nitrogen
            )

            # Сбор данных для расчета выбросов N2O
            emission_factor = self._get_float(self.emission_factor_input, "Коэффициент выбросов")

            # Вызов метода расчета выбросов N2O
            n2o_emissions = self.calculator.calculate_n2o_emissions_from_effluent(
                nitrogen_in_effluent=nitrogen_in_effluent,
                emission_factor=emission_factor
            )

            result_text = (
                f"Результат:\n"
                f"Общее кол-во азота в стоках (N_сток): {nitrogen_in_effluent:.2f} кг N/год\n"
                f"Выбросы N2O: {n2o_emissions:.4f} тонн/год"
            )
            self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")