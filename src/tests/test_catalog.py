import subprocess
import sys
from pathlib import Path

# Добавляем корневую папку 'src' в пути поиска, чтобы импорт работал при прямом запуске
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Импортируем каталог из Python-файла
from app.data.catalog import CATALOG


def get_os():
    if sys.platform == "win32":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


def _check_choco(pkg: str) -> bool:
    """Проверяет наличие пакета в Chocolatey."""
    try:
        result = subprocess.run(
            ["choco", "search", "--exact", "--limit-output", pkg],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        return bool(result.stdout.strip())
    except subprocess.TimeoutExpired:
        print("[Timeout] ", end="")
        return False
    except Exception:
        return False


def _check_apt(pkg: str) -> bool:
    """Проверяет наличие пакета в APT."""
    try:
        result = subprocess.run(
            ["apt-cache", "show", pkg],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("[Timeout] ", end="")
        return False
    except Exception:
        return False


def _check_winget(pkg: str) -> bool:
    """Проверяет наличие пакета в Winget."""
    try:
        result = subprocess.run(
            ["winget", "show", "--id", pkg, "--exact", "--accept-source-agreements"],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("[Timeout] ", end="")
        return False
    except Exception:
        return False


def _check_snap(pkg: str) -> bool:
    """Проверяет наличие пакета в Snap."""
    try:
        result = subprocess.run(
            ["snap", "info", pkg],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("[Timeout] ", end="")
        return False
    except Exception:
        return False


def test_packages_exist():
    """Проверяет, что все пакеты из встроенного каталога реально существуют в репозиториях."""
    os_type = get_os()

    if os_type == "windows":
        main_key = "choco"
        fallback_key = "winget"
        fallback_name = "winget"
    elif os_type == "linux":
        main_key = "apt"
        fallback_key = "snap"
        fallback_name = "snap"
    else:
        print("Неизвестная ОС для тестов")
        return

    missing_packages = []
    warnings = []
    total_checked = 0
    found_in_main = 0
    found_in_fallback = 0

    # Проходим по встроенному списку CATALOG
    for item in CATALOG:
        name = item["name"]
        pkg_main = item.get(main_key, "").strip()
        pkg_fallback = item.get(fallback_key, "").strip()
        is_classic = item.get("snap_classic", False)

        # Если нет ни основного, ни fallback-кода — пропускаем
        if not pkg_main and not pkg_fallback:
            continue

        total_checked += 1
        print(f"Проверка: {name}...", end=" ")

        main_ok = False
        fallback_ok = False

        # 1. Проверяем основной пакет
        if pkg_main:
            if os_type == "windows":
                main_ok = _check_choco(pkg_main)
            elif os_type == "linux":
                main_ok = _check_apt(pkg_main)

            if main_ok:
                print(f"✅ OK ({pkg_main})")
                found_in_main += 1
                continue

        # 2. Если основной не найден, проверяем fallback
        if pkg_fallback:
            if os_type == "windows":
                fallback_ok = _check_winget(pkg_fallback)
            elif os_type == "linux":
                fallback_ok = _check_snap(pkg_fallback)

            if fallback_ok:
                classic_info = (
                    " (требует --classic)" if is_classic and os_type == "linux" else ""
                )
                print(
                    f"⚠️ Найден только в {fallback_name} ({pkg_fallback}){classic_info}"
                )
                warnings.append((name, pkg_fallback, fallback_name, is_classic))
                found_in_fallback += 1
                continue

        # 3. Если нигде нет
        if not pkg_main:
            print(f"❌ НЕ НАЙДЕН (нет кода для {os_type})")
        else:
            print(f"❌ НЕ НАЙДЕН (проверено: {pkg_main}, {pkg_fallback})")

        missing_packages.append((name, pkg_main or pkg_fallback))

    print("\n" + "=" * 50)
    print(f"Всего проверено: {total_checked}")
    print(f"Найдено в основном репозитории: {found_in_main}")
    print(f"Найдено только в fallback: {found_in_fallback}")
    print(f"Не найдено нигде: {len(missing_packages)}")

    if warnings:
        print("\n--- ВНИМАНИЕ! ЭТИ ПАКЕТЫ ЕСТЬ ТОЛЬКО В FALLBACK ---")
        for name, pkg, source, is_classic in warnings:
            classic_note = " [--classic]" if is_classic else ""
            print(f"{name} -> {source} ({pkg}){classic_note}")
        print("(При установке основной менеджер упадет, и сработает fallback).")

    if missing_packages:
        print("\n--- ОШИБКА! ЭТИ ПАКЕТЫ НЕ НАЙДЕНЫ НИГДЕ ---")
        for name, pkg in missing_packages:
            print(f"{name} ({pkg})")
        sys.exit(1)  # Тест провален
    else:
        print("\nВсе пакеты найдены (хотя бы в одном из менеджеров)!")
        sys.exit(0)  # Тест пройден


if __name__ == "__main__":
    test_packages_exist()
