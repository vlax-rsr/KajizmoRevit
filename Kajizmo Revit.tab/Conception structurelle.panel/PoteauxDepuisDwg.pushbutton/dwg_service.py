# -*- coding: utf-8 -*-
"""Détection du DWG et extraction des blocs (position, rotation, dimensions)."""
import math
from collections import OrderedDict

from Autodesk.Revit.DB import (
    FilteredElementCollector, ImportInstance, Options,
    GeometryInstance, PolyLine, XYZ, ElementId
)

from revit_utils import get_name, PIED_EN_CM


class DwgBlockService(object):
    def __init__(self, doc):
        self.doc = doc

    # ------------------------------------------------------------------
    # Étape 1 : DWG présents dans le projet
    # ------------------------------------------------------------------
    def list_dwgs(self, view):
        """OrderedDict libellé -> ImportInstance (vue active d'abord, sinon tout le projet)."""
        instances = list(FilteredElementCollector(self.doc, view.Id)
                         .OfClass(ImportInstance).ToElements())
        if not instances:
            instances = list(FilteredElementCollector(self.doc)
                             .OfClass(ImportInstance).ToElements())
        result = OrderedDict()
        for dwg in instances:
            type_elem = self.doc.GetElement(dwg.GetTypeId())
            nom = get_name(type_elem) or "DWG inconnu"
            if nom in result:
                nom = "{} (Id {})".format(nom, dwg.Id)
            result[nom] = dwg
        return result

    # ------------------------------------------------------------------
    # Étape 2 : extraction des blocs
    # ------------------------------------------------------------------
    def extract_blocks(self, dwg, view):
        """
        Liste de blocs : dict(nom, dims_label, dx, dy, origine_centre,
        origine_insertion, rotation, miroir).

        On lit GetSymbolGeometry() : GetInstanceGeometry() aplatit les blocs
        en polylignes/solides et ne les expose plus.
        """
        opt = Options()
        opt.View = view
        opt.ComputeReferences = False
        geometrie = dwg.get_Geometry(opt)
        blocs = []
        if geometrie:
            self._collecter(geometrie, self._identite(), blocs)
        return blocs

    @staticmethod
    def _identite():
        from Autodesk.Revit.DB import Transform
        return Transform.Identity

    def _collecter(self, elements, tf_parent, resultat):
        for obj in elements:
            if not isinstance(obj, GeometryInstance):
                continue

            tf = tf_parent.Multiply(obj.Transform)
            contenu = obj.GetSymbolGeometry()

            contient_sous_blocs = False
            if contenu is not None:
                for e in contenu:
                    if isinstance(e, GeometryInstance):
                        contient_sous_blocs = True
                        break

            if contient_sous_blocs:          # conteneur (le DWG entier)
                self._collecter(contenu, tf, resultat)
                continue

            # Échelle portée par la transformation du bloc : c'est là que Revit applique
            # l'unité choisie à l'import (facteur 1 pour un bloc statique, 0.01 pour un
            # bloc paramétrique dont la géométrie est stockée à l'échelle 100).
            try:
                echelle_x = tf.BasisX.GetLength()
                echelle_y = tf.BasisY.GetLength()
            except Exception:
                echelle_x = echelle_y = None

            mesure = self._mesurer(obj)
            dx = dy = None
            dims_label = None
            origine_centre = tf.Origin
            if mesure is not None:
                dx, dy, centre = mesure
                if echelle_x is not None and echelle_y is not None:
                    dx *= echelle_x
                    dy *= echelle_y
                petit, grand = sorted([dx, dy])
                dims_label = "{:.0f} x {:.0f} cm".format(petit, grand)
                origine_centre = tf.OfPoint(centre)

            miroir = False
            try:
                miroir = tf.BasisX.CrossProduct(tf.BasisY).Z < 0
            except Exception:
                pass

            resultat.append({
                "nom": self._nom_bloc(obj),
                "dims_label": dims_label,
                "dx": dx,
                "dy": dy,
                "origine_centre": origine_centre,
                "origine_insertion": tf.Origin,
                "rotation": math.atan2(tf.BasisX.Y, tf.BasisX.X),
                "miroir": miroir,
            })

    def _nom_bloc(self, gi):
        """Nom du bloc si Revit l'expose (None sinon)."""
        try:
            sid = gi.GetSymbolGeometryId().SymbolId
            if sid is not None and sid != ElementId.InvalidElementId:
                return get_name(self.doc.GetElement(sid))
        except Exception:
            pass
        return None

    @staticmethod
    def _mesurer(gi):
        """(largeur_cm, hauteur_cm, centre_local) de la forme du bloc, ou None."""
        xs, ys = [], []
        try:
            for o in gi.GetSymbolGeometry():
                if isinstance(o, PolyLine):
                    for pt in o.GetCoordinates():
                        xs.append(pt.X)
                        ys.append(pt.Y)
        except Exception:
            return None
        if not xs:
            return None
        dx = (max(xs) - min(xs)) * PIED_EN_CM
        dy = (max(ys) - min(ys)) * PIED_EN_CM
        centre = XYZ((max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0, 0.0)
        return (dx, dy, centre)

    # ------------------------------------------------------------------
    # Regroupement par DIMENSIONS seules (version « types automatiques »)
    # ------------------------------------------------------------------
    @staticmethod
    def group_by_dimensions(blocs, tol_cm=1.5, arrondi_cm=0.5):
        """
        Regroupe les blocs de mêmes dimensions, quel que soit leur nom.
        Les côtés sont triés : 30x40 et 40x30 forment un seul groupe.

        Retourne (groupes, sans_dimensions) :
          groupes         : liste triée de dict(petit, grand, dx, dy, nom, dims_label,
                            blocs, count) ; petit/grand sont arrondis à `arrondi_cm`
          sans_dimensions : blocs dont la forme n'a pas pu être mesurée
        """
        avec, sans = [], []
        for b in blocs:
            if b.get("dx") is None or b.get("dy") is None:
                sans.append(b)
            else:
                avec.append(b)

        def cote(b):
            return sorted([b["dx"], b["dy"]])

        avec.sort(key=lambda b: (cote(b)[0], cote(b)[1]))

        bruts = []      # [petit, grand, [blocs]]
        for b in avec:
            petit, grand = cote(b)
            cible = None
            for g in bruts:
                if abs(g[0] - petit) <= tol_cm and abs(g[1] - grand) <= tol_cm:
                    cible = g
                    break
            if cible is None:
                cible = [petit, grand, []]
                bruts.append(cible)
            cible[2].append(b)

        def arrondir(v):
            if not arrondi_cm:
                return v
            return round(v / arrondi_cm) * arrondi_cm

        groupes = []
        for petit, grand, liste in bruts:
            moy_p = sum(cote(b)[0] for b in liste) / len(liste)
            moy_g = sum(cote(b)[1] for b in liste) / len(liste)
            p, g = arrondir(moy_p), arrondir(moy_g)
            label = u"{:g} x {:g} cm".format(p, g)
            groupes.append({
                "petit": p, "grand": g,
                "dx": p, "dy": g,
                "nom": label,
                "dims_label": label,
                "blocs": liste,
                "count": len(liste),
            })
        groupes.sort(key=lambda g: (g["petit"], g["grand"]))
        return groupes, sans
