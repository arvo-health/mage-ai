import os
from typing import Dict

import yaml

from mage_ai.command_center.constants import SETTINGS_FILENAME
from mage_ai.shared.io import safe_write


def load_settings(full_path: str = None) -> Dict:
    full_path = full_path or __settings_full_path()

    settings = None

    if os.path.exists(full_path):
        # This file stores values submitted through the API; never render it as a template.
        with open(full_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f.read()) or {}

    return settings


def save_settings(settings: Dict, full_path: str = None) -> Dict:
    full_path = full_path or __settings_full_path()

    content = yaml.dump(settings)
    safe_write(full_path, content)


def __settings_full_path() -> str:
    from mage_ai.settings.repo import get_variables_dir

    variables_dir = get_variables_dir(root_project=True)
    return os.path.join(variables_dir, SETTINGS_FILENAME)
