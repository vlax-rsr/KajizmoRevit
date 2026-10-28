# -*- coding: utf-8 -*-
import os

import clr
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('System.Windows.Forms')

from System.Windows.Media import BrushConverter

from Autodesk.Revit.DB import (
    GridType, Level,
    FilteredElementCollector, BuiltInParameter
)
from pyrevit import forms, revit

from logger import UserLogger
from validator import DataValidator
from grid_service import RevitGridService
from app_config import ConfigManager


class QuadrillageWindow(forms.WPFWindow):
    def __init__(self, xaml_path=None):
        if xaml_path is None:
            xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self.doc = revit.doc
        self.uidoc = __revit__.ActiveUIDocument
        self.cfg = ConfigManager()
        self.logger = UserLogger()
        self.validator = DataValidator()
        self.grid_service = RevitGridService(self.doc, self.uidoc)

        try:
            cfg_title = self.cfg.get('title', "Réseau")
            cfg_subtitle = self.cfg.get('subtitle', "de quadrillage")
            cfg_ver = self.cfg.get('version', "1.1.0")
            full_title = "Kajizmo Revit - {} {} - v{}".format(cfg_title, cfg_subtitle, cfg_ver).replace("  ", " ")
            self.Title = full_title
        except Exception:
            pass

        try:
            win_w = self.cfg.get('ui.window_width')
            win_h = self.cfg.get('ui.window_height')
            if win_w:
                self.Width = float(win_w)
            if win_h:
                self.Height = float(win_h)
        except Exception:
            pass

        try:
            if hasattr(self, 'lbl_footer_info') and self.lbl_footer_info is not None:
                author = self.cfg.get('author', "Riana Stellia")
                self.lbl_footer_info.Text = "©2026 {}".format(author)
        except Exception:
            pass

        self.active_view = self.doc.ActiveView
        self.view_name = self.active_view.Name if self.active_view else "Vue active"
        self.current_level = getattr(self.active_view, "GenLevel", None) or getattr(self.active_view, "Level", None)
        badge = getattr(self, 'lbl_view_badge', None)
        if badge is not None:
            badge.Text = "Vue active : {}".format(self.view_name)

        self.brush_muted = BrushConverter().ConvertFromString("#5E6B78")
        self.brush_ink = BrushConverter().ConvertFromString("#1B2A3A")
        self.brush_blue = BrushConverter().ConvertFromString("#24508A")
        self.brush_red = BrushConverter().ConvertFromString("#C9372C")
        self.brush_line = BrushConverter().ConvertFromString("#D3D9DF")

        ph_x = self.cfg.get('placeholders.dist_x', "3, 4, 5, 5")
        ph_y = self.cfg.get('placeholders.dist_y', "3, 4, 5, 5")
        self.setup_placeholder(self.txt_dist_x, ph_x)
        self.setup_placeholder(self.txt_dist_y, ph_y)

        self.grid_types = list(FilteredElementCollector(self.doc).OfClass(GridType).WhereElementIsElementType())
        if hasattr(self, 'cb_grid_type'):
            self.cb_grid_type.Items.Clear()
            for gt in self.grid_types:
                try:
                    p_name = gt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
                    name = p_name.AsString() if p_name else "Quadrillage"
                except Exception:
                    name = "Quadrillage"
                self.cb_grid_type.Items.Add(name)
            if self.cb_grid_type.Items.Count > 0:
                self.cb_grid_type.SelectedIndex = 0

        if hasattr(self, 'cb_unit'):
            try:
                self.cb_unit.Items.Clear()
                units = self.cfg.get('units', [])
                for u in units:
                    try:
                        from System.Windows.Controls import ComboBoxItem
                        item = ComboBoxItem()
                        item.Content = u.get('label', '')
                        self.cb_unit.Items.Add(item)
                    except Exception:
                        pass
                def_unit = self.cfg.get('default_unit_index', 0)
                if self.cb_unit.Items.Count > 0 and 0 <= def_unit < self.cb_unit.Items.Count:
                    self.cb_unit.SelectedIndex = def_unit
            except Exception:
                pass

        if hasattr(self, 'cb_color'):
            try:
                color_opts = self.cfg.get('color_options', [])
                if color_opts:
                    from System.Windows.Controls import ComboBoxItem
                    self.cb_color.Items.Clear()
                    for c in color_opts:
                        item = ComboBoxItem()
                        item.Content = c.get('label', '')
                        self.cb_color.Items.Add(item)
                def_color = self.cfg.get('default_color_index', 1)
                if self.cb_color.Items.Count > 0 and 0 <= def_color < self.cb_color.Items.Count:
                    self.cb_color.SelectedIndex = def_color
            except Exception:
                pass

        if hasattr(self, 'txt_start_x'):
            try:
                self.txt_start_x.SelectedIndex = 0 if not self.cfg.get('notation.x_default_alpha', False) else 1
            except Exception:
                pass
        if hasattr(self, 'txt_start_y'):
            try:
                self.txt_start_y.SelectedIndex = 1 if self.cfg.get('notation.y_default_alpha', True) else 0
            except Exception:
                pass

        if hasattr(self, 'txt_offset'):
            try:
                self.txt_offset.Text = "{:.1f}".format(self.cfg.get('default_offset', 1.0))
            except Exception:
                pass

        if hasattr(self, 'txt_dist_x'):
            self.txt_dist_x.TextChanged += self.on_inputs_changed
        if hasattr(self, 'txt_dist_y'):
            self.txt_dist_y.TextChanged += self.on_inputs_changed
        if hasattr(self, 'cb_unit'):
            self.cb_unit.SelectionChanged += self.on_inputs_changed
        if hasattr(self, 'txt_offset'):
            self.txt_offset.TextChanged += self.on_inputs_changed

        if hasattr(self, 'btn_off_up'):
            self.btn_off_up.Click += self.on_offset_up
        if hasattr(self, 'btn_off_down'):
            self.btn_off_down.Click += self.on_offset_down

        if hasattr(self, 'btn_create'):
            self.btn_create.Click += self.on_create
        if hasattr(self, 'btn_cancel'):
            self.btn_cancel.Click += self.on_cancel

        self.update_preview()
        self.logger.info("Fenêtre QuadrillageWindow initialisée - Vue: {}".format(self.view_name))

    def setup_placeholder(self, textbox, placeholder_text):
        if textbox is None:
            return
        try:
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
                self.on_inputs_changed(sender, e)

            textbox.GotFocus += on_got_focus
            textbox.LostFocus += on_lost_focus
        except Exception:
            pass

    def get_clean_text(self, textbox):
        if textbox is None:
            return ""
        try:
            val = textbox.Text.strip() if textbox.Text else ""
            if val == "" or val == str(textbox.Tag):
                return ""
            return val
        except Exception:
            return ""

    def on_offset_up(self, sender, args):
        try:
            step = self.cfg.get('offset_step', 0.5)
            curr = float(self.txt_offset.Text.replace(",", "."))
        except Exception:
            curr = self.cfg.get('default_offset', 1.0)
            step = self.cfg.get('offset_step', 0.5)
        self.txt_offset.Text = "{:.1f}".format(curr + step)

    def on_offset_down(self, sender, args):
        try:
            step = self.cfg.get('offset_step', 0.5)
            curr = float(self.txt_offset.Text.replace(",", "."))
        except Exception:
            curr = self.cfg.get('default_offset', 1.0)
            step = self.cfg.get('offset_step', 0.5)
        new_val = max(0.0, curr - step)
        self.txt_offset.Text = "{:.1f}".format(new_val)

    def on_inputs_changed(self, sender, args):
        self.validate_and_update_borders()
        self.update_preview()

    def validate_and_update_borders(self):
        try:
            if hasattr(self, 'txt_dist_x') and self.txt_dist_x is not None:
                raw_x = self.get_clean_text(self.txt_dist_x)
                if raw_x:
                    if self.validator.is_positive_number_list(raw_x):
                        try:
                            self.txt_dist_x.BorderBrush = self.brush_blue
                        except Exception:
                            pass
                    else:
                        try:
                            self.txt_dist_x.BorderBrush = self.brush_red
                        except Exception:
                            pass
                else:
                    try:
                        self.txt_dist_x.BorderBrush = self.brush_line
                    except Exception:
                        pass
            if hasattr(self, 'txt_dist_y') and self.txt_dist_y is not None:
                raw_y = self.get_clean_text(self.txt_dist_y)
                if raw_y:
                    if self.validator.is_positive_number_list(raw_y):
                        try:
                            self.txt_dist_y.BorderBrush = self.brush_blue
                        except Exception:
                            pass
                    else:
                        try:
                            self.txt_dist_y.BorderBrush = self.brush_red
                        except Exception:
                            pass
                else:
                    try:
                        self.txt_dist_y.BorderBrush = self.brush_line
                    except Exception:
                        pass
        except Exception:
            pass

    def update_preview(self):
        try:
            raw_x = self.get_clean_text(self.txt_dist_x)
            raw_y = self.get_clean_text(self.txt_dist_y)
            if not hasattr(self, 'txt_preview_dims'):
                return
            if not raw_x or not raw_y:
                self.txt_preview_dims.Text = "Veuillez renseigner les listes d'entraxes X et Y."
                self.logger.info("Aperçu: entrées incomplètes")
                return
            try:
                d_x = self.validator.parse_distances(raw_x)
            except ValueError as ve:
                self.txt_preview_dims.Text = "Axe X - {}".format(ve)
                self.logger.warning("Aperçu invalide X: {}".format(ve))
                return
            try:
                d_y = self.validator.parse_distances(raw_y)
            except ValueError as ve:
                self.txt_preview_dims.Text = "Axe Y - {}".format(ve)
                self.logger.warning("Aperçu invalide Y: {}".format(ve))
                return
            def get_coords_cumulees(entraxes):
                coords = [0.0]
                for e in entraxes:
                    coords.append(coords[-1] + e)
                return coords
            rel_x = get_coords_cumulees(d_x)
            rel_y = get_coords_cumulees(d_y)
            units = self.cfg.get('units', [])
            try:
                unit_sym = units[self.cb_unit.SelectedIndex].get('symbol', 'm')
            except Exception:
                unit_symbols = ["m", "mm", "cm"]
                try:
                    unit_sym = unit_symbols[self.cb_unit.SelectedIndex]
                except Exception:
                    unit_sym = "m"
            if hasattr(self, 'lbl_offset'):
                self.lbl_offset.Text = "Débordement ({})".format(unit_sym)
            self.txt_preview_dims.Text = "Emprise : {:.2f} {} × {:.2f} {} ({} files X × {} files Y)".format(
                rel_x[-1], unit_sym, rel_y[-1], unit_sym, len(rel_x), len(rel_y)
            )
            self.logger.info("Aperçu mis à jour - X:{} Y:{}".format(len(d_x), len(d_y)))
        except Exception as ex:
            if hasattr(self, 'txt_preview_dims'):
                self.txt_preview_dims.Text = "Format de saisie incorrect : {}".format(ex)
            self.logger.error("Erreur update_preview: {}".format(ex))

    def on_cancel(self, sender, args):
        self.logger.info("Annulation par l'utilisateur")
        self.Close()

    def on_create(self, sender, args):
        doc = self.doc
        uidoc = self.uidoc
        raw_x = self.get_clean_text(self.txt_dist_x)
        raw_y = self.get_clean_text(self.txt_dist_y)
        if not raw_x:
            forms.alert("Vous n'avez pas entré la liste des entraxes pour les axes verticaux (X).", title="Champ manquant", warn_icon=True)
            self.logger.warning("Création refusée - X manquant")
            if hasattr(self, 'txt_dist_x'):
                self.txt_dist_x.Focus()
            return
        if not raw_y:
            forms.alert("Vous n'avez pas entré la liste des entraxes pour les axes horizontaux (Y).", title="Champ manquant", warn_icon=True)
            self.logger.warning("Création refusée - Y manquant")
            if hasattr(self, 'txt_dist_y'):
                self.txt_dist_y.Focus()
            return
        try:
            d_x = self.validator.parse_distances(raw_x)
        except ValueError as ve:
            forms.alert("Erreur dans la liste des entraxes X :\n\n{}".format(ve), title="Liste invalide", warn_icon=True)
            self.logger.error("Création refusée - X invalide: {}".format(ve))
            if hasattr(self, 'txt_dist_x'):
                self.txt_dist_x.Focus()
            return
        try:
            d_y = self.validator.parse_distances(raw_y)
        except ValueError as ve:
            forms.alert("Erreur dans la liste des entraxes Y :\n\n{}".format(ve), title="Liste invalide", warn_icon=True)
            self.logger.error("Création refusée - Y invalide: {}".format(ve))
            if hasattr(self, 'txt_dist_y'):
                self.txt_dist_y.Focus()
            return
        try:
            offset_val = float(self.txt_offset.Text.replace(",", "."))
            unit_idx = self.cb_unit.SelectedIndex if hasattr(self, 'cb_unit') else 0
        except Exception as e:
            forms.alert("Erreur dans les valeurs saisies : {}".format(e), title="Erreur")
            self.logger.error("Création refusée - paramètres invalides: {}".format(e))
            return
        self.Hide()
        try:
            message_texte = "Veuillez placer un point dans la vue '{}' qui servira d'origine à votre quadrillage.".format(self.view_name)
            forms.alert(message_texte, title="Placement du Point d'Origine", warn_icon=False)
            pt_origin = uidoc.Selection.PickPoint("Cliquez sur le point d'origine du quadrillage")
        except Exception:
            self.logger.warning("Placement annulé par l'utilisateur")
            self.Show()
            return

        try:
            notation_x_alpha = False
            notation_y_alpha = True
            if hasattr(self, 'txt_start_x') and self.txt_start_x.SelectedIndex == 1:
                notation_x_alpha = True
            if hasattr(self, 'txt_start_y') and self.txt_start_y.SelectedIndex == 0:
                notation_y_alpha = False
            color_choice = self.cb_color.SelectedIndex if hasattr(self, 'cb_color') else 1
            levels_list = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
            grid_types_list = getattr(self, 'grid_types', None)
            cb_gt_idx = self.cb_grid_type.SelectedIndex if hasattr(self, 'cb_grid_type') else 0

            success, msg = self.grid_service.create_grids(
                pt_origin=pt_origin,
                d_x=d_x,
                d_y=d_y,
                unit_idx=unit_idx,
                offset_val=offset_val,
                notation_x_alpha=notation_x_alpha,
                notation_y_alpha=notation_y_alpha,
                grid_types=grid_types_list,
                cb_grid_type_index=cb_gt_idx,
                color_choice=color_choice,
                levels_list=levels_list
            )
            if success:
                self.logger.info("Quadrillages créés avec succès - X:{} Y:{}".format(len(d_x), len(d_y)))
                forms.alert(msg, title="Succès")
                self.Close()
            else:
                self.logger.error(msg)
                forms.alert(msg, title="Erreur")
                self.Show()
        except Exception as err:
            self.logger.error("Erreur inattendue création quadrillages: {}".format(err))
            forms.alert("Erreur lors de la création : {}".format(err), title="Erreur")
            self.Show()

