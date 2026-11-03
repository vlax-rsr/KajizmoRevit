# -*- coding: utf-8 -*-
__title__ = """Poteaux
depuis DWG"""
__doc__ = """Implantation de poteaux à partir des blocs d'un DWG : choisissez une famille,
un type est créé automatiquement pour chaque dimension détectée."""
__version__ = "1.0.0"
__author__ = "R. Stellia"

from ui_manager import PoteauWindow

if __name__ == "__main__":
    app = PoteauWindow("ui.xaml")
    app.ShowDialog()
