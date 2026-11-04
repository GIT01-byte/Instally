"""
Встроенный каталог программ.
Включает в себя все менеджеры пакетов (Choco, Apt, Dnf, Snap, Winget)
и флаг необходимости установки через Snap с параметром --classic.
"""

TEST_CATALOG = [
    {
        "category": "ТЕСТЫ",
        "name": "1. Успешная установка (Choco/Apt)",
        "desc": "Ставит hello (Win) или cowsay (Linux). Проверка зеленого статуса.",
        "choco": "hello",
        "apt": "cowsay",
        "dnf": "cowsay",
        "snap": "",
        "winget": "",
        "snap_classic": False,
    },
    {
        "category": "ТЕСТЫ",
        "name": "2. Падение Choco -> Winget",
        "desc": "CodeBlocks часто падает в Choco (404). Должен подхватиться Winget.",
        "choco": "failededasedase",
        "apt": "",
        "dnf": "",
        "snap": "",
        "winget": "CodeBlocks.CodeBlocks",
        "snap_classic": False,
    },
    {
        "category": "ТЕСТЫ",
        "name": "3. Падение Apt -> Snap",
        "desc": "VS Code нет в стандартном Apt. Должен автоматически уйти в Snap.",
        "choco": "",
        "apt": "code",
        "dnf": "code",
        "snap": "code",
        "winget": "",
        "snap_classic": True,
    },
    {
        "category": "ТЕСТЫ",
        "name": "4. Полный провал (404)",
        "desc": "Пакета нет нигде. Должны отработать оба движка и выдать ошибку.",
        "choco": "failededasedase",
        "apt": "failededasedase",
        "dnf": "failededasedase",
        "snap": "failededasedase",
        "winget": "failededasedase",
        "snap_classic": True,
    },
]
