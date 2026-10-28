# -*- coding: utf-8 -*-
import re
from System.Windows.Media import BrushConverter

class DataValidator(object):
    def __init__(self):
        try:
            self.brush_blue = BrushConverter().ConvertFromString("#24508A")
            self.brush_red = BrushConverter().ConvertFromString("#C9372C")
            self.brush_line = BrushConverter().ConvertFromString("#D3D9DF")
        except Exception:
            self.brush_blue = None
            self.brush_red = None
            self.brush_line = None

    def parse_distances(self, text):
        if not text:
            raise ValueError("La liste d'entraxes est vide.")
        cleaned = text.strip().replace(",", ".")
        cleaned = re.sub(r"[^\d\.\-\s;]", "", cleaned)
        tokens = re.split(r"[;\s]+", cleaned)
        result = []
        for t in tokens:
            t = t.strip()
            if not t:
                continue
            try:
                v = float(t)
            except ValueError:
                raise ValueError("Valeur non numérique détectée : '{}'.".format(t))
            if v <= 0:
                raise ValueError("Les entraxes doivent être strictement positifs (> 0). Valeur incorrecte : {}.".format(t))
            if v < 1e-6:
                raise ValueError("Valeur trop faible détectée : {}. Veuillez saisir un entraxe valide.".format(t))
            result.append(v)
        if len(result) == 0:
            raise ValueError("Aucune valeur numérique valide trouvée. Séparez vos distances par une virgule, un point-virgule ou un espace.")
        return result

    def is_positive_number_list(self, text):
        try:
            values = self.parse_distances(text)
            if not values:
                return False
            return True
        except Exception:
            return False

    def get_border_brush(self, is_valid):
        if is_valid:
            return self.brush_blue
        return self.brush_red
