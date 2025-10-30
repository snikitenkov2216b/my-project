# ui/lazy_tab_widget.py
"""
Ленивая загрузка вкладок для оптимизации времени запуска приложения.
Вкладки создаются только при первом обращении к ним.
"""
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class LazyTabWidget(QWidget):
    """
    Виджет-обертка для ленивой загрузки вкладок.
    Отображает заглушку до первой активации вкладки.
    """

    def __init__(self, tab_factory, tab_title):
        """
        Args:
            tab_factory: Callable функция для создания вкладки
            tab_title: Название вкладки для логирования
        """
        super().__init__()
        self._tab_factory = tab_factory
        self._tab_title = tab_title
        self._real_widget = None
        self._initialized = False

        # Создаем заглушку
        self._init_placeholder()

    def _init_placeholder(self):
        """Создает placeholder пока вкладка не загружена."""
        layout = QVBoxLayout(self)
        label = QLabel(f"Загрузка {self._tab_title}...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(label)

    def ensure_loaded(self):
        """
        Гарантирует что реальная вкладка загружена.
        Вызывается при первой активации вкладки.
        """
        if not self._initialized:
            try:
                logging.debug(f"Lazy loading tab: {self._tab_title}")

                # Создаем реальную вкладку
                self._real_widget = self._tab_factory()

                if self._real_widget:
                    # Заменяем placeholder на реальный виджет
                    layout = self.layout()
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()

                    layout.addWidget(self._real_widget)
                    self._initialized = True
                    logging.info(f"Tab loaded: {self._tab_title}")
                else:
                    logging.error(f"Failed to create tab: {self._tab_title}")

            except Exception as e:
                logging.error(f"Error loading tab {self._tab_title}: {e}", exc_info=True)
                # Показываем ошибку вместо placeholder
                layout = self.layout()
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                error_label = QLabel(f"❌ Ошибка загрузки: {str(e)}")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                error_label.setStyleSheet("font-size: 14px; color: #c00;")
                layout.addWidget(error_label)

    def showEvent(self, event):
        """Переопределяем showEvent для ленивой загрузки."""
        self.ensure_loaded()
        super().showEvent(event)

    def is_initialized(self):
        """Проверяет, инициализирована ли вкладка."""
        return self._initialized

    def get_real_widget(self):
        """Возвращает реальный виджет (или None если не загружен)."""
        return self._real_widget

    # Методы для совместимости с TabDataMixin
    def get_data(self):
        """Прокси для get_data() реального виджета."""
        if self._real_widget and hasattr(self._real_widget, 'get_data'):
            return self._real_widget.get_data()
        return {'fields': {}, 'result': None}

    def set_data(self, data):
        """Прокси для set_data() реального виджета."""
        # Гарантируем что вкладка загружена
        self.ensure_loaded()
        if self._real_widget and hasattr(self._real_widget, 'set_data'):
            self._real_widget.set_data(data)

    def clear_fields(self):
        """Прокси для clear_fields() реального виджета."""
        if self._real_widget and hasattr(self._real_widget, 'clear_fields'):
            self._real_widget.clear_fields()
