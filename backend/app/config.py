"""
config.py — loads agents.yaml and policy_rules.yaml at startup.
These are immutable after load. No runtime mutation.
"""
import os
import yaml
from functools import lru_cache
from typing import Any

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")


def _load_yaml(filename: str) -> dict[str, Any]:
    path = os.path.join(CONFIG_DIR, filename)
    with open(path, "r") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_agents_config() -> dict[str, Any]:
    return _load_yaml("agents.yaml")


@lru_cache(maxsize=1)
def get_policy_config() -> dict[str, Any]:
    return _load_yaml("policy_rules.yaml")


def get_all_categories() -> list[str]:
    return get_agents_config()["all_categories"]


def get_agent_definitions() -> list[dict]:
    return get_agents_config()["agents"]
