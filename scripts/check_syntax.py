"""
Проверка синтаксиса всех Python файлов в проекте
"""
import sys
import py_compile
from pathlib import Path

# Установка кодировки UTF-8 для вывода
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_syntax(filepath):
    """Проверяет синтаксис Python файла"""
    try:
        py_compile.compile(str(filepath), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    project_root = Path(__file__).parent.parent

    print("="*80)
    print("ПРОВЕРКА СИНТАКСИСА PYTHON ФАЙЛОВ")
    print("="*80)
    print()

    errors = []
    success_count = 0

    # Проверяем все .py файлы в проекте
    for py_file in project_root.rglob("*.py"):
        # Пропускаем __pycache__ и виртуальные окружения
        if '__pycache__' in str(py_file) or 'venv' in str(py_file) or '.venv' in str(py_file):
            continue

        is_valid, error = check_syntax(py_file)

        if is_valid:
            success_count += 1
        else:
            errors.append((py_file, error))
            print(f"✗ {py_file.relative_to(project_root)}")
            print(f"  {error}")
            print()

    print("="*80)
    print("РЕЗУЛЬТАТЫ")
    print("="*80)
    print(f"Успешно: {success_count} файлов")
    print(f"Ошибки: {len(errors)} файлов")

    if errors:
        print("\n❌ Найдены синтаксические ошибки!")
        return 1
    else:
        print("\n✅ Все файлы прошли проверку синтаксиса!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
