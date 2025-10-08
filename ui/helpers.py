# ui/helpers.py
"""
Вспомогательные виджеты и функции для улучшения UI.
Комментарии на русском. Поддержка UTF-8.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor


class SectionHeader(QLabel):
    """Заголовок секции с улучшенным стилем."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.setStyleSheet("""
            QLabel {
                color: #1976D2;
                padding: 8px;
                background-color: #E3F2FD;
                border-left: 4px solid #1976D2;
                border-radius: 3px;
            }
        """)


class InfoBox(QGroupBox):
    """Информационный блок с подсказкой."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout(self)
        
        info_label = QLabel(message)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #455A64;
                padding: 10px;
                background-color: #FFF9C4;
                border-left: 3px solid #FBC02D;
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(info_label)


class HorizontalLine(QFrame):
    """Горизонтальная разделительная линия."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setStyleSheet("QFrame { color: #BDBDBD; }")


class ResultDisplayWidget(QWidget):
    """Виджет для красивого отображения результата расчета."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title = QLabel("📊 РЕЗУЛЬТАТ РАСЧЕТА")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1976D2;
                padding: 10px;
                background-color: #E3F2FD;
                border-radius: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Результаты
        self.result_label = QLabel("Нажмите 'Рассчитать' для получения результата")
        self.result_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("""
            QLabel {
                color: #2E7D32;
                padding: 20px;
                background-color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.result_label)
    
    def set_result(self, value: float, unit: str = "т CO₂"):
        """
        Устанавливает результат расчета.
        
        :param value: Значение выбросов.
        :param unit: Единица измерения.
        """
        self.result_label.setText(f"Выбросы: {value:,.2f} {unit}")
        self.result_label.setStyleSheet("""
            QLabel {
                color: #2E7D32;
                padding: 20px;
                background-color: #E8F5E9;
                border: 2px solid #4CAF50;
                border-radius: 5px;
            }
        """)
    
    def set_error(self, message: str):
        """
        Отображает сообщение об ошибке.
        
        :param message: Текст ошибки.
        """
        self.result_label.setText(f"⚠️ {message}")
        self.result_label.setStyleSheet("""
            QLabel {
                color: #C62828;
                padding: 20px;
                background-color: #FFEBEE;
                border: 2px solid #F44336;
                border-radius: 5px;
            }
        """)
    
    def clear(self):
        """Очищает результат."""
        self.result_label.setText("Нажмите 'Рассчитать' для получения результата")
        self.result_label.setStyleSheet("""
            QLabel {
                color: #757575;
                padding: 20px;
                background-color: #FFFFFF;
                border: 2px solid #BDBDBD;
                border-radius: 5px;
            }
        """)


class BalanceVisualizationWidget(QWidget):
    """Виджет для визуализации баланса углерода."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = SectionHeader("⚖️ Баланс углерода")
        layout.addWidget(title)
        
        # Входящий углерод
        self.carbon_in_label = QLabel("Углерод входящий: — т")
        self.carbon_in_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.carbon_in_label)
        
        self.carbon_in_bar = QProgressBar()
        self.carbon_in_bar.setMaximum(100)
        self.carbon_in_bar.setValue(0)
        self.carbon_in_bar.setTextVisible(True)
        self.carbon_in_bar.setFormat("%v%")
        self.carbon_in_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BDBDBD;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #FF9800;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.carbon_in_bar)
        
        # Выходящий углерод
        self.carbon_out_label = QLabel("Углерод выходящий: — т")
        self.carbon_out_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.carbon_out_label)
        
        self.carbon_out_bar = QProgressBar()
        self.carbon_out_bar.setMaximum(100)
        self.carbon_out_bar.setValue(0)
        self.carbon_out_bar.setTextVisible(True)
        self.carbon_out_bar.setFormat("%v%")
        self.carbon_out_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BDBDBD;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.carbon_out_bar)
        
        # Разница (выбросы)
        self.emissions_label = QLabel("Выбросы CO₂: — т")
        self.emissions_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.emissions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emissions_label.setStyleSheet("""
            QLabel {
                color: #D32F2F;
                padding: 10px;
                background-color: #FFEBEE;
                border: 2px solid #F44336;
                border-radius: 5px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.emissions_label)
    
    def update_balance(self, carbon_in: float, carbon_out: float):
        """
        Обновляет отображение баланса углерода.
        
        :param carbon_in: Входящий углерод, т.
        :param carbon_out: Выходящий углерод, т.
        """
        # Расчет выбросов CO2
        co2_emissions = (carbon_in - carbon_out) * 3.664
        
        # Обновление текста
        self.carbon_in_label.setText(f"Углерод входящий: {carbon_in:,.2f} т")
        self.carbon_out_label.setText(f"Углерод выходящий: {carbon_out:,.2f} т")
        self.emissions_label.setText(f"Выбросы CO₂: {co2_emissions:,.2f} т")
        
        # Обновление прогресс-баров (в процентах от максимума)
        max_carbon = max(carbon_in, carbon_out) if max(carbon_in, carbon_out) > 0 else 1
        
        in_percent = int((carbon_in / max_carbon) * 100)
        out_percent = int((carbon_out / max_carbon) * 100)
        
        self.carbon_in_bar.setValue(in_percent)
        self.carbon_out_bar.setValue(out_percent)
    
    def clear(self):
        """Очищает виджет баланса."""
        self.carbon_in_label.setText("Углерод входящий: — т")
        self.carbon_out_label.setText("Углерод выходящий: — т")
        self.emissions_label.setText("Выбросы CO₂: — т")
        self.carbon_in_bar.setValue(0)
        self.carbon_out_bar.setValue(0)


def create_tooltip_style() -> str:
    """
    Возвращает CSS стиль для всплывающих подсказок.
    
    :return: CSS строка.
    """
    return """
        QToolTip {
            background-color: #37474F;
            color: #FFFFFF;
            border: 1px solid #263238;
            border-radius: 4px;
            padding: 8px;
            font-size: 11px;
        }
    """


def add_calculation_help_text(layout, category_name: str):
    """
    Добавляет информационный блок с подсказкой о категории.
    
    :param layout: Layout, в который добавляется помощь.
    :param category_name: Название категории.
    """
    help_texts = {
        "Категория 1": "Расчет выбросов CO₂ от сжигания топлива в стационарных установках (котлы, печи, ТЭС).",
        "Категория 5": "Расчет выбросов CO₂ от производства кокса на основе углеродного баланса.",
        "Категория 6": "Расчет выбросов CO₂ от производства цемента при обжиге карбонатного сырья.",
        "Категория 7": "Расчет выбросов CO₂ от производства извести при разложении известняка и доломита.",
        "Категория 14": "Расчет выбросов CO₂ от металлургических процессов (чугун, сталь, агломерат).",
        "Категория 20": "Расчет выбросов CH₄ от захоронения отходов с использованием модели затухания первого порядка.",
    }
    
    if category_name in help_texts:
        info_box = InfoBox("ℹ️ О категории", help_texts[category_name])
        layout.addWidget(info_box)