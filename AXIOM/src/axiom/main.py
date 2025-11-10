# AXIOM/src/axiom/main.py

from .config import AxiomConfig, ROOT_DIR
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def main():
    # Use ROOT_DIR from config.py to ensure all paths point to project root
    CONFIG_DIR = ROOT_DIR / "configs"
    default_json = CONFIG_DIR / "default.json"
    production_json = CONFIG_DIR / "production.json"

    print("=== Environment Variable Configuration ===")
    env_config = AxiomConfig.from_env()
    for key, value in env_config.to_dict().items():
        print(f"{key}: -> {value}")

    print("\n=== Default JSON Configuration ===")
    json_config = AxiomConfig.from_json_file(default_json)
    for key, value in json_config.to_dict().items():
        print(f"{key}: -> {value}")

    print("\n=== Production JSON Configuration ===")
    prod_config = AxiomConfig.from_json_file(production_json)
    for key, value in prod_config.to_dict().items():
        print(f"{key}: -> {value}")

if __name__ == "__main__":
    main()
