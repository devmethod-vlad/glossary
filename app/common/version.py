import toml


def get_app_info() -> dict:
    """Получение версии приложения"""
    with open("pyproject.toml") as f:
        info: dict = toml.load(f)

    return {
        "name": info["tool"]["poetry"]["name"],
        "version": info["tool"]["poetry"]["version"],
        "description": info["tool"]["poetry"]["description"],
    }
