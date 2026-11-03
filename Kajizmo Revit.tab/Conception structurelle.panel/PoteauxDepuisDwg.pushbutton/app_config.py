# -*- coding: utf-8 -*-
"""Lecture de config.json (compatible IronPython 2.7 et CPython 3).

Ce module ne s'appelle pas config.py : pyRevit réserve ce nom au script de
configuration (Shift+Clic sur le bouton).
"""
from __future__ import unicode_literals
import io
import json
import os

DEFAULTS = {
    "version": "1.0.0",
    "title": "Poteaux",
    "subtitle": "depuis DWG",
    "author": "R. Stellia",
    "log_name": "poteaux_dwg.log",
    "options": {
        "use_rotation": True,
        "auto_orient": True,
        "center_on_shape": True
    },
    "tolerances": {
        "orientation_cm": 1.0,
        "dimensions_cm": 1.5
    },
    "ui": {
        "window_width": 480,
        "window_height": 760
    },
    "types": {
        "param_b": "",
        "param_h": "",
        "arrondi_cm": 0.5,
        "prefixe": "",
        "plage_section_cm": [10, 200]
    },
    "revit": {
        "transaction_name": "Implanter des poteaux depuis DWG"
    },
}


class ConfigManager(object):
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.config_path = config_path
        self.load_error = None
        self.config = self._load()

    def _load(self):
        try:
            # io.open accepte 'encoding' sous IronPython 2.7 (le open() natif non)
            with io.open(self.config_path, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except Exception as ex:
            self.load_error = str(ex)
            return {}

    def get(self, key, default=None):
        for source in (self.config, DEFAULTS):
            try:
                value = source
                for k in key.split('.'):
                    value = value[k]
                return value
            except Exception:
                continue
        return default

    def get_config(self):
        return self.config
