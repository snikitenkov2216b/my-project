# calculations/category_16.py - Модуль для расчетов по Категории 16.
# Инкапсулирует бизнес-логику для производства первичного алюминия.
# Код обновлен для полной реализации всех формул (16.1 - 16.22) из методики.
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
        :return: Словарь с общими выбросами CF4 и C2F6 в тоннах.
        """
        tech_data = self.data_service.get_aluminium_tech_data_table_16_1(technology)
        if not tech_data:
            raise ValueError(f"Данные для технологии '{technology}' не найдены в таблице 16.1.")

        s_cf4 = tech_data['S_CF4']
        f_c2f6_cf4 = tech_data['F_C2F6_CF4']

        # Формула 16.4: AEM = AEF * AED
        aem = aef * aed

        # Формула 16.2: E_CF4 (удельный) = S_CF4 * AEM / 1000
        e_cf4_specific = s_cf4 * aem / 1000
        
        # Формула 16.3: E_C2F6 (удельный) = E_CF4 * F_C2F6/CF4
        e_c2f6_specific = e_cf4_specific * f_c2f6_cf4

        # Формула 16.1 (часть): Общие выбросы = Удельные выбросы * Производство
        total_cf4 = e_cf4_specific * aluminium_production
        total_c2f6 = e_c2f6_specific * aluminium_production

        return {'cf4': total_cf4, 'c2f6': total_c2f6}

    def calculate_soderberg_co2_emissions(self, 
                                          anode_paste_consumption: float, 
                                          h_content: float, 
                                          s_content: float, 
                                          z_content: float,
                                          # Параметры для детализированного расчета потерь (опционально)
                                          tar_loss_params: dict = None,
                                          dust_loss_params: dict = None,
                                          foam_loss_params: dict = None,
                                          wet_scrubbing_params: dict = None
                                          ) -> float:
        """
        Рассчитывает удельные выбросы CO2 от электролизеров Содерберга.
        Реализует формулу 16.6 и связанные с ней (16.7 - 16.16).
        """
        # Формула 16.7: Потери анодной массы с водородом
        m_am_h = anode_paste_consumption * (h_content / 100)

        # Формула 16.8: Потери анодной массы с серой и золой
        m_am_sz = anode_paste_consumption * ((s_content + z_content) / 100)
        
        # Расчет детализированных потерь углерода, если данные предоставлены
        m_c_tar = 0.0
        if tar_loss_params:
            # Формулы 16.9, 16.10, 16.11
            p_sm_r = tar_loss_params['p_sm_r']
            w_c_sm = tar_loss_params['w_c_sm'] / 100
            eta_k = tar_loss_params.get('eta_k', 0.0)
            p_sm_psh = tar_loss_params.get('p_sm_psh', 0.0) # Потери при перестановке штырей
            
            p_sm_f = (1 - eta_k) * p_sm_r + p_sm_psh
            
            if tar_loss_params.get('has_wet_scrubber', False):
                 m_c_tar = (p_sm_f / 1000 * w_c_sm) + (p_sm_r / 1000 * w_c_sm)
            else: # Сухая газоочистка
                 m_c_tar = (p_sm_f / 1000) * w_c_sm

        m_c_dust = 0.0
        if dust_loss_params:
            # Формулы 16.12, 16.13, 16.14
            p_pyl_r = dust_loss_params['p_pyl_r']
            w_c_pyl = dust_loss_params['w_c_pyl'] / 100
            eta_k = dust_loss_params.get('eta_k', 0.0)
            
            p_pyl_f = (1 - eta_k) * p_pyl_r
            
            if dust_loss_params.get('has_wet_scrubber', False):
                m_c_dust = (p_pyl_f / 1000 * w_c_pyl) + (p_pyl_r / 1000 * w_c_pyl)
            else: # Сухая газоочистка
                m_c_dust = (p_pyl_f / 1000) * w_c_pyl

        m_c_foam = 0.0
        if foam_loss_params:
            # Формула 16.15
            p_pena_vyh = foam_loss_params['p_pena_vyh']
            w_c_pena = foam_loss_params['w_c_pena'] / 100
            m_c_foam = (p_pena_vyh / 1000) * w_c_pena

        e_co2_mo = 0.0
        if wet_scrubbing_params:
            # Формула 16.16
            p_so2 = wet_scrubbing_params['p_so2']
            eta_so2 = wet_scrubbing_params['eta_so2']
            e_co2_mo = (p_so2 / 1000) * eta_so2 * (44 / 64)

        # Формула 16.6
        e_co2_sodb = (anode_paste_consumption - m_am_h - m_am_sz - m_c_tar - m_c_dust - m_c_foam) * self.CARBON_TO_CO2_FACTOR + e_co2_mo
        
        return e_co2_sodb

    def calculate_prebaked_anode_co2_emissions(self, anode_consumption: float, s_content: float, z_content: float, dust_loss_params: dict = None, foam_loss_params: dict = None) -> float:
        """
        Рассчитывает удельные выбросы CO2 от электролизеров с обожженными анодами (ОА).
        Реализует формулу 16.18 и связанные (16.19, 16.20).
        """
        m_c_dust = 0.0
        if dust_loss_params:
            # Формула 16.19 (аналогична 16.14)
             p_pyl_f = dust_loss_params['p_pyl_f']
             w_c_pyl = dust_loss_params['w_c_pyl'] / 100
             m_c_dust = (p_pyl_f / 1000) * w_c_pyl

        m_c_foam = 0.0
        if foam_loss_params:
            # Формула 16.20 (аналогична 16.15)
            p_pena_vyh = foam_loss_params['p_pena_vyh']
            w_c_pena = foam_loss_params['w_c_pena'] / 100
            m_c_foam = (p_pena_vyh / 1000) * w_c_pena
            
        # Формула 16.18
        e_co2_oa = (anode_consumption * (100 - s_content - z_content) / 100 - m_c_dust - m_c_foam) * self.CARBON_TO_CO2_FACTOR
        
        return e_co2_oa

    def calculate_coke_calcination_co2(self, raw_coke_consumption: float, coke_loss_factor: float, carbon_content: float) -> float:
        """
        Рассчитывает выбросы CO2 от угара при прокалке кокса.
        Реализует формулу 16.21.
        """
        e_co2_kp = (raw_coke_consumption * coke_loss_factor / 100) * (carbon_content / 100) * self.CARBON_TO_CO2_FACTOR
        return e_co2_kp
        
    def calculate_green_anode_baking_co2(self, green_anode_production: float) -> float:
        """
        Рассчитывает выбросы CO2 от обжига "зеленых" анодов.
        Реализует формулу 16.22.
        """
        m_co2_obzh = green_anode_production * 0.066 * self.CARBON_TO_CO2_FACTOR
        return m_co2_obzh