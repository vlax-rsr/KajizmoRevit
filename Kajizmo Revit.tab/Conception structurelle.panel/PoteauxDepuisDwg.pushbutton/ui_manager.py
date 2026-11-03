# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

import clr
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')

from System.Windows import (
    Thickness, CornerRadius, GridLength, GridUnitType,
    HorizontalAlignment, VerticalAlignment, TextTrimming, FontWeights, Visibility
)
from System.Windows.Controls import (
    Grid, ColumnDefinition, RowDefinition, Border, CheckBox, TextBlock
)
from System.Windows.Documents import Run
from System.Windows.Media import BrushConverter

from pyrevit import forms, revit

from app_config import ConfigManager
from logger import UserLogger
from validator import DataValidator
from revit_utils import get_name, PIED_EN_M
from dwg_service import DwgBlockService
from column_service import ColumnTypeService


def _brush(hex_color):
    return BrushConverter().ConvertFromString(hex_color)


class PoteauWindow(forms.WPFWindow):
    """
    Déroulé de saisie :
      1. choix du DWG              (cb_dwg)     -> analyse automatique à l'ouverture
                                                   et à chaque changement de DWG
      2. choix de la famille       (cb_famille) -> vérification automatique (test à blanc annulé)
      3. dimensions détectées      (panel_blocs : une carte = une dimension -> un type)
      4. aperçu puis création      (txt_preview / btn_create)

    Les options d'implantation (rotation des blocs, correction d'orientation,
    pose au centre de la forme) sont toujours appliquées.
    """

    def __init__(self, xaml_path=None):
        if xaml_path is None:
            xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)

        self.doc = revit.doc
        self.cfg = ConfigManager()
        self.logger = UserLogger()
        self.validator = DataValidator()
        self.dwg_service = DwgBlockService(self.doc)

        self.rows = []              # [{"groupe", "chk", "lbl_type"}]
        self.groupes = []           # groupes de dimensions du DWG courant
        self.sans_dims = []         # blocs non mesurables (ignorés)
        self.dwg_map = {}           # libellé -> ImportInstance
        self.familles = {}          # nom de famille -> [FamilySymbol]
        self.family_info = None     # résultat de check_family si la famille est valide
        self.family_msg = None      # message de la dernière vérification
        self._loading = False

        self.brush_white = _brush("#FFFFFF")
        self.brush_line = _brush("#E2E8F0")
        self.brush_navy = _brush("#17365D")
        self.brush_muted = _brush("#5E6B78")
        self.brush_red = _brush("#C9372C")

        # --- titre, dimensions, pied de page -----------------------------
        try:
            self.Title = "Kajizmo Revit - {} {} - v{}".format(
                self.cfg.get('title', "Poteaux"),
                self.cfg.get('subtitle', "types auto"),
                self.cfg.get('version', "1.0.0")).replace("  ", " ")
            w = self.cfg.get('ui.window_width')
            h = self.cfg.get('ui.window_height')
            if w:
                self.Width = float(w)
            if h:
                self.Height = float(h)
            self.MinWidth = min(self.MinWidth, self.Width)
            self.MinHeight = min(self.MinHeight, self.Height)
            if hasattr(self, 'lbl_footer_info') and self.lbl_footer_info is not None:
                self.lbl_footer_info.Text = "©2026 {}".format(self.cfg.get('author', "R. Stellia"))
        except Exception:
            pass

        # --- vue active et niveau de base --------------------------------
        self.active_view = self.doc.ActiveView
        self.view_name = get_name(self.active_view) or "Vue active"
        self.current_level = getattr(self.active_view, "GenLevel", None)
        niveau_txt = ""
        if self.current_level is not None:
            niveau_txt = " ({:.2f} m)".format(self.current_level.Elevation * PIED_EN_M)
        if hasattr(self, 'lbl_view_badge') and self.lbl_view_badge is not None:
            self.lbl_view_badge.Text = "Vue active : {}{}".format(self.view_name, niveau_txt)

        # --- familles de poteaux -----------------------------------------
        self.column_service = None
        self._loading = True
        if self.current_level is None:
            self.show_status("La vue active n'est pas une vue en plan associée à un niveau. "
                             "Placez-vous sur un plan d'étage avant d'implanter les poteaux.")
        else:
            self.column_service = ColumnTypeService(self.doc, self.current_level)
            self.familles = self.column_service.list_families()
            for nom in self.familles.keys():
                self.cb_famille.Items.Add(nom)
            if not self.familles:
                self.show_status("Aucune famille de poteau structurel n'est chargée dans ce projet.")

        # --- liste des DWG ------------------------------------------------
        self.cb_dwg.Items.Clear()
        try:
            self.dwg_map = self.dwg_service.list_dwgs(self.active_view)
        except Exception as ex:
            self.dwg_map = {}
            self.logger.error("Liste DWG impossible : {}".format(ex))
        for label in self.dwg_map.keys():
            self.cb_dwg.Items.Add(label)
        if self.cb_dwg.Items.Count > 0:
            self.cb_dwg.SelectedIndex = 0
        else:
            self.show_status("Aucun fichier DWG trouvé dans le projet.")
        if self.cb_famille.Items.Count == 1:        # une seule famille : choisie d'office
            self.cb_famille.SelectedIndex = 0
        self._loading = False

        # --- événements ---------------------------------------------------
        self.cb_dwg.SelectionChanged += self.on_dwg_changed
        self.cb_famille.SelectionChanged += self.on_famille_changed
        self.btn_select_all.Click += self.on_select_all
        self.btn_select_none.Click += self.on_select_none
        self.btn_create.Click += self.on_create
        self.btn_cancel.Click += self.on_cancel

        if self.cb_dwg.Items.Count > 0:
            self.analyze()
        if self.cb_famille.SelectedItem is not None:
            self.check_famille()
        self.update_preview()
        self.logger.info("Fenêtre PoteauWindow (Poteaux depuis DWG) initialisée - Vue: {}".format(self.view_name))

    # ------------------------------------------------------------------
    # Statut
    # ------------------------------------------------------------------
    def show_status(self, message):
        try:
            self.txt_status.Text = message
            self.txt_status.Visibility = Visibility.Visible
        except Exception:
            pass

    def clear_status(self):
        try:
            self.txt_status.Text = ""
            self.txt_status.Visibility = Visibility.Collapsed
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Étape 1 : DWG -> dimensions
    # ------------------------------------------------------------------
    def on_dwg_changed(self, sender, args):
        if not self._loading:
            self.analyze()

    def analyze(self):
        self.clear_status()
        self.panel_blocs.Children.Clear()
        self.rows = []
        self.groupes = []
        self.sans_dims = []

        label = self.cb_dwg.SelectedItem
        dwg = self.dwg_map.get(label) if label is not None else None
        if dwg is None:
            self.txt_empty.Visibility = Visibility.Visible
            self.update_preview()
            return

        try:
            blocs = self.dwg_service.extract_blocks(dwg, self.active_view)
            self.groupes, self.sans_dims = self.dwg_service.group_by_dimensions(
                blocs,
                tol_cm=float(self.cfg.get("tolerances.dimensions_cm", 1.5)),
                arrondi_cm=float(self.cfg.get("types.arrondi_cm", 0.5)))
        except Exception as ex:
            self.logger.error("Analyse DWG impossible : {}".format(ex))
            self.show_status("Analyse impossible : {}".format(ex))
            self.txt_empty.Visibility = Visibility.Visible
            self.update_preview()
            return

        self.txt_empty.Visibility = Visibility.Collapsed if self.groupes else Visibility.Visible
        for g in self.groupes:
            self.add_row(g)

        suspects = self.groupes_suspects(self.groupes)
        if suspects:
            pmin, pmax = self.plage_section()
            self.show_status(
                "⚠ Section(s) hors de la plage réaliste ({:g} à {:g} cm) : {}. "
                "L'unité choisie à l'import du DWG est probablement incorrecte."
                .format(pmin, pmax, ", ".join(g["dims_label"] for g in suspects)))

        self.logger.info("DWG '{}' analysé : {} bloc(s), {} dimension(s), {} sans dimensions".format(
            label, len(blocs), len(self.groupes), len(self.sans_dims)))
        self.refresh_plan()

    def plage_section(self):
        try:
            pmin, pmax = [float(v) for v in self.cfg.get("types.plage_section_cm", [10, 200])]
        except Exception:
            pmin, pmax = 10.0, 200.0
        return pmin, pmax

    def groupes_suspects(self, groupes):
        pmin, pmax = self.plage_section()
        return [g for g in groupes if g["petit"] < pmin or g["grand"] > pmax]

    def add_row(self, groupe):
        """Carte compacte : [case] dimensions [occurrences] / type prévu dessous."""
        border = Border()
        border.Background = self.brush_white
        border.BorderBrush = self.brush_line
        border.BorderThickness = Thickness(1)
        border.CornerRadius = CornerRadius(6)
        border.Padding = Thickness(10, 8, 10, 8)
        border.Margin = Thickness(0, 0, 0, 6)

        grid = Grid()
        # colonnes : case (26 px) | dimensions (*) | occurrences (auto)
        for largeur in (GridLength(26, GridUnitType.Pixel),
                        GridLength(1, GridUnitType.Star),
                        GridLength.Auto):
            cd = ColumnDefinition()
            cd.Width = largeur
            grid.ColumnDefinitions.Add(cd)
        for _ in range(2):
            rd = RowDefinition()
            rd.Height = GridLength.Auto
            grid.RowDefinitions.Add(rd)

        chk = CheckBox()
        chk.IsChecked = True
        chk.VerticalAlignment = VerticalAlignment.Center
        Grid.SetRow(chk, 0)
        Grid.SetColumn(chk, 0)

        info = TextBlock()
        info.VerticalAlignment = VerticalAlignment.Center
        info.TextTrimming = TextTrimming.CharacterEllipsis
        info.Margin = Thickness(0, 0, 8, 0)
        run_dims = Run(groupe["dims_label"])
        run_dims.FontWeight = FontWeights.SemiBold
        run_dims.Foreground = _brush("#1B2A3A")
        info.Inlines.Add(run_dims)
        Grid.SetRow(info, 0)
        Grid.SetColumn(info, 1)

        badge = Border()
        badge.Background = _brush("#DAE3EB")
        badge.CornerRadius = CornerRadius(10)
        badge.Padding = Thickness(8, 2, 8, 2)
        badge.HorizontalAlignment = HorizontalAlignment.Right
        badge.VerticalAlignment = VerticalAlignment.Center
        txt_count = TextBlock()
        txt_count.Text = str(groupe["count"])
        txt_count.FontSize = 11
        txt_count.FontWeight = FontWeights.SemiBold
        txt_count.Foreground = _brush("#17365D")
        badge.Child = txt_count
        Grid.SetRow(badge, 0)
        Grid.SetColumn(badge, 2)

        # ligne 1 : type prévu (mis à jour par refresh_plan)
        lbl_type = TextBlock()
        lbl_type.FontSize = 11
        lbl_type.Foreground = self.brush_muted
        lbl_type.Margin = Thickness(0, 4, 0, 0)
        lbl_type.TextTrimming = TextTrimming.CharacterEllipsis
        lbl_type.Text = "Type : choisissez une famille"
        Grid.SetRow(lbl_type, 1)
        Grid.SetColumn(lbl_type, 1)
        Grid.SetColumnSpan(lbl_type, 2)

        for c in (chk, info, badge, lbl_type):
            grid.Children.Add(c)
        border.Child = grid
        self.panel_blocs.Children.Add(border)

        self.rows.append({"groupe": groupe, "chk": chk, "lbl_type": lbl_type})

        def on_row_changed(sender, args):
            self.update_preview()

        chk.Checked += on_row_changed
        chk.Unchecked += on_row_changed

    # ------------------------------------------------------------------
    # Étape 2 : famille (vérification automatique)
    # ------------------------------------------------------------------
    def on_famille_changed(self, sender, args):
        if not self._loading:
            self.check_famille()

    def check_famille(self):
        self.family_info = None
        self.family_msg = None
        nom = self.cb_famille.SelectedItem
        if nom is None or self.column_service is None:
            self.txt_famille.Text = "Choisissez une famille de poteau."
            self.txt_famille.Foreground = self.brush_muted
            self.refresh_plan()
            return

        try:
            ok, msg, info = self.column_service.check_family(self.familles[nom])
        except Exception as ex:
            ok, msg, info = False, "Vérification impossible : {}".format(ex), None

        self.family_msg = msg
        if ok:
            self.family_info = info
            self.txt_famille.Text = "✔ {}".format(msg)
            self.txt_famille.Foreground = self.brush_navy
            self.logger.info("Famille '{}' validée : {}".format(nom, msg))
        else:
            self.txt_famille.Text = "✖ {}".format(msg)
            self.txt_famille.Foreground = self.brush_red
            self.logger.warning("Famille '{}' refusée : {}".format(nom, msg.replace("\n", " | ")))
        self.refresh_plan()

    # ------------------------------------------------------------------
    # Types prévus pour chaque dimension
    # ------------------------------------------------------------------
    def refresh_plan(self):
        if self.family_info is not None and self.groupes:
            try:
                self.column_service.plan_types(self.groupes, self.family_info)
            except Exception as ex:
                self.logger.error("Plan des types impossible : {}".format(ex))
                self.family_info = None
                self.show_status("Plan des types impossible : {}".format(ex))
        for r in self.rows:
            g = r["groupe"]
            if self.family_info is None:
                r["lbl_type"].Text = "Type : choisissez une famille valide"
                r["lbl_type"].Foreground = self.brush_muted
            elif g.get("existant") is not None:
                r["lbl_type"].Text = "Type existant : {}".format(g["nom_type"])
                r["lbl_type"].Foreground = self.brush_navy
            else:
                r["lbl_type"].Text = "Type à créer : {}".format(g["nom_type"])
                r["lbl_type"].Foreground = self.brush_navy
        self.update_preview()

    # ------------------------------------------------------------------
    # Sélection globale
    # ------------------------------------------------------------------
    def on_select_all(self, sender, args):
        for r in self.rows:
            r["chk"].IsChecked = True

    def on_select_none(self, sender, args):
        for r in self.rows:
            r["chk"].IsChecked = False

    # ------------------------------------------------------------------
    # Étape 4 : aperçu, validation
    # ------------------------------------------------------------------
    def get_options(self):
        """Options d'implantation : lues depuis config.json (avec repli par défaut)."""
        return {
            "use_rotation": bool(self.cfg.get("options.use_rotation", True)),
            "auto_orient": bool(self.cfg.get("options.auto_orient", True)),
            "center_on_shape": bool(self.cfg.get("options.center_on_shape", True)),
        }

    def get_lignes(self):
        return [{"use": bool(r["chk"].IsChecked), "dims": r["groupe"]["dims_label"]}
                for r in self.rows]

    def _validation(self):
        return self.validator.check_selection(
            self.get_lignes(),
            self.cb_famille.SelectedItem,
            self.family_info is not None,
            self.family_msg)

    def update_preview(self):
        try:
            if not self.rows:
                self.txt_preview.Text = "Aucune dimension à afficher."
                self.btn_create.IsEnabled = False
                return

            total = 0
            morceaux = []
            for r in self.rows:
                if not r["chk"].IsChecked:
                    continue
                g = r["groupe"]
                total += g["count"]
                if self.family_info is None:
                    cible = "⚠ famille à valider"
                else:
                    cible = "{} ({})".format(
                        g.get("nom_type", "?"),
                        "existant" if g.get("existant") is not None else "à créer")
                morceaux.append("• {} × {} → {}".format(g["count"], g["dims_label"], cible))

            if not morceaux:
                texte = "Aucune dimension sélectionnée."
            else:
                niveau = get_name(self.current_level) if self.current_level is not None else "?"
                texte = "{} poteau(x) seront créés sur « {} » :\n{}".format(
                    total, niveau, "\n".join(morceaux))
            if self.sans_dims:
                texte += "\n⚠ {} bloc(s) sans dimensions mesurables : ignorés.".format(len(self.sans_dims))
            self.txt_preview.Text = texte

            ok, _erreurs = self._validation()
            self.btn_create.IsEnabled = bool(ok and self.column_service is not None)
        except Exception as ex:
            self.txt_preview.Text = "Aperçu indisponible : {}".format(ex)
            self.logger.error("Erreur update_preview: {}".format(ex))

    # ------------------------------------------------------------------
    # Boutons
    # ------------------------------------------------------------------
    def on_cancel(self, sender, args):
        self.logger.info("Annulation par l'utilisateur")
        self.Close()

    def on_create(self, sender, args):
        if self.column_service is None:
            forms.alert("Impossible d'implanter : la vue active n'est pas un plan associé à un niveau.",
                        title="Vue incorrecte", warn_icon=True)
            return

        ok, erreurs = self._validation()
        if not ok:
            forms.alert("\n".join(erreurs), title="Saisie incomplète", warn_icon=True)
            self.logger.warning("Création refusée : {}".format(" | ".join(erreurs)))
            return

        groupes_sel = [r["groupe"] for r in self.rows if r["chk"].IsChecked]

        suspects = self.groupes_suspects(groupes_sel)
        if suspects:
            pmin, pmax = self.plage_section()
            detail = "\n".join("• {} ({} bloc(s))".format(g["dims_label"], g["count"]) for g in suspects)
            self.logger.warning("Sections hors plage : {}".format(detail.replace("\n", " | ")))
            if not forms.alert(
                    "Des sections sont hors de la plage réaliste ({:g} à {:g} cm) :\n\n{}\n\n"
                    "L'unité choisie à l'import du DWG est probablement incorrecte.\n"
                    "Continuer quand même ?".format(pmin, pmax, detail),
                    title="Dimensions suspectes", yes=True, no=True):
                return

        options = self.get_options()
        self.Hide()
        try:
            success, msg = self.column_service.create_columns(groupes_sel, self.family_info, options)
        except Exception as err:
            success, msg = False, "Erreur inattendue : {}".format(err)

        if success:
            self.logger.info(msg.replace("\n", " "))
            forms.alert(msg, title="Succès")
            self.Close()
        else:
            self.logger.error(msg.replace("\n", " "))
            forms.alert(msg, title="Erreur")
            self.Show()
