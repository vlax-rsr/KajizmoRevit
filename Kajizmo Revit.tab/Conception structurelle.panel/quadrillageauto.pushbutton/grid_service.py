# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import (
    XYZ, Line, Grid, Level,
    Transaction, FilteredElementCollector, BuiltInParameter,
    Color, BuiltInCategory, Category, ElementId
)
from pyrevit import forms
from app_config import ConfigManager


class RevitGridService(object):
    def __init__(self, doc, uidoc=None):
        self.doc = doc
        self.uidoc = uidoc
        self.cfg = ConfigManager()

    def _get_color_rgb(self, color_choice):
        try:
            color_opts = self.cfg.get('color_options', [])
            if color_opts and 0 <= color_choice < len(color_opts):
                rgb_val = color_opts[color_choice].get('rgb')
                if rgb_val is not None and len(rgb_val) == 3:
                    return tuple(rgb_val)
                return None
        except Exception:
            pass
        fallback = {0: (255, 0, 0), 1: (0, 0, 0), 2: None}
        return fallback.get(color_choice)

    def to_feet(self, value, unit_idx):
        try:
            units = self.cfg.get('units', [])
            if units and 0 <= unit_idx < len(units):
                factor = units[unit_idx].get('factor_to_feet', 3.28084)
                return float(value) * factor
            if unit_idx == 1:   # mm
                return (float(value) / 1000.0) * 3.28084
            elif unit_idx == 2:  # cm
                return (float(value) / 100.0) * 3.28084
            return float(value) * 3.28084  # m
        except Exception:
            raise

    def get_coords_cumulees(self, entraxes):
        coords = [0.0]
        for e in entraxes:
            coords.append(coords[-1] + float(e))
        return coords

    def get_name_sequence(self, is_alpha, count):
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

    def _color_param_value(self, rgb):
        return rgb[0] + (rgb[1] << 8) + (rgb[2] << 16)

    def find_grid_heads_category(self):
        target_id = ElementId(BuiltInCategory.OST_GridHeads)
        try:
            cat = Category.GetCategory(self.doc, target_id)
            if cat:
                return cat
        except Exception:
            pass
        try:
            parent = self.doc.Settings.Categories.get_Item(BuiltInCategory.OST_Grids)
        except Exception:
            parent = None
        if parent is not None:
            try:
                for sub in parent.SubCategories:
                    if sub.Id == target_id:
                        return sub
            except Exception:
                pass
        return None

    def create_grids(self, pt_origin, d_x, d_y, 
                     unit_idx, offset_val,
                     notation_x_alpha=False, notation_y_alpha=True,
                     grid_types=None, cb_grid_type_index=0,
                     color_choice=1, levels_list=None):
        try:
            if pt_origin is None:
                raise ValueError("Point d'origine non défini.")
            if not d_x or not d_y:
                raise ValueError("Listes d'entraxes vides ou invalides.")

            rel_x = self.get_coords_cumulees(d_x)
            rel_y = self.get_coords_cumulees(d_y)

            coords_x = [self.to_feet(x, unit_idx) for x in rel_x]
            coords_y = [self.to_feet(y, unit_idx) for y in rel_y]
            offset_ft = self.to_feet(offset_val, unit_idx)

            xmin, xmax = coords_x[0], coords_x[-1]
            ymin, ymax = coords_y[0], coords_y[-1]

            if levels_list is None:
                levels_list = list(FilteredElementCollector(self.doc).OfClass(Level).ToElements())
            elevations = []
            for l in levels_list:
                try:
                    elevations.append(l.Elevation)
                except Exception:
                    pass
            if not elevations:
                elevations = [0.0]
            ext = self.cfg.get('revit.level_extension_feet', 3.28084)
            min_z = min(elevations) - ext
            max_z = max(elevations) + ext

            names_x = self.get_name_sequence(notation_x_alpha, len(coords_x))
            names_y = self.get_name_sequence(notation_y_alpha, len(coords_y))

            selected_type = None
            if grid_types and cb_grid_type_index >= 0 and cb_grid_type_index < len(grid_types):
                selected_type = grid_types[cb_grid_type_index]

            trans_name = self.cfg.get('revit.transaction_name', "Créer Quadrillage par Origine")
            t = Transaction(self.doc, trans_name)
            t.Start()
            try:
                rgb = self._get_color_rgb(color_choice)
                if rgb is not None:
                    if selected_type is not None:
                        try:
                            p_col = selected_type.get_Parameter(BuiltInParameter.LINE_COLOR)
                            if p_col is not None and not p_col.IsReadOnly:
                                p_col.Set(self._color_param_value(rgb))
                        except Exception:
                            pass
                    heads_category = self.find_grid_heads_category()
                    if heads_category is not None:
                        try:
                            heads_category.LineColor = Color(rgb[0], rgb[1], rgb[2])
                        except Exception:
                            pass

                created_count = 0
                for i, x in enumerate(coords_x):
                    p_start = XYZ(pt_origin.X + x, pt_origin.Y + ymin - offset_ft, pt_origin.Z)
                    p_end = XYZ(pt_origin.X + x, pt_origin.Y + ymax + offset_ft, pt_origin.Z)
                    grid = Grid.Create(self.doc, Line.CreateBound(p_start, p_end))
                    if selected_type is not None:
                        try:
                            grid.ChangeTypeId(selected_type.Id)
                        except Exception:
                            pass
                    if levels_list:
                        try:
                            grid.SetVerticalExtents(min_z, max_z)
                        except Exception:
                            pass
                    try:
                        grid.Name = names_x[i]
                    except Exception:
                        pass
                    created_count += 1

                for i, y in enumerate(coords_y):
                    p_start = XYZ(pt_origin.X + xmin - offset_ft, pt_origin.Y + y, pt_origin.Z)
                    p_end = XYZ(pt_origin.X + xmax + offset_ft, pt_origin.Y + y, pt_origin.Z)
                    grid = Grid.Create(self.doc, Line.CreateBound(p_start, p_end))
                    if selected_type is not None:
                        try:
                            grid.ChangeTypeId(selected_type.Id)
                        except Exception:
                            pass
                    if levels_list:
                        try:
                            grid.SetVerticalExtents(min_z, max_z)
                        except Exception:
                            pass
                    try:
                        grid.Name = names_y[i]
                    except Exception:
                        pass
                    created_count += 1

                t.Commit()
                return True, "Quadrillages créés avec succès! ({} axes)".format(created_count)
            except Exception as err:
                try:
                    t.RollBack()
                except Exception:
                    pass
                raise err
        except Exception as err:
            return False, "Erreur lors de la création : {}".format(err)
