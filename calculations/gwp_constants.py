# calculations/gwp_constants.py
"""
Потенциалы глобального потепления (GWP) для парниковых газов.
Согласно Fifth Assessment Report (AR5) IPCC, 2014.

Период оценки: 100 лет

Источник: IPCC Fifth Assessment Report: Climate Change 2013
The Physical Science Basis, Chapter 8, Table 8.7
"""

# Основные потенциалы глобального потепления (GWP) за 100 лет
# Используются в расчетах поглощения и выбросов парниковых газов
GWP_AR5_100Y = {
    "CO2": 1,  # Диоксид углерода (базовое значение)
    "CH4": 28,  # Метан (было 25 в AR4)
    "N2O": 265,  # Закись азота (было 298 в AR4)
    "CF4": 7390,  # Тетрафторметан
    "C2F6": 12200,  # Гексафторэтан
    "SF6": 23500,  # Гексафторид серы
    "CHF3": 14800,  # Трифторметан (HFC-23)
}

# Для обратной совместимости
GWP_VALUES = GWP_AR5_100Y

# Коэффициенты перевода масс
CARBON_TO_CO2_RATIO = 44 / 12  # Молярная масса CO2 / масса C
NITROGEN_TO_N2O_RATIO = 44 / 28  # Молярная масса N2O / масса N2

# Справочная информация
GWP_INFO = {
    "source": "IPCC AR5 (2014)",
    "time_horizon": "100 years",
    "reference": "https://www.ipcc.ch/report/ar5/wg1/",
    "table": "Chapter 8, Table 8.7",
}

# Сравнение с предыдущими отчетами IPCC
GWP_COMPARISON = {
    "AR4_2007": {"CH4": 25, "N2O": 298},
    "AR5_2014": {"CH4": 28, "N2O": 265},
    "AR6_2021": {"CH4": 27.9, "N2O": 273},
}


def get_co2_equivalent(gas_amount: float, gas_type: str) -> float:
    """
    Переводит количество газа в CO2-эквивалент.

    :param gas_amount: Масса газа, тонн
    :param gas_type: Тип газа (CO2, CH4, N2O, и т.д.)
    :return: CO2-эквивалент, тонн
    :raises ValueError: Если тип газа неизвестен
    """
    if gas_type not in GWP_VALUES:
        raise ValueError(
            f"Неизвестный тип газа: '{gas_type}'. "
            f"Доступные: {', '.join(GWP_VALUES.keys())}"
        )

    return gas_amount * GWP_VALUES[gas_type]


def carbon_to_co2(carbon_mass: float, absorption: bool = True) -> float:
    """
    Переводит массу углерода в массу CO2.

    :param carbon_mass: Масса углерода, тонн
    :param absorption: True для поглощения (отрицательные выбросы),
                      False для выбросов (положительные)
    :return: Масса CO2, тонн (отрицательная при поглощении)
    """
    sign = -1 if absorption else 1
    return carbon_mass * CARBON_TO_CO2_RATIO * sign


def nitrogen_to_n2o(nitrogen_mass: float) -> float:
    """
    Переводит массу азота в массу N2O.

    :param nitrogen_mass: Масса N (азота), тонн
    :return: Масса N2O, тонн
    """
    return nitrogen_mass * NITROGEN_TO_N2O_RATIO


if __name__ == "__main__":
    # Примеры использования
    print("=== ПОТЕНЦИАЛЫ ГЛОБАЛЬНОГО ПОТЕПЛЕНИЯ (GWP) ===")
    print(f"Источник: {GWP_INFO['source']}")
    print(f"Период: {GWP_INFO['time_horizon']}\n")

    for gas, gwp in GWP_VALUES.items():
        print(f"{gas:8s}: GWP = {gwp:>6}")

    print("\n=== ПРИМЕРЫ РАСЧЕТОВ ===")

    # Пример 1: Поглощение углерода
    print("\n1. Поглощение 100 тонн углерода:")
    co2_absorbed = carbon_to_co2(100, absorption=True)
    print(f"   CO2 удалено из атмосферы: {co2_absorbed:.2f} т CO2")

    # Пример 2: Выбросы метана
    print("\n2. Выброс 10 тонн метана:")
    ch4_co2eq = get_co2_equivalent(10, "CH4")
    print(f"   CO2-эквивалент: {ch4_co2eq:.2f} т CO2-экв")

    # Пример 3: Выбросы N2O
    print("\n3. Выброс 5 тонн N2O:")
    n2o_co2eq = get_co2_equivalent(5, "N2O")
    print(f"   CO2-эквивалент: {n2o_co2eq:.2f} т CO2-экв")
