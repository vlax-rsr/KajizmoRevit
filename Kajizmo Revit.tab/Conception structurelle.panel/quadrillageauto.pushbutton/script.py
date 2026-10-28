# -*- coding: utf-8 -*-
__title__ = "Quadrillage\nPersonnalisé"
__doc__ = """Générateur de quadrillages basé sur un point d'origine unique."""
__version__ = "1.1.0"
__author__ = "Riana Stellia"

from ui_manager import QuadrillageWindow

if __name__ == "__main__":
    app = QuadrillageWindow("ui.xaml")
    app.ShowDialog()
