# ui/formula_library_dialog.py
# Диалоговое окно для управления библиотекой сохраненных формул.
# Обновлено: централизованные пути, обработка ошибок IO.
# Комментарии на русском. Поддержка UTF-8.

import json
import logging
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtCore import Qt

# Импортируем централизованный путь к файлу библиотеки
from paths import LIBRARY_FILE


class FormulaLibraryDialog(QDialog):
    """
    Диалоговое окно для работы с библиотекой формул.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Библиотека формул")
        self.setMinimumSize(500, 400)

        self.selected_formula = None
        self._init_ui()
        self._load_formulas_to_list()

    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)

        # Список формул
        self.formula_list = QListWidget()
        self.formula_list.itemDoubleClicked.connect(self.accept)
        self.formula_list.setToolTip(
            "Дважды кликните на формулу для загрузки.\n"
            "Выберите формулу и нажмите 'Удалить' для удаления."
        )
        layout.addWidget(self.formula_list)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        load_button = QPushButton("Загрузить")
        load_button.setToolTip("Загрузить выбранную формулу в редактор")
        load_button.clicked.connect(self.accept)

        delete_button = QPushButton("Удалить")
        delete_button.setToolTip("Удалить выбранную формулу из библиотеки")
        delete_button.clicked.connect(self._delete_selected)

        refresh_button = QPushButton("Обновить")
        refresh_button.setToolTip("Обновить список формул")
        refresh_button.clicked.connect(self._load_formulas_to_list)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(load_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

    def _load_formulas_to_list(self):
        """
        Загружает список формул из файла библиотеки и отображает в списке.
        С полной обработкой ошибок.
        """
        self.formula_list.clear()

        try:
            # Проверяем существование файла
            if not LIBRARY_FILE.exists():
                logging.info(f"Файл библиотеки формул не найден: {LIBRARY_FILE}")
                logging.info("Библиотека будет создана при первом сохранении формулы.")
                return

            # Читаем файл
            with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                library = json.load(f)

            # Проверяем, что library - это список
            if not isinstance(library, list):
                logging.warning(
                    "Файл библиотеки имеет неверный формат (ожидается список)."
                )
                QMessageBox.warning(
                    self,
                    "Ошибка формата",
                    "Файл библиотеки поврежден. Он будет пересоздан.",
                )
                return

            # Добавляем формулы в список
            for formula_data in library:
                if isinstance(formula_data, dict) and "name" in formula_data:
                    self.formula_list.addItem(formula_data["name"])
                else:
                    logging.warning(
                        f"Пропущена формула с неверным форматом: {formula_data}"
                    )

            logging.info(f"Загружено формул: {len(library)}")

        except json.JSONDecodeError as e:
            logging.error(
                f"Ошибка парсинга JSON в файле библиотеки: {e}", exc_info=True
            )
            QMessageBox.warning(
                self,
                "Ошибка чтения",
                f"Файл библиотеки поврежден (ошибка JSON).\n"
                f"Файл: {LIBRARY_FILE}\n\n"
                f"Библиотека будет пересоздана при следующем сохранении.",
            )

        except PermissionError as e:
            logging.error(f"Нет прав доступа к файлу библиотеки: {e}")
            QMessageBox.critical(
                self,
                "Ошибка доступа",
                f"Нет прав для чтения файла библиотеки.\n"
                f"Файл: {LIBRARY_FILE}\n\n"
                f"Проверьте права доступа к файлу.",
            )

        except Exception as e:
            logging.error(
                f"Неожиданная ошибка при загрузке библиотеки: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось загрузить библиотеку формул:\n{e}"
            )

    def _save_library(self, library: list):
        """
        Сохраняет библиотеку формул в файл.
        С полной обработкой ошибок.

        :param library: Список словарей с данными формул.
        """
        try:
            # Создаем родительскую директорию, если её нет
            LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Сохраняем данные
            with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
                json.dump(library, f, ensure_ascii=False, indent=4)

            logging.info(f"Библиотека сохранена: {LIBRARY_FILE}")

        except PermissionError as e:
            logging.error(f"Нет прав для записи файла библиотеки: {e}")
            raise PermissionError(
                f"Нет прав для записи в файл.\n"
                f"Файл: {LIBRARY_FILE}\n\n"
                f"Проверьте права доступа."
            )

        except OSError as e:
            logging.error(f"Ошибка записи файла библиотеки: {e}", exc_info=True)
            raise OSError(f"Ошибка при записи файла:\n{e}\n\n" f"Файл: {LIBRARY_FILE}")

        except Exception as e:
            logging.error(
                f"Неожиданная ошибка при сохранении библиотеки: {e}", exc_info=True
            )
            raise Exception(f"Не удалось сохранить библиотеку:\n{e}")

    def _delete_selected(self):
        """Удаляет выбранную формулу из библиотеки."""
        current_item = self.formula_list.currentItem()

        if not current_item:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите формулу для удаления."
            )
            return

        formula_name = current_item.text()

        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить формулу\n'{formula_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Загружаем библиотеку
            if not LIBRARY_FILE.exists():
                QMessageBox.warning(self, "Ошибка", "Файл библиотеки не найден.")
                return

            with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                library = json.load(f)

            # Удаляем формулу
            library = [f for f in library if f.get("name") != formula_name]

            # Сохраняем обновленную библиотеку
            self._save_library(library)

            # Обновляем список
            self._load_formulas_to_list()

            QMessageBox.information(
                self, "Успех", f"Формула '{formula_name}' удалена из библиотеки."
            )
            logging.info(f"Формула '{formula_name}' удалена из библиотеки.")

        except Exception as e:
            logging.error(f"Ошибка при удалении формулы: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить формулу:\n{e}")

    def get_selected_formula(self):
        """
        Возвращает данные выбранной формулы.

        :return: Словарь с данными формулы или None.
        """
        current_item = self.formula_list.currentItem()

        if not current_item:
            return None

        formula_name = current_item.text()

        try:
            if not LIBRARY_FILE.exists():
                return None

            with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                library = json.load(f)

            # Ищем формулу по имени
            for formula_data in library:
                if formula_data.get("name") == formula_name:
                    return formula_data

            return None

        except Exception as e:
            logging.error(
                f"Ошибка при получении формулы '{formula_name}': {e}", exc_info=True
            )
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить формулу:\n{e}")
            return None
