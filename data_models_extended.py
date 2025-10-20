# data_models_extended.py
"""
Расширение DataService с таблицами из Приказа Минприроды РФ от 27.05.2022 N 371
для расчета поглощения парниковых газов.
"""
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class RegionalForestData:
    """Данные по лесам для субъектов РФ."""
    region: str
    # Покрытые лесом земли
    above_biomass: float  # Надземная биомасса, т C/га
    below_biomass: float  # Подземная биомасса, т C/га
    deadwood: float  # Мертвое органическое вещество, т C/га
    litter: float  # Подстилка, т C/га
    soil: float  # Почва, т C/га
    # Кустарниковая растительность
    shrub_above: float  # Надземная биомасса кустарников, т C/га
    shrub_below: float  # Подземная биомасса кустарников, т C/га
    shrub_deadwood: float  # Мертвое органическое вещество, т C/га
    shrub_litter: float  # Подстилка, т C/га
    shrub_soil: float  # Почва под кустарниками, т C/га


class ExtendedDataService:
    """Расширенный сервис данных с таблицами для поглощения ПГ."""
    
    def __init__(self):
        self._init_forest_coefficients()
        self._init_regional_data()
        self._init_emission_factors()
        self._init_agricultural_data()
        
    def _init_forest_coefficients(self):
        """Инициализация коэффициентов для лесных расчетов."""
        
        # Таблица 24: Коэффициенты аллометрических уравнений
        self.allometric_coefficients = {
            'ель': {
                'надземная': {'a': 0.0533, 'b': 0.8955},
                'корни': {'a': 0.0239, 'b': 0.8408},
                'всего': {'a': 0.1237, 'b': 0.8332}
            },
            'сосна': {
                'надземная': {'a': 0.0217, 'b': 0.9817},
                'корни': {'a': 0.0387, 'b': 0.7281},
                'всего': {'a': 0.0557, 'b': 0.9031}
            },
            'береза': {
                'надземная': {'a': 0.5443, 'b': 0.6527},
                'корни': {'a': 0.0387, 'b': 0.7281},
                'всего': {'a': 0.0557, 'b': 0.9031}
            }
        }
        
        # Таблица 24.2: Коэффициенты выбросов при пожарах
        self.fire_emission_factors = {
            'леса': {
                'CO2': 1569.0,  # г/кг сжигаемого вещества
                'CH4': 4.7,
                'N2O': 0.26
            },
            'сельхоз_остатки': {
                'CO2': 1515.0,
                'CH4': 2.7,
                'N2O': 0.07
            },
            'кормовые_угодья': {
                'CO2': 1613.0,
                'CH4': 2.3,
                'N2O': 0.21
            }
        }
        
        # Таблица 25.6: Масса доступного топлива для пожаров
        self.fuel_mass_forest = {
            'покрытые_лесом': {
                'биомасса': 87.9,
                'мертвая_древесина': 17.4,
                'подстилка': 16.1,
                'всего': 121.4
            },
            'непокрытые_лесом': {
                'биомасса': 10.4,
                'мертвая_древесина': 1.1,
                'подстилка': 10.9,
                'всего': 22.4
            }
        }
        
    def _init_regional_data(self):
        """Инициализация региональных данных по субъектам РФ."""
        
        # Таблица 27.8: Средние величины запасов углерода по регионам
        self.regional_carbon_stocks = {
            'Республика Адыгея': RegionalForestData(
                region='Республика Адыгея',
                above_biomass=74.02, below_biomass=20.86, deadwood=14.35,
                litter=5.51, soil=54.08, shrub_above=0.0, shrub_below=0.0,
                shrub_deadwood=0.0, shrub_litter=0.0, shrub_soil=49.84
            ),
            'Республика Алтай': RegionalForestData(
                region='Республика Алтай',
                above_biomass=55.08, below_biomass=16.05, deadwood=10.94,
                litter=5.06, soil=100.53, shrub_above=1.94, shrub_below=0.52,
                shrub_deadwood=0.09, shrub_litter=6.66, shrub_soil=96.54
            ),
            'Республика Башкортостан': RegionalForestData(
                region='Республика Башкортостан',
                above_biomass=43.87, below_biomass=11.03, deadwood=10.02,
                litter=6.56, soil=69.49, shrub_above=5.10, shrub_below=1.36,
                shrub_deadwood=0.31, shrub_litter=6.68, shrub_soil=65.26
            ),
            'Республика Бурятия': RegionalForestData(
                region='Республика Бурятия',
                above_biomass=37.09, below_biomass=7.33, deadwood=9.73,
                litter=6.47, soil=93.24, shrub_above=7.27, shrub_below=11.07,
                shrub_deadwood=4.05, shrub_litter=3.92, shrub_soil=88.75
            ),
            # Добавить остальные регионы...
        }
        
        # Таблица 27.3: Продуктивность сенокосов и пастбищ по регионам
        self.grassland_productivity = {
            'Республика Адыгея': {'productivity': 5.0, 'carbon_accumulation': 3660},
            'Республика Алтай': {'productivity': 2.5, 'carbon_accumulation': 1830},
            'Республика Башкортостан': {'productivity': 4.0, 'carbon_accumulation': 2928},
            'Республика Бурятия': {'productivity': 3.0, 'carbon_accumulation': 2196},
            'Республика Дагестан': {'productivity': 4.5, 'carbon_accumulation': 3294},
            # Добавить остальные регионы...
        }
        
    def _init_emission_factors(self):
        """Инициализация коэффициентов выбросов."""
        
        # Коэффициенты выбросов от осушенных почв
        self.drained_soil_factors = {
            'лесные_земли': {
                'CO2': 0.71,  # т C/га/год
                'N2O': 1.71,  # кг N/га/год
                'CH4_frac_ditch': 0.025,
                'CH4_ef_land': 4.5,  # кг CH4/га/год
                'CH4_ef_ditch': 217  # кг CH4/га/год
            },
            'пахотные_земли': {
                'CO2': 5.9,  # т C/га/год
                'N2O': 7.0,  # кг N-N2O/га/год
                'CH4_frac_ditch': 0.5,
                'CH4_ef_land': 0.0,
                'CH4_ef_ditch': 1165
            },
            'кормовые_угодья': {
                'CO2': 5.82,  # т C/га/год
                'N2O': 9.5,  # кг N-N2O/га/год
                'CH4_frac_ditch': 0.05,
                'CH4_ef_land': 1.4,
                'CH4_ef_ditch': 43.63
            }
        }
        
    def _init_agricultural_data(self):
        """Инициализация данных для сельскохозяйственных расчетов."""
        
        # Таблица 26.1: Содержание углерода в органических удобрениях
        self.organic_fertilizer_carbon = {
            'навоз': 8.07,  # % сырого вещества
            'навоз_подстилочный': 12.07,
            'навоз_бесподстилочный': 4.08,
            'торф': 23.56,
            'помет': 19.11,
            'солома_сидераты': 22.23
        }
        
        # Таблица 26.2: Коэффициенты углерода в минеральных удобрениях
        self.mineral_fertilizer_carbon = {
            'азотные': 0.13,
            'фосфорные': 0.015,
            'калийные': 0.017
        }
        
        # Таблица 26.3: Уравнения для расчета углерода растительных остатков
        self.crop_residue_equations = {
            'озимая_рожь': {
                '10-25': {'above': (0.3, 3.2), 'below': (0.6, 8.9), 'carbon': 0.45},
                '26-40': {'above': (0.2, 6.3), 'below': (0.6, 13.9), 'carbon': 0.45}
            },
            'озимая_пшеница': {
                '10-25': {'above': (0.4, 2.6), 'below': (0.9, 5.8), 'carbon': 0.4853},
                '26-40': {'above': (0.1, 8.9), 'below': (0.7, 10.0), 'carbon': 0.4853}
            },
            'яровая_пшеница': {
                '10-20': {'above': (0.4, 1.8), 'below': (0.7, 10.2), 'carbon': 0.4853},
                '21-30': {'above': (0.2, 5.4), 'below': (0.8, 6.0), 'carbon': 0.4853}
            },
            'ячмень': {
                '10-20': {'above': (0.4, 1.8), 'below': (0.8, 6.5), 'carbon': 0.4567},
                '21-35': {'above': (0.09, 7.6), 'below': (0.4, 13.45), 'carbon': 0.4567}
            },
            # Добавить остальные культуры...
        }
        
        # Таблица 27.1: Коэффициенты для оценки поступления углерода с навозом
        self.livestock_carbon_factors = {
            'коровы': {
                'excretion': 244.6,  # кг C/голова/год
                'ch4': 5.07,
                'co2': 3.38,
                'grazing_time': 19.2  # %
            },
            'крс_без_коров': {
                'excretion': 115.9,
                'ch4': 3.04,
                'co2': 2.02,
                'grazing_time': 24.8
            },
            'овцы': {
                'excretion': 36.9,
                'ch4': 0.19,
                'co2': 0.13,
                'grazing_time': 18.4
            },
            'козы': {
                'excretion': 23.3,
                'ch4': 0.13,
                'co2': 0.09,
                'grazing_time': 18.4
            },
            'лошади': {
                'excretion': 156.6,
                'ch4': 1.56,
                'co2': 1.04,
                'grazing_time': 18.4
            },
            # Добавить остальных животных...
        }
        
        # Таблица 27.2: Эмиссия CO2 от дыхания почв
        self.soil_respiration_rates = {
            'среднее_луговые': 445,  # мг CO2/м²/час
            'дерново_подзолистая': 200,
            'торфяная': 937,
            'мерзлотно_луговая': 600,
            'серая_лесная': 385,
            'чернозем': 280,
            'чернозем_обыкновенный': 359
        }
        
    def get_allometric_coefficients(
        self,
        species: str,
        fraction: str = 'всего'
    ) -> Optional[Dict[str, float]]:
        """Получить коэффициенты аллометрических уравнений."""
        species_data = self.allometric_coefficients.get(species.lower())
        if species_data:
            return species_data.get(fraction)
        return None
    
    def get_fire_emission_factor(
        self,
        land_type: str,
        gas_type: str
    ) -> Optional[float]:
        """Получить коэффициент выбросов при пожарах."""
        land_data = self.fire_emission_factors.get(land_type)
        if land_data:
            return land_data.get(gas_type)
        return None
    
    def get_regional_carbon_stocks(
        self,
        region: str
    ) -> Optional[RegionalForestData]:
        """Получить данные по запасам углерода для региона."""
        return self.regional_carbon_stocks.get(region)
    
    def get_drained_soil_factors(
        self,
        land_type: str
    ) -> Optional[Dict[str, float]]:
        """Получить коэффициенты выбросов от осушенных почв."""
        return self.drained_soil_factors.get(land_type)
    
    def get_organic_fertilizer_carbon(
        self,
        fertilizer_type: str
    ) -> Optional[float]:
        """Получить содержание углерода в органическом удобрении."""
        return self.organic_fertilizer_carbon.get(fertilizer_type)
    
    def get_crop_residue_coefficients(
        self,
        crop: str,
        yield_range: str
    ) -> Optional[Dict]:
        """Получить коэффициенты для расчета углерода растительных остатков."""
        crop_data = self.crop_residue_equations.get(crop)
        if crop_data:
            return crop_data.get(yield_range)
        return None
    
    def get_livestock_carbon_factors(
        self,
        animal_type: str
    ) -> Optional[Dict[str, float]]:
        """Получить коэффициенты углерода для животных."""
        return self.livestock_carbon_factors.get(animal_type)
    
    def get_soil_respiration_rate(
        self,
        soil_type: str = 'среднее_луговые'
    ) -> float:
        """Получить скорость дыхания почвы."""
        return self.soil_respiration_rates.get(soil_type, 445)
    
    def get_grassland_productivity(
        self,
        region: str
    ) -> Optional[Dict[str, float]]:
        """Получить продуктивность кормовых угодий по региону."""
        return self.grassland_productivity.get(region)