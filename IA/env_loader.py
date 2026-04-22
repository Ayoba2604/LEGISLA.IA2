from pathlib import Path

from dotenv import load_dotenv


_ENV_LOADED = False


def load_project_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    root_dir = Path(__file__).resolve().parent.parent
    for env_name in (".env", ".env.local"):
        env_path = root_dir / env_name
        if env_path.exists():
            load_dotenv(env_path, override=False)

    _ENV_LOADED = True
