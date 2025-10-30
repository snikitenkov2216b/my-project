# ui/tab_config.py
"""
Конфигурация вкладок для оптимизированной загрузки.
Позволяет централизованно управлять структурой приложения.
"""

# Конфигурация вкладок выбросов
EMISSION_TABS_CONFIG = [
    # (номер_категории, заголовок_вкладки)
    (0, "0️⃣ Расход ресурсов"),
    (1, "1️⃣ Стац. сжигание"),
    (2, "2️⃣ Факелы"),
    (3, "3️⃣ Фугитивные"),
    (4, "4️⃣ Нефтепереработка"),
    (5, "5️⃣ Производство кокса"),
    (6, "6️⃣ Цемент"),
    (7, "7️⃣ Известь"),
    (8, "8️⃣ Стекло"),
    (9, "9️⃣ Керамика"),
    (10, "🔟 Аммиак"),
    (11, "1️⃣1️⃣ Хим. N2O"),
    (12, "1️⃣2️⃣ Нефтехимия"),
    (13, "1️⃣3️⃣ Фторсодержащие"),
    (14, "1️⃣4️⃣ Черная металлургия"),
    (15, "1️⃣5️⃣ Ферросплавы"),
    (16, "1️⃣6️⃣ Алюминий"),
    (17, "1️⃣7️⃣ Прочие процессы"),
    (18, "1️⃣8️⃣ Транспорт"),
    (19, "1️⃣9️⃣ Дор. хозяйство"),
    (20, "2️⃣0️⃣ Захоронение отходов"),
    (21, "2️⃣1️⃣ Био. переработка"),
    (22, "2️⃣2️⃣ Сжигание отходов"),
    (23, "2️⃣3️⃣ Сточные воды"),
    (24, "2️⃣4️⃣ N2O из стоков"),
]

# Конфигурация вкладок поглощения
ABSORPTION_TABS_CONFIG = [
    # (тип_калькулятора, заголовок_вкладки, модуль_вкладки, класс_вкладки)
    ("ForestRestoration", "🌱 Лесовосстановление", "ui.forest_restoration_tab", "ForestRestorationTab"),
    ("PermanentForest", "🌲 Постоянные леса", "ui.permanent_forest_tab", "PermanentForestTab"),
    ("ProtectiveForest", "🌳 Защитные насаждения", "ui.protective_forest_tab", "ProtectiveForestTab"),
    ("AgriculturalLand", "🌾 Сельхозугодья", "ui.agricultural_absorption_tab", "AgriculturalAbsorptionTab"),
    ("LandReclamation", "♻️ Рекультивация", "ui.land_reclamation_tab", "LandReclamationTab"),
    ("LandConversion", "🔄 Конверсия земель", "ui.land_conversion_tab", "LandConversionTab"),
]


def get_emission_tab_class(category_num):
    """
    Динамически загружает класс вкладки для категории выбросов.

    Args:
        category_num: Номер категории (0-24)

    Returns:
        class: Класс вкладки или None при ошибке
    """
    try:
        module = __import__(f"ui.category_{category_num}_tab", fromlist=[f"Category{category_num}Tab"])
        return getattr(module, f"Category{category_num}Tab")
    except (ImportError, AttributeError):
        return None


def get_absorption_tab_class(module_name, class_name):
    """
    Динамически загружает класс вкладки для поглощения.

    Args:
        module_name: Имя модуля
        class_name: Имя класса

    Returns:
        class: Класс вкладки или None при ошибке
    """
    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        return None
