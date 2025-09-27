# calculations/category_16.py - Модуль для расчетов по Категории 16.
# Инкапсулирует бизнес-логику для производства первичного алюминия.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category16Calculator:
    """
    Класс-калькулятор для категории 16: "Производство первичного алюминия".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service
        self.CARBON_TO_CO2_FACTOR = 44 / 12

    def calculate_pfc_emissions(self, technology: str, aluminium_production: float, aef: float, aed: float) -> dict:
        """
        Рассчитывает выбросы перфторуглеродов (CF4 и C2F6).
        
        Реализует формулы 16.1 - 16.4 из методических указаний.

        :param technology: Тип технологии (CWPB, VSS, HSS).
        :param aluminium_production: Выпуск алюминия, т/год.
        :param aef: Средняя частота анодных эффектов, шт./ванно-сутки.
        :param aed: Средняя продолжительность анодных эффектов, минут/шт.
        :return: Словарь с выбросами CF4 и C2F6 в тоннах.
        """
        tech_data = self.data_service.get_aluminium_tech_data_table_16_1(technology)
        if not tech_data:
            raise ValueError(f"Данные для технологии '{technology}' не найдены в таблице 16.1.")

        s_cf4 = tech_data['S_CF4']
        f_c2f6_cf4 = tech_data['F_C2F6_CF4']

        # Формула 16.4: AEM = AEF * AED
        aem = aef * aed

        # Формула 16.2: E_CF4 = S_CF4 * AEM / 1000 (удельный выброс в т/т Al)
        e_cf4_specific = s_cf4 * aem / 1000
        
        # Формула 16.3: E_C2F6 = E_CF4 * F_C2F6/CF4 (удельный выброс в т/т Al)
        e_c2f6_specific = e_cf4_specific * f_c2f6_cf4

        # Общие выбросы
        total_cf4 = e_cf4_specific * aluminium_production
        total_c2f6 = e_c2f6_specific * aluminium_production

        return {'cf4': total_cf4, 'c2f6': total_c2f6}

    def calculate_soderberg_co2_emissions(self, anode_paste_consumption: float, h_content: float, s_content: float, z_content: float) -> float:
        """
        Рассчитывает удельные выбросы CO2 от электролизеров Содерберга.
        
        Реализует основную часть формулы 16.6. 
        Для упрощения, потери со смолистыми веществами, пылью, пеной и от мокрой очистки не учитываются.

        :param anode_paste_consumption: Расход анодной массы, т/т Ал.
        :param h_content: Содержание водорода в анодной массе, %.
        :param s_content: Содержание серы в анодной массе, %.
        :param z_content: Содержание золы в анодной массе, %.
        :return: Удельные выбросы CO2, т CO2/т Ал.
        """
        # Формула 16.7: Потери анодной массы с водородом
        m_am_h = anode_paste_consumption * (h_content / 100)

        # Формула 16.8: Потери анодной массы с серой и золой
        m_am_sz = anode_paste_consumption * ((s_content + z_content) / 100)
        
        # Упрощенная формула 16.6
        e_co2_sodb = (anode_paste_consumption - m_am_h - m_am_sz) * self.CARBON_TO_CO2_FACTOR
        
        return e_co2_sodb

    def calculate_prebaked_anode_co2_emissions(self, anode_consumption: float, s_content: float, z_content: float) -> float:
        """
        Рассчитывает удельные выбросы CO2 от электролизеров с обожженными анодами (ОА).
        
        Реализует основную часть формулы 16.18.
        Для упрощения, потери с пылью и пеной не учитываются.

        :param anode_consumption: Расход обожженных анодов нетто, т/т Ал.
        :param s_content: Содержание серы в обожженном аноде, %.
        :param z_content: Содержание золы в обожженном аноде, %.
        :return: Удельные выбросы CO2, т CO2/т Ал.
        """
        # Упрощенная формула 16.18
        e_co2_oa = (anode_consumption * (100 - s_content - z_content) / 100) * self.CARBON_TO_CO2_FACTOR
        
        return e_co2_oa

    def calculate_coke_calcination_co2(self, raw_coke_consumption: float, coke_loss_factor: float, carbon_content: float) -> float:
        """
        Рассчитывает выбросы CO2 от угара при прокалке кокса.
        
        Реализует формулу 16.21.

        :param raw_coke_consumption: Расход сырого кокса, т/год.
        :param coke_loss_factor: Угар кокса, %.
        :param carbon_content: Содержание углерода в коксе, %.
        :return: Выбросы CO2, т/год.
        """
        e_co2_kp = (raw_coke_consumption * coke_loss_factor / 100) * (carbon_content / 100) * self.CARBON_TO_CO2_FACTOR
        return e_co2_kp
        
    def calculate_green_anode_baking_co2(self, green_anode_production: float) -> float:
        """
        Рассчитывает выбросы CO2 от обжига "зеленых" анодов.
        
        Реализует формулу 16.22.

        :param green_anode_production: Объем производства "зеленых" анодов, т/год.
        :return: Выбросы CO2, т/год.
        """
        # Коэффициент 0.066 учитывает потери летучих, смолистых и т.д.
        m_co2_obzh = green_anode_production * 0.066 * self.CARBON_TO_CO2_FACTOR
        return m_co2_obzh