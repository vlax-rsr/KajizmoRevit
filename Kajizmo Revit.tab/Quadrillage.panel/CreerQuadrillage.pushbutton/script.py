# -*- coding: utf-8 -*-
"""
Générateur de Quadrillages Revit (Stand-Alone)
Crée un seul réseau de quadrillages sur le niveau actif, avec une étendue verticale
traversant tous les niveaux, visible en 3D sur ce niveau, et avec un débordement exact.

Auteur : Riana
"""

__title__ = "Créer\nQuadrillage"
__doc__ = """Génération de quadrillages Revit : réseau sur niveau actif, étendue Z tous niveaux, visible en 3D, couleur et débordement maîtrisés."""

import os
import sys
import re

# Revit & pyRevit Imports
from Autodesk.Revit.DB import (
    XYZ, Line, Grid, GridType, Level, View3D, Element, Color, Category,
    Transaction, FilteredElementCollector, BuiltInCategory, BuiltInParameter, ElementId
)
from pyrevit import forms, revit, script

# .NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List
from System.Windows import Visibility

# ---------------------------------------------------------------------------
# Imports hoistés : résolus une seule fois au chargement du module
# (l'import dans chaque appel de get_element_name coûtait un dictionnaire
#  d'import par élément traité).
# ---------------------------------------------------------------------------
try:
    from pyrevit.revit import query as _rv_query
    _rv_get_name = _rv_query.get_name
except Exception:
    _rv_get_name = None

# ---------------------------------------------------------------------------
# Pré-processeur de failures : supprime les avertissements Revit pour que
# l'API n'ouvre jamais de dialogue modal (le point n°1 des "scripts lents").
# ---------------------------------------------------------------------------
try:
    from Autodesk.Revit.DB import (
        FailuresPreprocessor, FailureProcessingResult, FailureSeverity
    )
    _HAS_FAILURES_API = True
except Exception:
    _HAS_FAILURES_API = False

if _HAS_FAILURES_API:
    class _IgnoreWarnings(FailuresPreprocessor):
        def PreprocessFailures(self, failuresAccessor):
            try:
                for msg in failuresAccessor.GetFailureMessages():
                    if msg.GetSeverity() == FailureSeverity.Warning:
                        failuresAccessor.DeleteWarning(msg)
            except Exception:
                pass
            return FailureProcessingResult.Continue


def _ids_equal(id_a, id_b):
    """Comparaison d'ElementId fiable sous IronPython comme sous CPython3."""
    if id_a is None or id_b is None:
        return id_a is id_b
    try:
        return bool(id_a.Equals(id_b))
    except Exception:
        try:
            return bool(id_a == id_b)
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Couleurs des quadrillages
# ---------------------------------------------------------------------------
# Couleur de ligne Revit stockée en entier : rouge + (vert << 8) + (bleu << 16)
_RGB_COLOR_VALUES = {
    0: (255, 0, 0),   # Rouge
    1: (0, 0, 0),     # Noir (valeur par défaut)
}

# Type de quadrillage proposé par défaut dans la liste.
DEFAULT_GRID_TYPE_NAME = "Bulle 6.5mm"


def _color_param_value(rgb):
    return rgb[0] + (rgb[1] << 8) + (rgb[2] << 16)


def _normalized_name(value):
    return re.sub(r"[^0-9a-z]", "", (value or "").lower())


def find_grid_heads_category(doc):
    """Sous-catégorie « Extrémités de quadrillage » (style d'objet)."""
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
                if _ids_equal(sub.Id, target_id):
                    return sub
        except:
            pass
        try:
            for sub in parent.SubCategories:
                name = (get_element_name(sub) or "").lower()
                if "xtr" in name and "quadrillage" in name:
                    return sub
        except:
            pass
    try:
        for cat in doc.Settings.Categories:
            if _ids_equal(cat.Id, target_id):
                return cat
    except:
        pass
    return None


# ---------------------------------------------------------------------------
# Compatibilité IronPython pour les noms d'éléments Revit
# ---------------------------------------------------------------------------
def get_element_name(elem):
    """
    Récupère le nom d'un élément Revit de manière 100% compatible IronPython.
    Évite l'exception AttributeError: Name propre au runtime IronPython.
    """
    if not elem:
        return ""
    if _rv_get_name is not None:
        try:
            name = _rv_get_name(elem)
            if name:
                return str(name)
        except:
            pass
    try:
        name = Element.Name.GetValue(elem)
        if name:
            return str(name)
    except:
        pass
    try:
        name = Element.Name.__get__(elem)
        if name:
            return str(name)
    except:
        pass
    try:
        return str(elem.Name)
    except:
        pass
    try:
        p = elem.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        if p and p.AsString():
            return p.AsString()
        p = elem.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if p and p.AsString():
            return p.AsString()
    except:
        pass
    return "Grid_{}".format(elem.Id.ToString())


# Stratégie d'écriture du nom mémorisée : la première tentative (qui échoue
# toujours sous IronPython) n'est testée qu'une fois au lieu d'une fois par
# quadrillage créé.
_NAME_STRATEGIES = ("attr", "setvalue", "set")
_name_strategy = None


def _try_set_name(elem, new_name, strategy):
    try:
        if strategy == "attr":
            elem.Name = new_name
        elif strategy == "setvalue":
            Element.Name.SetValue(elem, new_name)
        else:
            Element.Name.__set__(elem, new_name)
        return True
    except:
        return False


def set_element_name(elem, new_name):
    """Définit le nom d'un élément Revit de manière compatible IronPython."""
    global _name_strategy
    if _name_strategy:
        if _try_set_name(elem, new_name, _name_strategy):
            return True
    for strategy in _NAME_STRATEGIES:
        if strategy != _name_strategy:
            if _try_set_name(elem, new_name, strategy):
                _name_strategy = strategy
                return True
    return False


def get_current_level(doc):
    """Détecte le niveau sur lequel se trouve l'utilisateur."""
    active_view = doc.ActiveView
    current_level = None
    if hasattr(active_view, "GenLevel") and active_view.GenLevel:
        current_level = active_view.GenLevel
    elif hasattr(active_view, "Level") and active_view.Level:
        current_level = active_view.Level
    elif (hasattr(active_view, "LevelId")
          and not _ids_equal(active_view.LevelId, ElementId.InvalidElementId)):
        current_level = doc.GetElement(active_view.LevelId)

    if not current_level:
        levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
        if levels:
            current_level = levels[0]
    return current_level


# ---------------------------------------------------------------------------
# Utilitaires de conversion et de nommage
# ---------------------------------------------------------------------------
def parse_distances(text):
    """Analyse une chaîne utilisateur et extrait la liste de flottants."""
    if not text:
        return []
    t = text.strip().strip("[]")
    if ";" in t:
        tokens = t.split(";")
        return [float(tok.strip().replace(",", ".")) for tok in tokens if tok.strip()]
    if re.search(r"\d,\d", t) and " " in t:
        t = re.sub(r"(\d),(\d)", r"\1.\2", t)
    tokens = re.split(r"[, \t]+", t)
    return [float(tok.strip().replace(",", ".")) for tok in tokens if tok.strip()]


def to_internal_feet(val, unit_idx):
    """Convertit une distance saisie vers l'unité interne de Revit (pieds)."""
    # 0: Mètres, 1: Millimètres, 2: Centimètres
    if unit_idx == 0:   # m
        return val / 0.3048
    elif unit_idx == 1: # mm
        return (val / 1000.0) / 0.3048
    elif unit_idx == 2: # cm
        return (val / 100.0) / 0.3048
    return val / 0.3048


def cumulative(values):
    """Sommes cumulées préfixées : [0, d0, d0+d1, ...]"""
    out = [0.0]
    running = 0.0
    for v in values:
        running += v
        out.append(running)
    return out


def get_grid_name_sequence(start_name, count):
    """Génère une suite de noms de quadrillages (ex: 1, 2, 3... ou A, B, C... AA)."""
    start_name = (start_name or "").strip()
    if not start_name:
        start_name = "1"

    if start_name.isdigit():
        start_num = int(start_name)
        return [str(start_num + i) for i in range(count)]
    elif len(start_name) == 1 and start_name.isalpha():
        is_upper = start_name.isupper()
        start_code = ord(start_name.upper()) - ord('A')
        names = []
        for i in range(count):
            curr = start_code + i
            name = ""
            while True:
                name = chr(ord('A') + (curr % 26)) + name
                curr = curr // 26 - 1
                if curr < 0:
                    break
            names.append(name if is_upper else name.lower())
        return names
    else:
        return ["{}_{}".format(start_name, i + 1) for i in range(count)]


# ---------------------------------------------------------------------------
# Interface Utilisateur (WPF)
# ---------------------------------------------------------------------------
class GridGeneratorWindow(forms.WPFWindow):
    def __init__(self, xaml_file_name, doc):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.doc = doc

        # Détection du niveau actif
        self.current_level = get_current_level(self.doc)
        level_display = get_element_name(self.current_level) if self.current_level else "Niveau 0"
        self.lbl_level_badge.Text = level_display
        self.lbl_header_subtitle.Text = "Réseau sur {} — Étendue tous niveaux & 3D".format(level_display)

        # Récupération et alimentation des GridTypes du modèle
        self.grid_types = []
        self.load_model_grid_types()

        # Événements de mise à jour dynamique
        self.txt_dist_x.TextChanged += self.on_input_changed
        self.txt_dist_y.TextChanged += self.on_input_changed
        self.cb_unit.SelectionChanged += self.on_input_changed
        self.txt_offset.TextChanged += self.on_input_changed

        # Événements boutons
        self.btn_create.Click += self.on_create
        self.btn_cancel.Click += self.on_cancel

        self.update_preview()

    def load_model_grid_types(self):
        """Récupère les types de quadrillages disponibles dans le document sans modifier leurs propriétés."""
        collector = FilteredElementCollector(self.doc).OfClass(GridType).WhereElementIsElementType()
        self.grid_types = list(collector)

        self.cb_grid_type.Items.Clear()
        selected_index = 0

        # Vérifie si un quadrillage existe déjà dans le modèle pour sélectionner son type par défaut
        existing_grid = FilteredElementCollector(self.doc).OfClass(Grid).FirstElement()
        default_type_id = existing_grid.GetTypeId() if existing_grid else None

        # « Bulle 6.5mm » est proposé en priorité, sinon le type du quadrillage existant
        preferred_name = _normalized_name(DEFAULT_GRID_TYPE_NAME)
        preferred_index = None

        for idx, gt in enumerate(self.grid_types):
            type_name = get_element_name(gt)
            self.cb_grid_type.Items.Add(type_name)
            if preferred_index is None and _normalized_name(type_name) == preferred_name:
                preferred_index = idx
            if default_type_id and _ids_equal(gt.Id, default_type_id):
                selected_index = idx

        if preferred_index is not None:
            selected_index = preferred_index

        if self.cb_grid_type.Items.Count > 0:
            self.cb_grid_type.SelectedIndex = selected_index

    def get_unit_symbol(self):
        idx = self.cb_unit.SelectedIndex
        return "m" if idx == 0 else ("mm" if idx == 1 else "cm")

    def on_input_changed(self, sender, args):
        self.update_preview()

    def update_preview(self):
        unit_sym = self.get_unit_symbol()
        try:
            d_x = parse_distances(self.txt_dist_x.Text)
            d_y = parse_distances(self.txt_dist_y.Text)

            if not d_x or not d_y:
                self.txt_status.Text = "Saisissez au moins une distance positive pour chaque axe."
                self.txt_status.Visibility = Visibility.Visible
                self.btn_create.IsEnabled = False
                return

            # Calcul des sommes cumulées
            total_x = cumulative(d_x)
            total_y = cumulative(d_y)

            self.txt_preview_dims.Text = "Emprise : {:.2f} {} × {:.2f} {} ({} × {} files)".format(
                total_x[-1], unit_sym, total_y[-1], unit_sym, len(total_x), len(total_y)
            )

            self.txt_status.Visibility = Visibility.Collapsed
            self.btn_create.IsEnabled = True

        except Exception:
            self.txt_status.Text = "Erreur de format dans les distances saisies."
            self.txt_status.Visibility = Visibility.Visible
            self.btn_create.IsEnabled = False

    def on_cancel(self, sender, args):
        self.Close()

    def on_create(self, sender, args):
        doc = self.doc
        if not doc:
            forms.alert("Aucun document Revit actif.", title="Erreur")
            return

        try:
            d_x = parse_distances(self.txt_dist_x.Text)
            d_y = parse_distances(self.txt_dist_y.Text)
            unit_idx = self.cb_unit.SelectedIndex

            try:
                offset_val = float(self.txt_offset.Text.replace(",", "."))
            except:
                offset_val = 0.0

            # Conversion du débordement en pieds Revit
            offset_ft = to_internal_feet(offset_val, unit_idx)

            # Calcul des positions cumulées
            total_x = cumulative(d_x)
            total_y = cumulative(d_y)

            coords_x_ft = [to_internal_feet(x, unit_idx) for x in total_x]
            coords_y_ft = [to_internal_feet(y, unit_idx) for y in total_y]

            min_x_ft = 0.0
            max_x_ft = coords_x_ft[-1]
            min_y_ft = 0.0
            max_y_ft = coords_y_ft[-1]

            # Altitude Z du niveau où se trouve l'utilisateur
            level_z = self.current_level.Elevation if self.current_level else 0.0
            current_level_id = self.current_level.Id if self.current_level else None

            # Noms des axes
            names_x = get_grid_name_sequence(self.txt_start_x.Text, len(coords_x_ft))
            names_y = get_grid_name_sequence(self.txt_start_y.Text, len(coords_y_ft))

            # Récupération du type de Grid sélectionné
            selected_grid_type = None
            idx_type = self.cb_grid_type.SelectedIndex
            if 0 <= idx_type < len(self.grid_types):
                selected_grid_type = self.grid_types[idx_type]
            type_id = selected_grid_type.Id if selected_grid_type else None

            # --- Collectes hors transaction (aucun document n'est encore modifié) ---
            levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
            min_z = level_z - 10.0
            max_z = level_z + 20.0
            if levels:
                elevs = [l.Elevation for l in levels]
                min_z = min(elevs) - 3.28084  # 1 m sous le niveau le plus bas
                max_z = max(elevs) + 3.28084  # 1 m au-dessus du niveau le plus haut

            # Récupération des noms existants dans le document pour éviter les collisions
            existing_grids = FilteredElementCollector(doc).OfClass(Grid).ToElements()
            existing_names = set([get_element_name(g) for g in existing_grids])

            # Les vues 3D existent déjà : elles sont collectées avant la transaction
            views_3d = [v3d for v3d in FilteredElementCollector(doc).OfClass(View3D).ToElements()
                        if not v3d.IsTemplate]
            grid_cat_id = ElementId(BuiltInCategory.OST_Grids)

            grids_created_count = 0

            # Option couleur texte / ligne
            color_choice = self.cb_color.SelectedIndex  # 0: Rouge, 1: Noir, 2: Conserver

            # Transaction Revit unique : une seule régénération du document.
            t = Transaction(doc, "Créer Quadrillages")
            preproc = _IgnoreWarnings() if _HAS_FAILURES_API else None
            if preproc is not None:
                try:
                    t.SetFailuresPreprocessor(preproc)
                    preproc = None
                except:
                    pass
            t.Start()
            if preproc is not None:
                try:
                    t.SetFailuresPreprocessor(preproc)
                except:
                    pass

            try:
                # Ajustement de la couleur du type ET des extrémités (style d'objet)
                # pour que l'extrémité de ligne soit toujours de la même couleur
                # que le quadrillage.
                rgb = _RGB_COLOR_VALUES.get(color_choice)
                if rgb is not None:
                    if selected_grid_type:
                        try:
                            p_col = selected_grid_type.get_Parameter(BuiltInParameter.LINE_COLOR)
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

                # Axes verticaux (X fixes) puis horizontaux (Y fixes), dans l'ordre d'origine.
                jobs = []
                for i, x_ft in enumerate(coords_x_ft):
                    jobs.append((x_ft, max_y_ft, min_y_ft, True, names_x[i]))
                for i, y_ft in enumerate(coords_y_ft):
                    jobs.append((y_ft, max_x_ft, min_x_ft, False, names_y[i]))

                for coord, span_max, span_min, is_vertical, desired_name in jobs:
                    # Le tracé déborde de `offset_ft` aux deux extrémités,
                    # SANS Maximize3DExtents() pour préserver ce débordement exact.
                    if is_vertical:
                        start_pt = XYZ(coord, span_max + offset_ft, level_z)
                        end_pt = XYZ(coord, span_min - offset_ft, level_z)
                    else:
                        start_pt = XYZ(span_max + offset_ft, coord, level_z)
                        end_pt = XYZ(span_min - offset_ft, coord, level_z)

                    grid = Grid.Create(doc, Line.CreateBound(start_pt, end_pt))

                    # Affectation du type : on ne change le type que s'il diffère
                    # déjà (GetTypeId est bien moins coûteux que ChangeTypeId).
                    if type_id is not None:
                        try:
                            if not _ids_equal(grid.GetTypeId(), type_id):
                                grid.ChangeTypeId(type_id)
                        except:
                            pass

                    # Étendues verticales traversant TOUS les niveaux
                    if levels:
                        try:
                            grid.SetVerticalExtents(min_z, max_z)
                        except:
                            pass

                    # Affectation du nom désiré
                    if desired_name not in existing_names:
                        if set_element_name(grid, desired_name):
                            existing_names.add(desired_name)

                    grids_created_count += 1

                # 3. Visibilité du réseau de quadrillages en 3D UNIQUEMENT sur le niveau actif.
                #    On ne modifie une vue que si elle n'est pas déjà dans l'état voulu
                #    (Show/HideGridsOnLevel déclenche une régénération de la vue).
                for v3d in views_3d:
                    needs_unhide = True
                    try:
                        needs_unhide = v3d.IsCategoryHidden(grid_cat_id)
                    except:
                        needs_unhide = True
                    if needs_unhide:
                        try:
                            if v3d.CanCategoryBeHidden(grid_cat_id):
                                v3d.SetCategoryHidden(grid_cat_id, False)
                        except:
                            pass

                    already_showing = False
                    try:
                        for lvl_id in v3d.GetLevelsThatShowGrids():
                            if current_level_id is not None and _ids_equal(lvl_id, current_level_id):
                                already_showing = True
                            else:
                                try:
                                    v3d.HideGridsOnLevel(lvl_id)
                                except:
                                    pass
                    except:
                        pass

                    if current_level_id is not None and not already_showing:
                        try:
                            v3d.ShowGridsOnLevel(current_level_id)
                        except:
                            pass

                t.Commit()
            except Exception as t_err:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise t_err

            # Désélectionne tout pour éviter que les éléments soient surlignés en bleu
            try:
                uidoc = __revit__.ActiveUIDocument
                if uidoc:
                    uidoc.Selection.SetElementIds(List[ElementId]())
            except:
                pass

            self.Close()
            level_display = get_element_name(self.current_level) if self.current_level else "Niveau actif"
            type_name_display = get_element_name(selected_grid_type) if selected_grid_type else "Par défaut"
            forms.alert(
                "{} quadrillages créés avec succès !\n\n"
                "- Réseau créé sur : {}\n"
                "- Étendue verticale : traverse tous les niveaux\n"
                "- Vue 3D : réseau actif sur {}\n"
                "- Débordement appliqué : {} {}\n"
                "- Type : {}\n"
                "- Emprise : {:.2f} × {:.2f} {}".format(
                    grids_created_count,
                    level_display,
                    level_display,
                    offset_val,
                    self.get_unit_symbol(),
                    type_name_display,
                    total_x[-1],
                    total_y[-1],
                    self.get_unit_symbol()
                ),
                title="Quadrillages Créés",
                warn_icon=False
            )

        except Exception as err:
            forms.alert("Une erreur est survenue lors de la création :\n{}".format(err), title="Erreur")


# ---------------------------------------------------------------------------
# Point d'entrée du script (Stand-Alone)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    doc = revit.doc
    if not doc:
        try:
            doc = __revit__.ActiveUIDocument.Document
        except:
            doc = None

    if not doc:
        forms.alert("Aucun document Revit actif. Veuillez ouvrir un projet Revit.", title="Erreur")
        script.exit()

    bundle_dir = os.path.dirname(__file__)
    xaml_path = os.path.join(bundle_dir, "ui.xaml")
    win = GridGeneratorWindow(xaml_path, doc)
    win.ShowDialog()
