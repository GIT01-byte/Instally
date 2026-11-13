import subprocess
import sys
from pathlib import Path

# Добавляем корневую папку 'src' в пути поиска
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.catalog import CATALOG


def get_os():
    if sys.platform == "win32":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


def _check_choco(pkg: str) -> bool:
    try:
        result = subprocess.run(
            ["choco", "search", "--exact", "--limit-output", pkg],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def _check_apt(pkg: str) -> bool:
    try:
        result = subprocess.run(
            ["apt-cache", "show", pkg], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_winget(pkg: str) -> bool:
    try:
        result = subprocess.run(
            ["winget", "show", "--id", pkg, "--exact", "--accept-source-agreements"],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_snap(pkg: str) -> bool:
    try:
        result = subprocess.run(
            ["snap", "info", pkg], capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except Exception:
        return False


def test_packages_exist():
    """Проверяет пакеты и возвращает результат (без вызова sys.exit)."""
    os_type = get_os()
    if os_type == "windows":
        main_key, fallback_key, fallback_name = "choco", "winget", "winget"
    elif os_type == "linux":
        main_key, fallback_key, fallback_name = "apt", "snap", "snap"
    else:
        print("Неизвестная ОС для тестов")
        return

    missing_packages = []
    warnings = []
    total_checked = 0

    for item in CATALOG:
        name = item["name"]
        pkg_main = item.get(main_key, "").strip()
        pkg_fallback = item.get(fallback_key, "").strip()
        is_classic = item.get("snap_classic", False)

        if not pkg_main and not pkg_fallback:
            continue

        total_checked += 1
        print(f"Проверка: {name}...", end=" ")

        main_ok = False
        if pkg_main:
            if os_type == "windows":
                main_ok = _check_choco(pkg_main)
            elif os_type == "linux":
                main_ok = _check_apt(pkg_main)

            if main_ok:
                print(f"✅ OK ({pkg_main})")
                continue

        if pkg_fallback:
            fallback_ok = False
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
                warnings.append(name)
                continue

        if not pkg_main:
            print(f"❌ НЕ НАЙДЕН (нет кода для {os_type})")
        else:
            print(f"❌ НЕ НАЙДЕН (проверено: {pkg_main}, {pkg_fallback})")
        missing_packages.append(name)

    print("\n" + "=" * 50)
    print(f"Всего проверено: {total_checked}")
    print(
        f"Найдено в основном репозитории: {total_checked - len(warnings) - len(missing_packages)}"
    )
    print(f"Найдено только в fallback: {len(warnings)}")
    print(f"Не найдено нигде: {len(missing_packages)}")

    if warnings:
        print("\n--- ЕСТЬ ТОЛЬКО В FALLBACK ---")
        for name in warnings:
            print(f"- {name}")

    if missing_packages:
        print("\n--- ОШИБКА! НЕ НАЙДЕНЫ НИГДЕ ---")
        for name in missing_packages:
            print(f"- {name}")
    else:
        print("\nВсе пакеты найдены (хотя бы в одном из менеджеров)!")

    # Возвращаем True/False, если нужно, но UI парсит текст
    return len(missing_packages) == 0
