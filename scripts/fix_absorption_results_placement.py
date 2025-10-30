"""
Скрипт для исправления расположения результатов в absorption tabs.
Добавляет QLabel результаты после каждой кнопки "Рассчитать" и удаляет нижний result_text.
"""
import re
import os

def fix_forest_restoration_tab():
    """Исправляет forest_restoration_tab.py"""
    file_path = "ui/forest_restoration_tab.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Удаляем блок result_text и кнопку очистки (строки 191-198)
    content = re.sub(
        r'\n\s+# --- Результаты ---\n\s+self\.result_text = QTextEdit\(\).*?\n\s+layout\.addWidget\(self\.result_text\)\n\s+\n\s+# Кнопка очистки результатов\n\s+clear_results_btn = QPushButton\("🗑 Очистить результаты"\)\n\s+clear_results_btn\.clicked\.connect\(lambda: self\.result_text\.clear\(\)\)\n\s+layout\.addWidget\(clear_results_btn\)\n',
        '\n',
        content
    )

    # Добавляем результаты после каждой кнопки расчета

    # Ф.1
    content = re.sub(
        r'(calc_f1_btn = QPushButton\("Рассчитать ΔC общее \(Ф\. 1\)"\); calc_f1_btn\.clicked\.connect\(self\._calculate_f1\)\n\s+carbon_layout\.addRow\(calc_f1_btn\))',
        r'\1\n        self.f1_result = QLabel("—"); self.f1_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f1_result.setWordWrap(True)\n        carbon_layout.addRow("Результат:", self.f1_result)',
        content
    )

    # Ф.2
    content = re.sub(
        r'(calc_f2_btn = QPushButton\("Рассчитать ΔC биомассы \(Ф\. 2\)"\); calc_f2_btn\.clicked\.connect\(self\._calculate_f2\)\n\s+layout_f2\.addRow\(calc_f2_btn\))',
        r'\1\n        self.f2_result = QLabel("—"); self.f2_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f2_result.setWordWrap(True)\n        layout_f2.addRow("Результат:", self.f2_result)',
        content
    )

    # Ф.3
    content = re.sub(
        r'(calc_f3_btn = QPushButton\("Рассчитать C древостоя \(Ф\. 3\)"\); calc_f3_btn\.clicked\.connect\(self\._calculate_f3\)\n\s+layout_f3\.addRow\(calc_f3_btn\))',
        r'\1\n        self.f3_result = QLabel("—"); self.f3_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f3_result.setWordWrap(True)\n        layout_f3.addRow("Результат:", self.f3_result)',
        content
    )

    # Ф.4
    content = re.sub(
        r'(calc_f4_btn = QPushButton\("Рассчитать C подроста \(Ф\. 4\)"\); calc_f4_btn\.clicked\.connect\(self\._calculate_f4\)\n\s+layout_f4\.addRow\(calc_f4_btn\))',
        r'\1\n        self.f4_result = QLabel("—"); self.f4_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f4_result.setWordWrap(True)\n        layout_f4.addRow("Результат:", self.f4_result)',
        content
    )

    # Ф.5
    content = re.sub(
        r'(calc_f5_btn = QPushButton\("Рассчитать C почвы \(Ф\. 5\)"\); calc_f5_btn\.clicked\.connect\(self\._calculate_f5\)\n\s+layout_f5\.addRow\(calc_f5_btn\))',
        r'\1\n        self.f5_result = QLabel("—"); self.f5_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f5_result.setWordWrap(True)\n        layout_f5.addRow("Результат:", self.f5_result)',
        content
    )

    # Ф.6
    content = re.sub(
        r'(calc_f6_btn = QPushButton\("Рассчитать выбросы от пожара \(Ф\. 6\)"\); calc_f6_btn\.clicked\.connect\(self\._calculate_f6\)\n\s+layout_f6\.addRow\(calc_f6_btn\))',
        r'\1\n        self.f6_result = QLabel("—"); self.f6_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f6_result.setWordWrap(True)\n        layout_f6.addRow("Результат:", self.f6_result)',
        content
    )

    # Ф.7
    content = re.sub(
        r'(calc_f7_btn = QPushButton\("Рассчитать CO2 \(Ф\. 7\)"\); calc_f7_btn\.clicked\.connect\(self\._calculate_f7\)\n\s+drain_layout\.addRow\(calc_f7_btn\))',
        r'\1\n        self.f7_result = QLabel("—"); self.f7_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f7_result.setWordWrap(True)\n        drain_layout.addRow("Результат:", self.f7_result)',
        content
    )

    # Ф.8
    content = re.sub(
        r'(calc_f8_btn = QPushButton\("Рассчитать N2O \(Ф\. 8\)"\); calc_f8_btn\.clicked\.connect\(self\._calculate_f8\)\n\s+drain_layout\.addRow\(calc_f8_btn\))',
        r'\1\n        self.f8_result = QLabel("—"); self.f8_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f8_result.setWordWrap(True)\n        drain_layout.addRow("Результат:", self.f8_result)',
        content
    )

    # Ф.9
    content = re.sub(
        r'(calc_f9_btn = QPushButton\("Рассчитать CH4 \(Ф\. 9\)"\); calc_f9_btn\.clicked\.connect\(self\._calculate_f9\)\n\s+drain_layout\.addRow\(calc_f9_btn\))',
        r'\1\n        self.f9_result = QLabel("—"); self.f9_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f9_result.setWordWrap(True)\n        drain_layout.addRow("Результат:", self.f9_result)',
        content
    )

    # Ф.10
    content = re.sub(
        r'(calc_f10_btn = QPushButton\("Рассчитать C_FUEL \(Ф\. 10\)"\)\n\s+calc_f10_btn\.clicked\.connect\(self\._calculate_f10\)\n\s+fuel_btn_layout\.addWidget\(add_fuel_btn\)\n\s+fuel_btn_layout\.addWidget\(remove_fuel_btn\)\n\s+fuel_btn_layout\.addWidget\(calc_f10_btn\)\n\s+fuel_layout\.addLayout\(fuel_btn_layout\))',
        r'\1\n        self.f10_result = QLabel("—"); self.f10_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f10_result.setWordWrap(True)\n        fuel_layout.addWidget(QLabel("Результат:")); fuel_layout.addWidget(self.f10_result)',
        content
    )

    # Ф.11
    content = re.sub(
        r'(calc_f11_btn = QPushButton\("Перевести ΔC в CO2 \(Ф\. 11\)"\); calc_f11_btn\.clicked\.connect\(self\._calculate_f11\))',
        r'\1\n        self.f11_result = QLabel("—"); self.f11_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f11_result.setWordWrap(True)\n        convert_layout.addRow(calc_f11_btn)\n        convert_layout.addRow("Результат Ф.11:", self.f11_result)',
        content
    )
    # Убираем двойное добавление кнопки
    content = re.sub(
        r'(self\.f11_result\.setWordWrap\(True\)\n\s+convert_layout\.addRow\(calc_f11_btn\)\n\s+convert_layout\.addRow\("Результат Ф\.11:", self\.f11_result\))\n\s+calc_f12_btn',
        r'\1\n        calc_f12_btn',
        content
    )

    # Ф.12
    content = re.sub(
        r'(calc_f12_btn = QPushButton\("Перевести в CO2-экв \(Ф\. 12\)"\); calc_f12_btn\.clicked\.connect\(self\._calculate_f12\))',
        r'\1\n        self.f12_result = QLabel("—"); self.f12_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f12_result.setWordWrap(True)\n        convert_layout.addRow(calc_f12_btn)\n        convert_layout.addRow("Результат Ф.12:", self.f12_result)',
        content
    )
    # Убираем двойное добавление кнопок
    content = re.sub(
        r'(self\.f12_result\.setWordWrap\(True\)\n\s+convert_layout\.addRow\(calc_f12_btn\)\n\s+convert_layout\.addRow\("Результат Ф\.12:", self\.f12_result\))\n\s+convert_layout\.addRow\(calc_f11_btn\)\n\s+convert_layout\.addRow\(calc_f12_btn\)',
        r'\1',
        content
    )

    # Теперь обновляем методы расчета, заменяя _append_result на установку текста в label
    # Читаем методы
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Найдем где начинаются методы расчета
    method_start = None
    for i, line in enumerate(lines):
        if 'def _calculate_f1(self):' in line:
            method_start = i
            break

    # Заменим весь раздел методов
    if method_start:
        # Сохраняем все до методов
        before_methods = ''.join(lines[:method_start])

        # Записываем новый файл с обновленными методами
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content[:content.find('def _calculate_f1(self):')])
            f.write('''    def _calculate_f1(self):
        try:
            biomass = get_float(self.f1_biomass, "ΔC биомасса")
            deadwood = get_float(self.f1_deadwood, "ΔC мертвая древесина")
            litter = get_float(self.f1_litter, "ΔC подстилка")
            soil = get_float(self.f1_soil, "ΔC почва")
            delta_c = self.calculator.calculate_carbon_stock_change(biomass, deadwood, litter, soil)
            co2_eq = delta_c * (-44/12)
            self.f1_result.setText(f"ΔC общее: {delta_c:.4f} т C/год\\nCO2-экв: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            logging.info(f"ForestRestorationTab: F1 calculated: {delta_c:.4f} t C/year")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 1")

    def _calculate_f2(self):
        try:
            c_after = get_float(self.f2_c_after, "C после")
            c_before = get_float(self.f2_c_before, "C до")
            area = get_float(self.f2_area, "Площадь")
            period = get_float(self.f2_period, "Период")
            delta_c = self.calculator.calculate_biomass_change(c_after, c_before, area, period)
            self.f2_result.setText(f"ΔC биомассы: {delta_c:.4f} т C/год")
            logging.info(f"ForestRestorationTab: F2 calculated: {delta_c:.4f} t C/year")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 2")

    def _calculate_f3(self):
        try:
            species = self.f3_species.currentText().lower()
            diameter = get_float(self.f3_diameter, "Диаметр")
            height = get_float(self.f3_height, "Высота")
            count = self.f3_count.value()
            carbon = self.calculator.calculate_tree_biomass(species, diameter, height)
            total_carbon = carbon * count
            self.f3_result.setText(f"C древостоя: {carbon:.4f} т C (на дерево)\\nВсего ({count} шт): {total_carbon:.4f} т C")
            logging.info(f"ForestRestorationTab: F3 calculated: {carbon:.4f} t C/tree")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 3")

    def _calculate_f4(self):
        try:
            heights_text = self.f4_heights.text().strip()
            if not heights_text:
                raise ValueError("Введите высоты через запятую")
            heights = [float(h.strip().replace(',', '.')) for h in heights_text.split(',')]
            species = self.f4_species.currentText().lower()
            carbon = self.calculator.calculate_undergrowth_biomass(species, heights)
            avg_height = sum(heights) / len(heights)
            self.f4_result.setText(f"C подроста: {carbon:.4f} т C\\n(N={len(heights)}, средн. высота={avg_height:.2f} м)")
            logging.info(f"ForestRestorationTab: F4 calculated: {carbon:.4f} t C")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 4")

    def _calculate_f5(self):
        try:
            org_percent = get_float(self.f5_org_percent, "Орг. вещество")
            depth_cm = get_float(self.f5_depth_cm, "Глубина")
            bulk_density = get_float(self.f5_bulk_density, "Объемная масса")
            carbon = self.calculator.calculate_soil_carbon(org_percent, depth_cm, bulk_density)
            self.f5_result.setText(f"C почвы: {carbon:.4f} т C/га")
            logging.info(f"ForestRestorationTab: F5 calculated: {carbon:.4f} t C/ha")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 5")

    def _calculate_f6(self):
        try:
            area = get_float(self.f6_area, "Площадь")
            fuel_mass = get_float(self.f6_fuel_mass, "Масса топлива")
            comb_factor = get_float(self.f6_comb_factor, "Коэф. сгорания")
            gas_type = self.f6_gas_type.currentText()
            emission = self.calculator.calculate_fire_emissions(area, fuel_mass, comb_factor, gas_type)
            gwp_factors = {"CO2": 1, "CH4": 28, "N2O": 265}
            co2_eq = emission * gwp_factors.get(gas_type, 1)
            self.f6_result.setText(f"Выбросы {gas_type}: {emission:.4f} т\\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ForestRestorationTab: F6 calculated: {emission:.4f} t {gas_type}")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 6")

    def _calculate_f7(self):
        try:
            area = get_float(self.drain_area, "Площадь")
            ef = get_float(self.f7_ef, "Коэф. выброса")
            co2_emission = self.calculator.calculate_drained_soil_co2(area, ef)
            self.f7_result.setText(f"CO2 от осушения: {co2_emission:.4f} т CO2/год")
            logging.info(f"ForestRestorationTab: F7 calculated: {co2_emission:.4f} t CO2/year")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 7")

    def _calculate_f8(self):
        try:
            area = get_float(self.drain_area, "Площадь")
            ef = get_float(self.f8_ef, "Коэф. выброса N2O")
            n2o_emission = self.calculator.calculate_drained_soil_n2o(area, ef)
            co2_eq = n2o_emission * 265
            self.f8_result.setText(f"N2O от осушения: {n2o_emission:.6f} т N2O/год\\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ForestRestorationTab: F8 calculated: {n2o_emission:.6f} t N2O/year")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 8")

    def _calculate_f9(self):
        try:
            area = get_float(self.drain_area, "Площадь")
            frac_ditch = get_float(self.f9_frac_ditch, "Доля канав")
            ef_land = get_float(self.f9_ef_land, "EF_land CH4")
            ef_ditch = get_float(self.f9_ef_ditch, "EF_ditch CH4")
            ch4_emission_kg = self.calculator.calculate_drained_soil_ch4(area, frac_ditch, ef_land, ef_ditch)
            ch4_emission_t = ch4_emission_kg / 1000.0
            co2_eq = ch4_emission_t * 28
            self.f9_result.setText(f"CH4 от осушения: {ch4_emission_t:.6f} т CH4/год ({ch4_emission_kg:.3f} кг/год)\\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ForestRestorationTab: F9 calculated: {ch4_emission_t:.6f} t CH4/year")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 9")

    def _calculate_f10(self):
        try:
            fuel_data = []
            for row in range(self.f10_table.rowCount()):
                fuel_name_item = self.f10_table.item(row, 0)
                volume_item = self.f10_table.item(row, 1)
                ef_item = self.f10_table.item(row, 2)

                if fuel_name_item and volume_item and ef_item:
                    fuel_name = fuel_name_item.text().strip()
                    if fuel_name:
                        volume = float(volume_item.text().replace(',', '.'))
                        ef = float(ef_item.text().replace(',', '.'))
                        fuel_data.append((volume, ef))

            if not fuel_data:
                raise ValueError("Добавьте хотя бы один вид топлива с данными")

            c_fuel = self.calculator.calculate_fossil_fuel_emissions(fuel_data)
            result_text = f"C_FUEL: {c_fuel:.4f} т C\\n\\nРазбивка по топливу:\\n"
            for i, (volume, ef) in enumerate(fuel_data, 1):
                contrib = volume * ef
                result_text += f"  Топливо {i}: {contrib:.4f} т C\\n"

            self.f10_result.setText(result_text)
            logging.info(f"ForestRestorationTab: F10 calculated: {c_fuel:.4f} t C")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 10")

    def _calculate_f11(self):
        try:
            carbon = get_float(self.f11_carbon, "ΔC")
            co2_eq = self.calculator.carbon_to_co2_conversion(carbon)
            self.f11_result.setText(f"CO2: {co2_eq:.4f} т CO2")
            logging.info(f"ForestRestorationTab: F11 calculated: {co2_eq:.4f} t CO2")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 11")

    def _calculate_f12(self):
        try:
            gas_amount = get_float(self.f12_gas_amount, "Кол-во газа")
            gas_type = self.f12_gas_type.currentText()
            co2_eq = self.calculator.ghg_to_co2_equivalent(gas_amount, gas_type)
            self.f12_result.setText(f"CO2-экв: {co2_eq:.4f} т CO2-экв")
            logging.info(f"ForestRestorationTab: F12 calculated: {co2_eq:.4f} t CO2eq")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 12")

    def get_summary_data(self) -> Dict[str, float]:
        """Собирает данные для сводного отчета."""
        data = {
            'absorption_c': 0.0,
            'emission_co2': 0.0,
            'emission_ch4': 0.0,
            'emission_n2o': 0.0,
            'details': ''
        }
        details = "Лесовосстановление:\\n"

        try:
            if hasattr(self, 'f2_c_after') and self.f2_c_after.text() and self.f2_c_before.text():
                c_after = float(self.f2_c_after.text().replace(',', '.'))
                c_before = float(self.f2_c_before.text().replace(',', '.'))
                area = float(self.f2_area.text().replace(',', '.')) if self.f2_area.text() else 0
                period = float(self.f2_period.text().replace(',', '.')) if self.f2_period.text() else 1
                delta_c = (c_after - c_before) * area / period
                if delta_c < 0:
                    data['absorption_c'] += abs(delta_c)
                details += f"  - Изменение C в биомассе: {delta_c:.2f} т C/год\\n"
        except:
            details += "  - Данные Ф. 2 не заполнены\\n"

        data['details'] = details
        return data
''')

    print("✅ forest_restoration_tab.py исправлен")

if __name__ == "__main__":
    print("Исправление расположения результатов в absorption tabs...")
    fix_forest_restoration_tab()
    print("\\nГотово!")
