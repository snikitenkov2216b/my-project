#!/usr/bin/env python3
"""
Скрипт для замены setText на _append_result в вкладках поглощения.
"""
import re
from pathlib import Path


def fix_result_display(file_path):
    """Заменяет self.result_text.setText на self._append_result."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Подсчитываем количество замен
    count = content.count('self.result_text.setText(')

    if count == 0:
        print(f"[SKIP] {file_path.name} - no setText calls found")
        return False

    # Заменяем все вызовы setText на _append_result
    # Паттерн: self.result_text.setText(...)
    content = content.replace('self.result_text.setText(', 'self._append_result(')

    # Также заменяем форматирование результатов для единого стиля
    # Заменяем просто имя формулы на [Ф. X]
    patterns = [
        (r'f"ΔC биомассы \(Ф\. 2\):', r'f"[Ф. 2] ΔC биомассы:'),
        (r'f"C древостоя \(Ф\. 3\):', r'f"[Ф. 3] C древостоя:'),
        (r'f"C подроста \(Ф\. 4\):', r'f"[Ф. 4] C подроста:'),
        (r'f"C почвы \(Ф\. 5\):', r'f"[Ф. 5] C почвы:'),
        (r'f"Выбросы от пожара \(Ф\. 6\):', r'f"[Ф. 6] Выбросы от пожара:'),
        (r'f"CO2 от осушения \(Ф\. 7\):', r'f"[Ф. 7] CO2 от осушения:'),
        (r'f"N2O от осушения \(Ф\. 8\):', r'f"[Ф. 8] N2O от осушения:'),
        (r'f"CH4 от осушения \(Ф\. 9\):', r'f"[Ф. 9] CH4 от осушения:'),
        (r'f"C_FUEL \(Ф\. 10\):', r'f"[Ф. 10] C_FUEL:'),
        (r'f"CO2 из ΔC \(Ф\. 11\):', r'f"[Ф. 11] CO2 из ΔC:'),
        (r'f"CO2-экв \(Ф\. 12\):', r'f"[Ф. 12] CO2-экв:'),
    ]

    for old_pattern, new_pattern in patterns:
        content = re.sub(old_pattern, new_pattern, content)

    # Сохраняем файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[FIXED] {file_path.name} - replaced {count} setText calls")
    return True


def main():
    """Главная функция."""
    # Находим файл absorption_tabs.py
    file_path = Path(__file__).parent / 'ui' / 'absorption_tabs.py'

    if not file_path.exists():
        print(f"File {file_path} not found!")
        return

    print(f"Processing {file_path.name}...")
    fix_result_display(file_path)
    print("\nDone!")


if __name__ == '__main__':
    main()
