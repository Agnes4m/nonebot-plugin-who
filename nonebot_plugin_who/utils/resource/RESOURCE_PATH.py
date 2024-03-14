from pathlib import Path

MAIN_PATH = Path("data/Pokemon")

PLAYER_PATH = MAIN_PATH / "players"
RESOURCE_PATH = MAIN_PATH / "resource"

CHAR_ICON_PATH = RESOURCE_PATH / "icon"
CHAR_ICON_S_PATH = RESOURCE_PATH / "staricon"


def init_dir():
    for i in [MAIN_PATH, PLAYER_PATH, RESOURCE_PATH, CHAR_ICON_PATH, CHAR_ICON_S_PATH]:
        i.mkdir(parents=True, exist_ok=True)


init_dir()
