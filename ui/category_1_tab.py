# ui/category_1_tab.py - Виджет вкладки для расчетов по Категории 1.
# Код обновлен для приема калькулятора, автоподстановки, подсказок и логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QHBoxLayout,
    QGroupBox,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_1 import Category1Calculator
from config import OXIDATION_FACTOR_SOLID, OXIDATION_FACTOR_LIQUID, OXIDATION_FACTOR_GAS

from ui.helpers import (
    SectionHeader, InfoBox, ResultDisplayWidget, 
    HorizontalLine, create_tooltip_style
)

class Category1Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 1 "Стационарное сжигание топлива".
    """

    def __init__(self, calculator: Category1Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        self.gas_volume_rows = []
        self.gas_mass_rows = []

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Применяем стиль для подсказок
        self.setStyleSheet(create_tooltip_style())
        
        # Информационный блок
        info_box = InfoBox(
            "ℹ️ О категории", 
            "Расчет выбросов CO₂ от сжигания топлива в стационарных установках "
            "(котлы, печи, ТЭС и др.). Используются данные о расходе топлива, "
            "коэффициенты выбросов и степень окисления."
        )
        main_layout.addWidget(info_box)
        
        # Секция: Основные параметры
        main_layout.addWidget(SectionHeader("🔥 Основные параметры топлива"))
        
        form_layout = QFormLayout()
        
        self.fuel_combobox = QComboBox()
        self.fuel_combobox.addItems(self.calculator.data_service.get_fuels_table_1_1())
        self.fuel_combobox.setToolTip(
            "Выберите вид сжигаемого топлива из справочника.\n"
            "Справочник содержит коэффициенты для расчета выбросов CO₂."
        )
        form_layout.addRow("Вид топлива:", self.fuel_combobox)

        self.fuel_consumption_input = QLineEdit()
        validator_consumption = QDoubleValidator(0.0, 1e12, 6, self)
        validator_consumption.setLocale(self.c_locale)
        self.fuel_consumption_input.setValidator(validator_consumption)
        self.fuel_consumption_input.setPlaceholderText("Введите расход топлива")
        self.fuel_consumption_input.setToolTip(
            "Годовой расход топлива в натуральных единицах:\n"
            "• Для твердого/жидкого топлива: тонны\n"
            "• Для газообразного топлива: тысячи м³"
        )
        form_layout.addRow("Расход топлива (т или тыс. м³):", self.fuel_consumption_input)
        
        main_layout.addLayout(form_layout)
        
        # Разделитель
        main_layout.addWidget(HorizontalLine())
        
        # Секция: Коэффициент выбросов
        main_layout.addWidget(SectionHeader("📊 Коэффициент выбросов (EF)"))

        ef_group = QGroupBox("Метод определения EF")
        ef_layout = QVBoxLayout(ef_group)

        self.ef_method_combobox = QComboBox()
        self.ef_method_combobox.addItems(
            [
                "Использовать стандартный EF (из Таблицы 1.1)",
                "Расчет EF по содержанию углерода (Формула 1.5)",
                "Расчет EF по объемному составу газа (Формула 1.3)",
                "Расчет EF по массовому составу газа (Формула 1.4)",
            ]
        )
        self.ef_method_combobox.setToolTip(
            "Стандартный метод: использует готовое значение из справочника (самый простой).\n"
            "Другие методы: позволяют рассчитать EF на основе состава топлива (для точности)."
        )
        ef_layout.addWidget(self.ef_method_combobox)

        self.ef_stacked_widget = QStackedWidget()
        self.ef_stacked_widget.addWidget(self._create_standard_ef_widget())
        self.ef_stacked_widget.addWidget(self._create_carbon_content_widget())
        self.ef_stacked_widget.addWidget(self._create_gas_composition_volume_widget())
        self.ef_stacked_widget.addWidget(self._create_gas_composition_mass_widget())
        ef_layout.addWidget(self.ef_stacked_widget)

        self.ef_method_combobox.currentIndexChanged.connect(
            self.ef_stacked_widget.setCurrentIndex
        )
        main_layout.addWidget(ef_group)
        
        # Разделитель
        main_layout.addWidget(HorizontalLine())
        
        # Секция: Коэффициент окисления
        main_layout.addWidget(SectionHeader("⚙️ Коэффициент окисления (OF)"))
        
        of_layout = QFormLayout()
        self.oxidation_factor_input = QLineEdit()
        validator_of = QDoubleValidator(0.0, 1.0, 4, self)
        validator_of.setLocale(self.c_locale)
        self.oxidation_factor_input.setValidator(validator_of)
        self.oxidation_factor_input.setPlaceholderText("0.98")
        self.oxidation_factor_input.setToolTip(
            "Доля углерода, окисленного до CO₂ (от 0 до 1).\n\n"
            "Стандартные значения:\n"
            "• Газообразное топливо: 0.995\n"
            "• Жидкое топливо: 0.99\n"
            "• Твердое топливо: 0.98"
        )
        of_layout.addRow("Коэффициент окисления (OF):", self.oxidation_factor_input)
        main_layout.addLayout(of_layout)
        
        # Разделитель
        main_layout.addWidget(HorizontalLine())

        # Кнопка расчета
        self.calculate_button = QPushButton("🧮 Рассчитать выбросы CO₂")
        self.calculate_button.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                padding: 12px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button)

        # Виджет результата
        self.result_widget = ResultDisplayWidget()
        main_layout.addWidget(self.result_widget)

    def _update_oxidation_factor(self):
        """Автоматически обновляет коэффициент окисления на основе типа топлива."""
        fuel_name = self.fuel_combobox.currentText()
        fuel_data = self.calculator.data_service.get_fuel_data_table_1_1(fuel_name)
        if not fuel_data:
            return

        unit = fuel_data.get("unit", "")
        if "тыс. м3" in unit:
            self.oxidation_factor_input.setText(str(OXIDATION_FACTOR_GAS))
        elif any(
            solid in fuel_name.lower()
            for solid in ["уголь", "кокс", "торф", "антрацит", "сланцы", "брикеты"]
        ):
            self.oxidation_factor_input.setText(str(OXIDATION_FACTOR_SOLID))
        else:
            self.oxidation_factor_input.setText(str(OXIDATION_FACTOR_LIQUID))

    def _create_ef_from_carbon_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.carbon_content_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1.0, 6, self)
        validator.setLocale(self.c_locale)
        self.carbon_content_input.setValidator(validator)
        self.carbon_content_input.setToolTip(
            "Массовая доля углерода в топливе (т C/т)."
        )
        layout.addRow(
            "Содержание углерода в топливе (доля):", self.carbon_content_input
        )
        return widget

    def _create_ef_from_gas_volume_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.rho_co2_input = QLineEdit(
            str(self.calculator.data_service.get_density_data_table_1_2()["rho_CO2"])
        )
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        self.rho_co2_input.setValidator(validator)
        self.rho_co2_input.setToolTip(
            "Плотность диоксида углерода при нормальных условиях (20 °C)."
        )
        form.addRow("Плотность CO₂, кг/м³:", self.rho_co2_input)
        layout.addLayout(form)

        group_box = QGroupBox("Компоненты газа (объемные доли)")
        self.gas_volume_layout = QVBoxLayout(group_box)
        layout.addWidget(group_box)
        add_button = QPushButton("Добавить компонент")
        add_button.clicked.connect(self._add_gas_volume_row)
        layout.addWidget(add_button)
        return widget

    def _create_ef_from_gas_mass_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.fuel_density_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        self.fuel_density_input.setValidator(validator)
        self.fuel_density_input.setToolTip(
            "Плотность газообразного топлива при нормальных условиях."
        )
        form.addRow("Плотность топлива, кг/м³:", self.fuel_density_input)
        layout.addLayout(form)

        group_box = QGroupBox("Компоненты газа (массовые доли)")
        self.gas_mass_layout = QVBoxLayout(group_box)
        layout.addWidget(group_box)
        add_button = QPushButton("Добавить компонент")
        add_button.clicked.connect(self._add_gas_mass_row)
        layout.addWidget(add_button)
        return widget

    def _add_gas_volume_row(self):
        row = {"widget": QWidget()}
        layout = QHBoxLayout(row["widget"])
        row["fraction"] = QLineEdit(placeholderText="Доля, %")
        row["fraction"].setToolTip("Объемная доля компонента в смеси.")
        row["carbon_atoms"] = QLineEdit(placeholderText="Атомов C")
        row["carbon_atoms"].setToolTip("Число атомов углерода в молекуле компонента.")
        remove_button = QPushButton("Удалить")
        layout.addWidget(row["fraction"])
        layout.addWidget(row["carbon_atoms"])
        layout.addWidget(remove_button)
        self.gas_volume_rows.append(row)
        self.gas_volume_layout.addWidget(row["widget"])
        remove_button.clicked.connect(
            lambda: self._remove_row(row, self.gas_volume_layout, self.gas_volume_rows)
        )

    def _add_gas_mass_row(self):
        row = {"widget": QWidget()}
        layout = QHBoxLayout(row["widget"])
        row["fraction"] = QLineEdit(placeholderText="Доля, %")
        row["fraction"].setToolTip("Массовая доля компонента в смеси.")
        row["carbon_atoms"] = QLineEdit(placeholderText="Атомов C")
        row["carbon_atoms"].setToolTip("Число атомов углерода в молекуле компонента.")
        row["molar_mass"] = QLineEdit(placeholderText="Молярная масса")
        row["molar_mass"].setToolTip("Молярная масса компонента, г/моль.")
        remove_button = QPushButton("Удалить")
        layout.addWidget(row["fraction"])
        layout.addWidget(row["carbon_atoms"])
        layout.addWidget(row["molar_mass"])
        layout.addWidget(remove_button)
        self.gas_mass_rows.append(row)
        self.gas_mass_layout.addWidget(row["widget"])
        remove_button.clicked.connect(
            lambda: self._remove_row(row, self.gas_mass_layout, self.gas_mass_rows)
        )

    def _remove_row(self, row, layout, storage):
        row["widget"].deleteLater()
        layout.removeWidget(row["widget"])
        storage.remove(row)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        """Выполняет расчет выбросов CO2 с улучшенной обработкой ошибок."""
        try:
            # Очищаем предыдущий результат
            self.result_widget.clear()
            
            fuel_name = self.fuel_combobox.currentText()
            
            # Получаем расход топлива
            fuel_consumption_str = self.fuel_consumption_input.text().replace(',', '.')
            if not fuel_consumption_str:
                self.result_widget.set_error("Введите расход топлива")
                return
            
            try:
                fuel_consumption = float(fuel_consumption_str)
            except ValueError:
                self.result_widget.set_error("Неверный формат расхода топлива")
                return
            
            if fuel_consumption <= 0:
                self.result_widget.set_error("Расход топлива должен быть больше нуля")
                return

            # Получаем коэффициент окисления
            oxidation_factor_str = self.oxidation_factor_input.text().replace(',', '.')
            if oxidation_factor_str:
                try:
                    oxidation_factor = float(oxidation_factor_str)
                    if not (0 < oxidation_factor <= 1):
                        self.result_widget.set_error("OF должен быть от 0 до 1")
                        return
                except ValueError:
                    self.result_widget.set_error("Неверный формат коэффициента окисления")
                    return
            else:
                # Автоматический выбор OF по типу топлива
                fuel_data = self.calculator.data_service.get_fuel_data_table_1_1(fuel_name)
                unit = fuel_data.get('unit', 'тонна')
                if 'м3' in unit:
                    oxidation_factor = OXIDATION_FACTOR_GAS
                elif 'тонна' in unit:
                    oxidation_factor = OXIDATION_FACTOR_SOLID
                else:
                    oxidation_factor = OXIDATION_FACTOR_LIQUID
                
                logging.info(f"Автоматически выбран OF = {oxidation_factor} для топлива '{fuel_name}'")

            # Определяем метод расчета EF
            ef_method_index = self.ef_method_combobox.currentIndex()

            if ef_method_index == 0:
                # Стандартный EF
                fuel_data = self.calculator.data_service.get_fuel_data_table_1_1(fuel_name)
                if not fuel_data:
                    self.result_widget.set_error(f"Данные для топлива '{fuel_name}' не найдены")
                    return
                
                ef_co2 = fuel_data.get('EF_CO2_ut')
                if ef_co2 is None:
                    self.result_widget.set_error(f"EF_CO2 для '{fuel_name}' не найден в таблице")
                    return

            elif ef_method_index == 1:
                # Расчет EF по содержанию углерода
                carbon_content_str = self.carbon_content_input.text().replace(',', '.')
                if not carbon_content_str:
                    self.result_widget.set_error("Введите содержание углерода")
                    return
                
                try:
                    carbon_content = float(carbon_content_str)
                    if not (0 <= carbon_content <= 1):
                        self.result_widget.set_error("Содержание углерода должно быть от 0 до 1")
                        return
                except ValueError:
                    self.result_widget.set_error("Неверный формат содержания углерода")
                    return
                
                ef_co2 = self.calculator.calculate_ef_from_carbon_content(carbon_content)

            elif ef_method_index == 2:
                # Расчет EF по объемному составу газа
                if not self.gas_volume_rows:
                    self.result_widget.set_error("Добавьте компоненты газа")
                    return
                
                components = []
                for row in self.gas_volume_rows:
                    try:
                        volume_fraction = float(row['volume_fraction'].text().replace(',', '.'))
                        carbon_atoms = int(row['carbon_atoms'].text())
                        components.append({
                            'volume_fraction': volume_fraction,
                            'carbon_atoms': carbon_atoms
                        })
                    except ValueError:
                        self.result_widget.set_error("Проверьте данные компонентов газа")
                        return
                
                rho_co2 = self.calculator.data_service.get_density_data_table_1_2()['rho_CO2']
                ef_co2 = self.calculator.calculate_ef_from_gas_composition_volume(
                    components, rho_co2
                )

            elif ef_method_index == 3:
                # Расчет EF по массовому составу газа
                if not self.gas_mass_rows:
                    self.result_widget.set_error("Добавьте компоненты газа")
                    return
                
                components = []
                for row in self.gas_mass_rows:
                    try:
                        mass_fraction = float(row['mass_fraction'].text().replace(',', '.'))
                        carbon_atoms = int(row['carbon_atoms'].text())
                        molar_mass = float(row['molar_mass'].text().replace(',', '.'))
                        components.append({
                            'mass_fraction': mass_fraction,
                            'carbon_atoms': carbon_atoms,
                            'molar_mass': molar_mass
                        })
                    except ValueError:
                        self.result_widget.set_error("Проверьте данные компонентов газа")
                        return
                
                fuel_density_str = self.fuel_density_input.text().replace(',', '.')
                if not fuel_density_str:
                    self.result_widget.set_error("Введите плотность топлива")
                    return
                
                try:
                    fuel_density = float(fuel_density_str)
                except ValueError:
                    self.result_widget.set_error("Неверный формат плотности")
                    return
                
                ef_co2 = self.calculator.calculate_ef_from_gas_composition_mass(
                    components, fuel_density
                )

            # Финальный расчет выбросов
            total_emissions = self.calculator.calculate_total_emissions(
                fuel_consumption, ef_co2, oxidation_factor
            )

            # Отображаем результат
            self.result_widget.set_result(total_emissions, "т CO₂")
            
            logging.info(
                f"Категория 1 - Расчет завершен: Топливо='{fuel_name}', "
                f"Расход={fuel_consumption}, EF={ef_co2}, OF={oxidation_factor}, "
                f"Выбросы={total_emissions:.2f} т CO₂"
            )

        except ValueError as e:
            error_msg = str(e)
            self.result_widget.set_error(error_msg)
            logging.error(f"Категория 1 - Ошибка валидации: {e}")
            
        except Exception as e:
            error_msg = f"Ошибка расчета: {e}"
            self.result_widget.set_error(error_msg)
            logging.error(f"Категория 1 - Неожиданная ошибка: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", error_msg)
