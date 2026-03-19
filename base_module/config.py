from pathlib import Path
import yaml


def load_yaml(config_path: str | Path):
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"config.yaml配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
