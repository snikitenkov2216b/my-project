# ui/formula_library_dialog.py
# Диалоговое окно для управления библиотекой сохраненных формул.
# Комментарии на русском. Поддержка UTF-8.

import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt

LIBRARY_FILE = "formulas_library.json"

class FormulaLibraryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Библиотека формул")
        self.setMinimumSize(400, 300)
        
        self.selected_formula = None
        
        layout = QVBoxLayout(self)
        
        self.formula_list = QListWidget()
        self.formula_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.formula_list)
        
        buttons_layout = QHBoxLayout()
        load_button = QPushButton("Загрузить")
        load_button.clicked.connect(self.accept)
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self._delete_selected)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(load_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        
        self._load_formulas_to_list()

    def _load_formulas_to_list(self):
        self.formula_list.clear()
        try:
            with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                library = json.load(f)
                for formula_data in library:
                    self.formula_list.addItem(formula_data['name'])
        except (FileNotFoundError, json.JSONDecodeError):
            # Файл еще не создан или пуст, это нормально
            pass

    def _save_library(self, library):
        with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=4)

    def _delete_selected(self):
        current_item = self.formula_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите формулу для удаления.")
            return

        reply = QMessageBox.question(self, "Подтверждение", 
                                     f"Вы уверены, что хотите удалить формулу '{current_item.text()}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                    library = json.load(f)
                
                library = [f for f in library if f['name'] != current_item.text()]
                
                self._save_library(library)
                self._load_formulas_to_list() # Обновляем список
            except FileNotFoundError:
                pass # Нечего удалять

    def accept(self):
        current_item = self.formula_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите формулу для загрузки.")
            return
            
        try:
            with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            formula_to_load = next((f for f in library if f['name'] == current_item.text()), None)
            
            if formula_to_load:
                self.selected_formula = formula_to_load
                super().accept()
        except FileNotFoundError:
            QMessageBox.critical(self, "Ошибка", "Файл библиотеки не найден.")

    def get_selected_formula(self):
        return self.selected_formula