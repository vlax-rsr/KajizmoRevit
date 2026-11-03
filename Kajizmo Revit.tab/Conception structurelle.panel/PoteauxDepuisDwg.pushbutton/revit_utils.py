# -*- coding: utf-8 -*-
"""Petits utilitaires Revit robustes sous IronPython."""
from Autodesk.Revit.DB import BuiltInParameter, Element

PIED_EN_CM = 30.48
PIED_EN_M = 0.3048


def get_name(elem):
    """Nom d'un élément/type. Element.Name peut lever AttributeError en IronPython."""
    if elem is None:
        return None
    for bip in (BuiltInParameter.SYMBOL_NAME_PARAM,
                BuiltInParameter.ALL_MODEL_TYPE_NAME,
                BuiltInParameter.VIEW_NAME):
        try:
            prm = elem.get_Parameter(bip)
            if prm is not None and prm.HasValue:
                v = prm.AsString()
                if v:
                    return v
        except Exception:
            pass
    try:
        return Element.Name.GetValue(elem)
    except Exception:
        pass
    try:
        return elem.Name
    except Exception:
        return None


def family_name(symbol):
    """Nom de la famille d'un FamilySymbol."""
    try:
        return symbol.FamilyName
    except Exception:
        pass
    try:
        return get_name(symbol.Family)
    except Exception:
        return None
