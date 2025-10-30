# scripts/fix_land_conversion_results.py
"""Автоматическое добавление меток результатов для land_conversion_tab.py"""

import re

# Read the file
with open('ui/land_conversion_tab.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replacements for _append_result -> setText
replacements = [
    (r'self\._append_result\((f"[^"]*Изменение запасов C в результате конверсии[^"]*")\)', r'self.f91_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*Выбросы CO2 от осушения[^"]*")\)', r'self.f92_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*Выбросы N2O от осушения[^"]*)\)', r'self.f93_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*Выбросы CH4 от осушения[^"]*)\)', r'self.f94_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*Выбросы от пожара[^"]*)\)', r'self.f95_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*ΔC на кормовых угодьях[^"]*)\)', r'self.f96_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*C из растений[^"]*)\)', r'self.f97_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*Потери C от эрозии[^"]*)\)', r'self.f99_result.setText(\1)'),
    (r'self\._append_result\((f"[^"]*Вынос C с урожаем[^"]*)\)', r'self.f100_result.setText(\1)'),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('ui/land_conversion_tab.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Completed replacements")
