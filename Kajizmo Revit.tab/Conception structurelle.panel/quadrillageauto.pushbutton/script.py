# -*- coding: utf-8 -*-
__title__ = "Quadrillage\nPersonnalisé"
__doc__ = """Générateur de quadrillages basé sur un point d'origine unique avec indication du nom de la vue active."""
__version__ = "1.0.0"
__author__ = "Riana Stellia"

import os
import re

# .NET / System Imports
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')

from System.Windows.Media import BrushConverter

# Revit & pyRevit Imports
from Autodesk.Revit.DB import (
    XYZ, Line, Grid, GridType, Level, Element,
    Transaction, FilteredElementCollector, BuiltInParameter,
    Color, BuiltInCategory, Category, ElementId
)
from pyrevit import forms, revit, script

# ---------------------------------------------------------------------------
# 1. UTILITAIRES GÉOMÉTRIQUES ET CONVERSIONS
# ---------------------------------------------------------------------------

def parse_distances(text):
    """Extrait une liste de valeurs numériques depuis une chaîne de texte."""
    if not text:
        return []
    cleaned = re.sub(r"[^\d.,;\s-]", "", text).replace(",", ".")
    tokens = re.split(r"[,;\s]+", cleaned.strip())
    return [float(t) for t in tokens if t]

def to_feet(value, unit_idx):
    """Convertit une valeur vers l'unité interne Revit (Pieds).
    0: Mètres (m), 1: Millimètres (mm), 2: Centimètres (cm)
    """
    if unit_idx == 1:   # mm
        return (value / 1000.0) * 3.28084
    elif unit_idx == 2: # cm
        return (value / 100.0) * 3.28084
    return value * 3.28084 # m (par défaut)

def get_coords_cumulees(entraxes):
    """Calcule les coordonnées cumulées absolues à partir d'une liste d'entraxes."""
    coords = [0.0]
    for e in entraxes:
        coords.append(coords[-1] + e)
    return coords

def get_name_sequence(is_alpha, count):
    """Génère la séquence de noms (1, 2, 3... ou A, B, C...)."""
    if not is_alpha:
        return [str(i + 1) for i in range(count)]
    names = []
    for i in range(count):
        curr = i
        name = ""
        while True:
            name = chr(ord('A') + (curr % 26)) + name
            curr = curr // 26 - 1
            if curr < 0:
                break
        names.append(name)
    return names

# ---------------------------------------------------------------------------
# Couleurs des quadrillages
# ---------------------------------------------------------------------------
_RGB_COLOR_VALUES = {
    0: (255, 0, 0),   # Rouge
    1: (0, 0, 0),     # Noir (valeur par défaut)
}

def _color_param_value(rgb):
    return rgb[0] + (rgb[1] << 8) + (rgb[2] << 16)

def find_grid_heads_category(doc):
    """Sous-catégorie Extrémités de quadrillage."""
    target_id = ElementId(BuiltInCategory.OST_GridHeads)
    try:
        cat = Category.GetCategory(doc, target_id)
        if cat:
            return cat
    except:
        pass
    try:
        parent = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Grids)
    except:
        parent = None
    if parent is not None:
        try:
            for sub in parent.SubCategories:
                if sub.Id == target_id:
                    return sub
        except:
            pass
    return None

# ---------------------------------------------------------------------------
# 2. INTERFACE UTILISATEUR & GESTION DES DÉBORDEMENTS/PLACEHOLDERS
# ---------------------------------------------------------------------------

class GridCustomPlacementWindow(forms.WPFWindow):
    def __init__(self, xaml_path, doc):
        forms.WPFWindow.__init__(self, xaml_path)
        self.doc = doc
        self.uidoc = __revit__.ActiveUIDocument

        # Niveau actif et nom de la vue active
        self.active_view = doc.ActiveView
        self.view_name = self.active_view.Name if self.active_view else "Vue active"
        self.current_level = getattr(self.active_view, "GenLevel", None) or getattr(self.active_view, "Level", None)
        level_name = self.current_level.Name if self.current_level else self.view_name
        if hasattr(self, 'lbl_level_badge'):
            self.lbl_level_badge.Text = level_name

        # Conversion de couleurs pour les Placeholders
        self.brush_muted = BrushConverter().ConvertFromString("#5E6B78")
        self.brush_ink = BrushConverter().ConvertFromString("#1B2A3A")

        # Configuration des Placeholders sur les axes X et Y
        self.setup_placeholder(self.txt_dist_x, "3, 4, 5, 5")
        self.setup_placeholder(self.txt_dist_y, "3, 4, 5, 5")

        # Alimentation des types de quadrillages du modèle
        self.grid_types = list(FilteredElementCollector(doc).OfClass(GridType).WhereElementIsElementType())
        self.cb_grid_type.Items.Clear()
        for gt in self.grid_types:
            p_name = gt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
            name = p_name.AsString() if p_name else "Quadrillage"
            self.cb_grid_type.Items.Add(name)
        if self.cb_grid_type.Items.Count > 0:
            self.cb_grid_type.SelectedIndex = 0

        # Événements en temps réel (Live Preview)
        self.txt_dist_x.TextChanged += self.on_inputs_changed
        self.txt_dist_y.TextChanged += self.on_inputs_changed
        self.cb_unit.SelectionChanged += self.on_inputs_changed
        self.txt_offset.TextChanged += self.on_inputs_changed

        # Boutons de réglage du débordement
        if hasattr(self, 'btn_off_up'):
            self.btn_off_up.Click += self.on_offset_up
        if hasattr(self, 'btn_off_down'):
            self.btn_off_down.Click += self.on_offset_down

        # Événements principaux
        self.btn_create.Click += self.on_create
        self.btn_cancel.Click += self.on_cancel

        # Premier calcul d'aperçu à l'ouverture
        self.update_preview()

    def setup_placeholder(self, textbox, placeholder_text):
        """Configure un texte indicatif (placeholder) sur un TextBox."""
        textbox.Tag = placeholder_text
        textbox.Text = placeholder_text
        textbox.Foreground = self.brush_muted

        def on_got_focus(sender, e):
            if sender.Text == sender.Tag:
                sender.Text = ""
                sender.Foreground = self.brush_ink

        def on_lost_focus(sender, e):
            if not sender.Text or sender.Text.strip() == "":
                sender.Text = sender.Tag
                sender.Foreground = self.brush_muted

        textbox.GotFocus += on_got_focus
        textbox.LostFocus += on_lost_focus

    def get_clean_text(self, textbox):
        """Récupère la valeur du TextBox en ignorant le placeholder."""
        val = textbox.Text.strip() if textbox.Text else ""
        if val == "" or val == str(textbox.Tag):
            return ""
        return val

    def on_offset_up(self, sender, args):
        try:
            curr = float(self.txt_offset.Text.replace(",", "."))
        except:
            curr = 1.0
        self.txt_offset.Text = "{:.1f}".format(curr + 0.5)

    def on_offset_down(self, sender, args):
        try:
            curr = float(self.txt_offset.Text.replace(",", "."))
        except:
            curr = 1.0
        new_val = max(0.0, curr - 0.5)
        self.txt_offset.Text = "{:.1f}".format(new_val)

    def on_inputs_changed(self, sender, args):
        self.update_preview()

    def update_preview(self):
        """Mise à jour dynamique de l'emprise en temps réel."""
        try:
            raw_x = self.get_clean_text(self.txt_dist_x)
            raw_y = self.get_clean_text(self.txt_dist_y)

            if not raw_x or not raw_y:
                self.txt_preview_dims.Text = "Veuillez renseigner les listes d'entraxes X et Y."
                return

            d_x = parse_distances(raw_x)
            d_y = parse_distances(raw_y)

            if not d_x or not d_y:
                self.txt_preview_dims.Text = "Format de liste incomplet ou invalide."
                return

            rel_x = get_coords_cumulees(d_x)
            rel_y = get_coords_cumulees(d_y)

            unit_symbols = ["m", "mm", "cm"]
            unit_sym = unit_symbols[self.cb_unit.SelectedIndex]

            if hasattr(self, 'lbl_offset'):
                self.lbl_offset.Text = "Débordement ({})".format(unit_sym)

            self.txt_preview_dims.Text = "Emprise : {:.2f} {} × {:.2f} {} ({} files X × {} files Y)".format(
                rel_x[-1], unit_sym, rel_y[-1], unit_sym, len(rel_x), len(rel_y)
            )
        except Exception:
            self.txt_preview_dims.Text = "Format de saisie incorrect."

    def on_cancel(self, sender, args):
        self.Close()

    def on_create(self, sender, args):
        doc = self.doc
        uidoc = self.uidoc
        
        # 1. Validation rigoureuse des listes avant toute action
        raw_x = self.get_clean_text(self.txt_dist_x)
        raw_y = self.get_clean_text(self.txt_dist_y)

        if not raw_x:
            forms.alert("Vous n'avez pas entré la liste des entraxes pour les axes verticaux (X).", title="Champ manquant", warn_icon=True)
            self.txt_dist_x.Focus()
            return

        if not raw_y:
            forms.alert("Vous n'avez pas entré la liste des entraxes pour les axes horizontaux (Y).", title="Champ manquant", warn_icon=True)
            self.txt_dist_y.Focus()
            return

        try:
            d_x = parse_distances(raw_x)
        except:
            d_x = []

        if not d_x:
            forms.alert("La liste des entraxes X est invalide ou vide. Veuillez entrer des nombres séparés par des virgules (ex: 3, 4, 5).", title="Liste invalide", warn_icon=True)
            self.txt_dist_x.Focus()
            return

        try:
            d_y = parse_distances(raw_y)
        except:
            d_y = []

        if not d_y:
            forms.alert("La liste des entraxes Y est invalide ou vide. Veuillez entrer des nombres séparés par des virgules (ex: 3, 4, 5).", title="Liste invalide", warn_icon=True)
            self.txt_dist_y.Focus()
            return

        try:
            offset_val = float(self.txt_offset.Text.replace(",", "."))
            unit_idx = self.cb_unit.SelectedIndex
        except Exception as e:
            forms.alert("Erreur dans les valeurs saisies : {}".format(e), title="Erreur")
            return

        # 2. Masquage temporaire de la fenêtre pour la sélection du point d'origine
        self.Hide()

        try:
            # Pop-up d'information incluant dynamiquement le nom de la vue active
            message_texte = "Veuillez placer un point dans la vue '{}' qui servira d'origine à votre quadrillage.".format(self.view_name)
            forms.alert(
                message_texte,
                title="Placement du Point d'Origine",
                warn_icon=False
            )

            # Saisie interactive du point d'origine dans Revit
            pt_origin = uidoc.Selection.PickPoint("Cliquez sur le point d'origine du quadrillage")
        except Exception:
            # Gère proprement l'annulation par l'utilisateur (touche Échap / ESC)
            self.Show()
            return

        # 3. Calculs géométriques basés sur l'origine sélectionnée
        rel_x = get_coords_cumulees(d_x)
        rel_y = get_coords_cumulees(d_y)

        coords_x = [to_feet(x, unit_idx) for x in rel_x]
        coords_y = [to_feet(y, unit_idx) for y in rel_y]
        offset_ft = to_feet(offset_val, unit_idx)

        xmin, xmax = coords_x[0], coords_x[-1]
        ymin, ymax = coords_y[0], coords_y[-1]

        level_z = self.current_level.Elevation if self.current_level else 0.0
        levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
        elevations = [l.Elevation for l in levels] if levels else [level_z]
        min_z = min(elevations) - 3.28084
        max_z = max(elevations) + 3.28084

        names_x = get_name_sequence(self.txt_start_x.SelectedIndex == 1, len(coords_x))
        names_y = get_name_sequence(self.txt_start_y.SelectedIndex == 1, len(coords_y))
        selected_type = self.grid_types[self.cb_grid_type.SelectedIndex] if self.grid_types else None

        # 4. Transaction unique Revit : Création des quadrillages et application des styles
        t = Transaction(doc, "Créer Quadrillage par Origine")
        t.Start()
        try:
            color_choice = self.cb_color.SelectedIndex  # 0: Rouge, 1: Noir, 2: Conserver
            rgb = _RGB_COLOR_VALUES.get(color_choice)
            if rgb is not None:
                if selected_type:
                    try:
                        p_col = selected_type.get_Parameter(BuiltInParameter.LINE_COLOR)
                        if p_col and not p_col.IsReadOnly:
                            p_col.Set(_color_param_value(rgb))
                    except:
                        pass

                heads_category = find_grid_heads_category(doc)
                if heads_category is not None:
                    try:
                        heads_category.LineColor = Color(rgb[0], rgb[1], rgb[2])
                    except:
                        pass

            created_count = 0

            # TRACÉ DES AXES VERTICAUX (X)
            for i, x in enumerate(coords_x):
                p_start = XYZ(pt_origin.X + x, pt_origin.Y + ymin - offset_ft, pt_origin.Z)
                p_end   = XYZ(pt_origin.X + x, pt_origin.Y + ymax + offset_ft, pt_origin.Z)

                grid = Grid.Create(doc, Line.CreateBound(p_start, p_end))
                if selected_type:
                    grid.ChangeTypeId(selected_type.Id)
                if levels:
                    grid.SetVerticalExtents(min_z, max_z)
                try:
                    grid.Name = names_x[i]
                except:
                    pass
                created_count += 1

            # TRACÉ DES AXES HORIZONTAUX (Y)
            for i, y in enumerate(coords_y):
                p_start = XYZ(pt_origin.X + xmin - offset_ft, pt_origin.Y + y, pt_origin.Z)
                p_end   = XYZ(pt_origin.X + xmax + offset_ft, pt_origin.Y + y, pt_origin.Z)

                grid = Grid.Create(doc, Line.CreateBound(p_start, p_end))
                if selected_type:
                    grid.ChangeTypeId(selected_type.Id)
                if levels:
                    grid.SetVerticalExtents(min_z, max_z)
                try:
                    grid.Name = names_y[i]
                except:
                    pass
                created_count += 1

            t.Commit()
            forms.alert("Quadrillages créés avec succès!".format(created_count), title="Succès")
            self.Close()

        except Exception as err:
            t.RollBack()
            forms.alert("Erreur lors de la création : {}".format(err), title="Erreur")
            self.Show()

# ---------------------------------------------------------------------------
# POINT D'ENTRÉE DU SCRIPT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    doc = revit.doc
    if doc:
        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        win = GridCustomPlacementWindow(xaml_path, doc)
        win.ShowDialog()
    else:
        forms.alert("Aucun document Revit actif.", title="Erreur")