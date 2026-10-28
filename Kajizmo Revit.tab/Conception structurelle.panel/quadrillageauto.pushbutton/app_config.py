# -*- coding: utf-8 -*-
"""Lecture de config.json (compatible IronPython 2.7 et CPython 3).

Ce module s'appelait config.py : pyRevit réserve ce nom au script de
configuration (Shift+Clic sur le bouton), il a donc été renommé.
"""
from __future__ import unicode_literals
import io
import json
import os

DEFAULTS = {
    "version": "1.1.0",
    "title": "Réseau",
    "subtitle": "de quadrillage",
    "author": "Riana Stellia",
    "log_name": "quadrillageauto.log",
    "units": [
        {"label": "Mètres (m)", "symbol": "m", "factor_to_feet": 3.28084},
        {"label": "Millimètres (mm)", "symbol": "mm", "factor_to_feet": 0.00328084},
        {"label": "Centimètres (cm)", "symbol": "cm", "factor_to_feet": 0.0328084},
    ],
    "default_unit_index": 0,
    "default_offset": 1.0,
    "offset_step": 0.5,
    "default_color_index": 1,
    "color_options": [
        {"label": "Rouge (texte & lignes)", "rgb": [255, 0, 0]},
        {"label": "Noir (inversion auto)", "rgb": [0, 0, 0]},
        {"label": "Conserver l'actuelle", "rgb": None}
    ],
    "notation": {
        "x_default_alpha": False,
        "y_default_alpha": True
    },
    "placeholders": {
        "dist_x": "3, 4, 5, 5",
        "dist_y": "3, 4, 5, 5"
    },
    "ui": {
        "window_width": 520,
        "window_height": 680,
        "badge_max_width": 260
    },
    "revit": {
        "transaction_name": "Créer Quadrillage par Origine",
        "level_extension_feet": 3.28084
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
