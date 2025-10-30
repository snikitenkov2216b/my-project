#!/usr/bin/env python3
"""
Скрипт для автоматического добавления TabDataMixin ко всем вкладкам категорий.
"""
import os
import re
from pathlib import Path


def add_mixin_to_file(file_path):
    """Добавляет TabDataMixin к классу вкладки, если его еще нет."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем, есть ли уже миксин
    if 'TabDataMixin' in content:
        print(f"[OK] {file_path.name} - mixin already added")
        return False

    # Проверяем, есть ли класс вкладки
    class_match = re.search(r'class\s+(\w+)\s*\(.*?QWidget.*?\):', content)
    if not class_match:
        print(f"[SKIP] {file_path.name} - class not found")
        return False

    class_name = class_match.group(1)

    # Добавляем импорт
    import_line = "from ui.tab_data_mixin import TabDataMixin\n"

    # Ищем последний импорт перед определением класса
    last_import_match = None
    for match in re.finditer(r'^from .+? import .+?$', content, re.MULTILINE):
        if match.start() < class_match.start():
            last_import_match = match

    if last_import_match:
        # Вставляем импорт после последнего импорта
        insert_pos = last_import_match.end()
        content = content[:insert_pos] + '\n' + import_line + content[insert_pos:]
    else:
        # Вставляем импорт перед классом
        insert_pos = class_match.start()
        content = content[:insert_pos] + import_line + '\n\n' + content[insert_pos:]

    # Изменяем определение класса
    old_class_def = class_match.group(0)
    new_class_def = old_class_def.replace('(QWidget)', '(TabDataMixin, QWidget)')
    new_class_def = new_class_def.replace('( QWidget)', '(TabDataMixin, QWidget)')

    content = content.replace(old_class_def, new_class_def, 1)

    # Сохраняем файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[ADDED] {file_path.name} - mixin added to {class_name}")
    return True


def main():
    """Главная функция."""
    ui_dir = Path(__file__).parent / 'ui'

    if not ui_dir.exists():
        print(f"Директория {ui_dir} не найдена!")
        return

    # Находим все файлы вкладок категорий
    category_files = sorted(ui_dir.glob('category_*_tab.py'))

    if not category_files:
        print("Файлы вкладок категорий не найдены!")
        return

    print(f"Найдено {len(category_files)} файлов вкладок категорий\n")

    modified_count = 0
    for file_path in category_files:
        if add_mixin_to_file(file_path):
            modified_count += 1

    print(f"\n{'='*60}")
    print(f"Обработано файлов: {len(category_files)}")
    print(f"Изменено файлов: {modified_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
