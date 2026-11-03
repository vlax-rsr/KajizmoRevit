# -*- coding: utf-8 -*-
"""Familles de poteaux, création automatique des types par dimension,
et création des poteaux structurels."""
from __future__ import unicode_literals
import math
from collections import OrderedDict

from Autodesk.Revit.DB import (
    XYZ, Line, Transaction, FilteredElementCollector,
    BuiltInCategory, FamilySymbol, ElementTransformUtils, StorageType
)
from Autodesk.Revit.DB.Structure import StructuralType

from app_config import ConfigManager
from revit_utils import get_name, family_name, PIED_EN_CM

# Noms de paramètres reconnus automatiquement (comparaison insensible à la casse)
CANDIDATS_B = ["b", "Largeur", "Width", "Largeur du poteau"]
CANDIDATS_H = ["h", "Profondeur", "Depth", "Hauteur de section"]

NOM_TYPE_TEST = "__test_dimensions_tmp__"
TEST_B_CM = 23.0     # dimensions de test volontairement différentes entre elles
TEST_H_CM = 37.0


class FamilyError(Exception):
    """Famille inutilisable pour obtenir les dimensions voulues."""


class ColumnTypeService(object):
    def __init__(self, doc, level):
        self.doc = doc
        self.level = level
        self.cfg = ConfigManager()

    # ------------------------------------------------------------------
    # Familles de poteaux structurels chargées dans le projet
    # ------------------------------------------------------------------
    def list_families(self):
        """OrderedDict 'Famille' -> liste de FamilySymbol (triés par nom)."""
        symboles = (FilteredElementCollector(self.doc)
                    .OfClass(FamilySymbol)
                    .OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .ToElements())
        tmp = {}
        for s in symboles:
            nom = family_name(s) or "?"
            tmp.setdefault(nom, []).append(s)
        result = OrderedDict()
        for nom in sorted(tmp.keys()):
            result[nom] = sorted(tmp[nom], key=lambda s: (get_name(s) or ""))
        return result

    # ------------------------------------------------------------------
    # Outils sur les paramètres
    # ------------------------------------------------------------------
    @staticmethod
    def _params_double(symbole):
        """dict nom_minuscule -> (nom, Parameter) des paramètres numériques du type."""
        res = {}
        for p in symbole.Parameters:
            try:
                nom = p.Definition.Name
                if nom and p.StorageType == StorageType.Double:
                    res[nom.lower()] = (nom, p)
            except Exception:
                continue
        return res

    def _trouver_params(self, symbole):
        """
        Retourne (nom_b, nom_h, params_ro) : noms des paramètres largeur/profondeur.
        Lève FamilyError s'ils sont introuvables, identiques ou en lecture seule.
        """
        params = self._params_double(symbole)
        force_b = (self.cfg.get("types.param_b", "") or "").strip()
        force_h = (self.cfg.get("types.param_h", "") or "").strip()
        cand_b = [force_b] if force_b else CANDIDATS_B
        cand_h = [force_h] if force_h else CANDIDATS_H

        def chercher(candidats):
            for c in candidats:
                if c.lower() in params:
                    return params[c.lower()]
            return None

        pb, ph = chercher(cand_b), chercher(cand_h)
        if pb is None or ph is None:
            dispo = sorted(v[0] for v in params.values())
            manquants = []
            if pb is None:
                manquants.append("largeur (essayé : {})".format(", ".join(cand_b)))
            if ph is None:
                manquants.append("profondeur (essayé : {})".format(", ".join(cand_h)))
            raise FamilyError(
                "Paramètre(s) de dimension introuvable(s) dans le type « {} » : {}.\n"
                "Paramètres numériques du type : {}.\n"
                "Indiquez les bons noms dans config.json (types.param_b / types.param_h)."
                .format(get_name(symbole), " ; ".join(manquants),
                        ", ".join(dispo[:25]) or "aucun"))
        if pb[0].lower() == ph[0].lower():
            raise FamilyError("Les paramètres largeur et profondeur sont identiques ({}).".format(pb[0]))
        for nom, p in (pb, ph):
            if p.IsReadOnly:
                raise FamilyError(
                    "Le paramètre « {} » est en lecture seule (piloté par une formule "
                    "ou une propriété de la famille) : impossible d'y écrire une dimension.".format(nom))
        return pb[0], ph[0]

    @staticmethod
    def _lire_cm(symbole, nom):
        try:
            p = symbole.LookupParameter(nom)
            if p is not None and p.HasValue:
                return p.AsDouble() * PIED_EN_CM
        except Exception:
            pass
        return None

    @staticmethod
    def _ecrire_cm(symbole, nom, valeur_cm):
        p = symbole.LookupParameter(nom)
        if p is None:
            raise FamilyError("Paramètre « {} » absent du nouveau type.".format(nom))
        if p.IsReadOnly:
            raise FamilyError("Paramètre « {} » en lecture seule.".format(nom))
        if not p.Set(valeur_cm / PIED_EN_CM):
            raise FamilyError("Revit a refusé la valeur {} cm pour « {} ».".format(valeur_cm, nom))

    def _dupliquer(self, base, nom):
        nouveau = base.Duplicate(nom)
        return self.doc.GetElement(nouveau.Id)

    def _empreinte_cm(self, symbole):
        """Pose un poteau temporaire (rotation 0) et mesure son empreinte X/Y en cm.
        À appeler dans une transaction ouverte."""
        if not symbole.IsActive:
            symbole.Activate()
            self.doc.Regenerate()
        pos = XYZ(0, 0, self.level.Elevation)
        poteau = self.doc.Create.NewFamilyInstance(pos, symbole, self.level, StructuralType.Column)
        self.doc.Regenerate()
        bb = poteau.get_BoundingBox(None)
        if bb is None:
            raise FamilyError("Le poteau créé n'a pas de géométrie mesurable.")
        return ((bb.Max.X - bb.Min.X) * PIED_EN_CM,
                (bb.Max.Y - bb.Min.Y) * PIED_EN_CM)

    # ------------------------------------------------------------------
    # Étape 2 : vérification de la famille (test à blanc, annulé)
    # ------------------------------------------------------------------
    def check_family(self, symboles):
        """
        Vérifie qu'on peut obtenir des dimensions arbitraires en dupliquant un type.
        Retourne (ok, message, info). info = dict(symboles, base, nom_b, nom_h).
        Aucune modification n'est conservée dans le projet (transaction annulée).
        """
        if not symboles:
            return False, "La famille ne contient aucun type à dupliquer.", None

        base = symboles[0]
        try:
            if base.Family.IsInPlace:
                return False, ("Famille « en place » : elle ne peut pas être dupliquée "
                               "pour créer de nouveaux types."), None
        except Exception:
            pass

        try:
            nom_b, nom_h = self._trouver_params(base)
        except FamilyError as ex:
            return False, "{}".format(ex), None

        tol = float(self.cfg.get("tolerances.dimensions_cm", 1.5))
        mesure = None
        erreur = None
        t = Transaction(self.doc, "Test famille de poteau (annulé)")
        t.Start()
        try:
            test = self._dupliquer(base, NOM_TYPE_TEST)
            self._ecrire_cm(test, nom_b, TEST_B_CM)
            self._ecrire_cm(test, nom_h, TEST_H_CM)
            mesure = self._empreinte_cm(test)
        except Exception as ex:
            erreur = "{}".format(ex)
        try:
            t.RollBack()          # le test ne laisse aucune trace dans le projet
        except Exception:
            pass

        if erreur:
            return False, ("La famille « {} » n'accepte pas la duplication avec de nouvelles "
                           "dimensions :\n{}".format(family_name(base), erreur)), None

        attendu = sorted([TEST_B_CM, TEST_H_CM])
        obtenu = sorted(mesure)
        if max(abs(attendu[0] - obtenu[0]), abs(attendu[1] - obtenu[1])) > tol:
            return False, (
                "Les paramètres « {} » / « {} » ne pilotent pas la section du poteau "
                "de la famille « {} » : section demandée {:g} x {:g} cm, obtenue {:.1f} x {:.1f} cm."
                .format(nom_b, nom_h, family_name(base),
                        attendu[0], attendu[1], obtenu[0], obtenu[1])), None

        info = {"symboles": list(symboles), "base": base, "nom_b": nom_b, "nom_h": nom_h,
                "famille": family_name(base)}
        return True, "Famille valide (paramètres : {} / {}).".format(nom_b, nom_h), info

    # ------------------------------------------------------------------
    # Prévisualisation : quel type sera créé / réutilisé pour chaque groupe
    # ------------------------------------------------------------------
    def plan_types(self, groupes, info):
        """Ajoute à chaque groupe : 'nom_type' et 'existant' (FamilySymbol ou None)."""
        prefixe = self.cfg.get("types.prefixe", "") or ""
        noms_pris = set(get_name(s) for s in info["symboles"])
        for g in groupes:
            g["existant"] = self._chercher_existant(g, info, info["symboles"])
            if g["existant"] is not None:
                g["nom_type"] = get_name(g["existant"])
            else:
                nom = "{}{:g}x{:g}".format(prefixe, g["petit"], g["grand"])
                base_nom, n = nom, 2
                while nom in noms_pris:
                    nom = "{} ({})".format(base_nom, n)
                    n += 1
                noms_pris.add(nom)
                g["nom_type"] = nom
        return groupes

    def _chercher_existant(self, groupe, info, symboles):
        """Type de la famille dont la section correspond déjà (à 1 mm près)."""
        for s in symboles:
            vb = self._lire_cm(s, info["nom_b"])
            vh = self._lire_cm(s, info["nom_h"])
            if vb is None or vh is None:
                continue
            v = sorted([vb, vh])
            if abs(v[0] - groupe["petit"]) <= 0.1 and abs(v[1] - groupe["grand"]) <= 0.1:
                return s
        return None

    # ------------------------------------------------------------------
    # Étape 3 : création des types et des poteaux (une seule transaction)
    # ------------------------------------------------------------------
    def create_columns(self, groupes, info, options):
        """
        groupes : sortie de DwgBlockService.group_by_dimensions + plan_types
        info    : sortie de check_family
        options : dict(use_rotation, auto_orient, center_on_shape)
        Retourne (succès, message). Tout est annulé en cas d'erreur.
        """
        use_rotation = options.get("use_rotation", True)
        auto_orient = options.get("auto_orient", True)
        center = options.get("center_on_shape", True)
        tol_orient = float(self.cfg.get("tolerances.orientation_cm", 1.0))
        tol_dims = float(self.cfg.get("tolerances.dimensions_cm", 1.5))
        elevation = self.level.Elevation

        lignes = []
        total = 0
        miroirs = 0
        crees = 0
        reutilises = 0
        symboles = list(info["symboles"])

        t = Transaction(self.doc, self.cfg.get("revit.transaction_name",
                                               "Implanter des poteaux depuis DWG"))
        t.Start()
        try:
            for g in groupes:
                # --- le type : réutilisé ou créé par duplication -------------
                symbole = g.get("existant")
                if symbole is None:
                    symbole = self._chercher_existant(g, info, symboles)
                if symbole is not None:
                    statut = "type existant"
                    reutilises += 1
                else:
                    nouveau = self._dupliquer(info["base"], g["nom_type"])
                    self._ecrire_cm(nouveau, info["nom_b"], g["petit"])
                    self._ecrire_cm(nouveau, info["nom_h"], g["grand"])
                    symbole = nouveau
                    symboles.append(nouveau)
                    statut = "type créé"
                    crees += 1

                if not symbole.IsActive:
                    symbole.Activate()
                    self.doc.Regenerate()

                # --- les poteaux (même logique que la version « blocs ») -----
                empreinte = None
                corriges = 0
                alerte_dims = False
                compteur = 0

                for bloc in g["blocs"]:
                    o = bloc["origine_centre"] if center else bloc["origine_insertion"]
                    pos = XYZ(o.X, o.Y, elevation)
                    poteau = self.doc.Create.NewFamilyInstance(
                        pos, symbole, self.level, StructuralType.Column)

                    if empreinte is None and poteau is not None:
                        self.doc.Regenerate()
                        bb = poteau.get_BoundingBox(None)
                        if bb is not None:
                            empreinte = ((bb.Max.X - bb.Min.X) * PIED_EN_CM,
                                         (bb.Max.Y - bb.Min.Y) * PIED_EN_CM)

                    angle = bloc["rotation"] if use_rotation else 0.0
                    dx, dy = bloc["dx"], bloc["dy"]

                    if empreinte is not None and dx is not None:
                        fx, fy = empreinte
                        if auto_orient and abs(dx - dy) > tol_orient and abs(fx - fy) > tol_orient:
                            if (dx > dy) != (fx > fy):
                                angle += math.pi / 2.0
                                corriges += 1
                        bd = sorted([dx, dy])
                        fd = sorted([fx, fy])
                        if max(abs(bd[0] - fd[0]), abs(bd[1] - fd[1])) > tol_dims:
                            alerte_dims = True

                    if bloc.get("miroir"):
                        miroirs += 1

                    if poteau is not None and abs(angle) > 1e-5:
                        axe = Line.CreateBound(pos, XYZ(pos.X, pos.Y, pos.Z + 10.0))
                        ElementTransformUtils.RotateElement(self.doc, poteau.Id, axe, angle)

                    compteur += 1

                total += compteur
                ligne = "• {} -> {} ({}) : {} poteau(x)".format(
                    g["dims_label"], g["nom_type"], statut, compteur)
                if corriges:
                    ligne += "\n    orientation corrigée de 90° : {}".format(corriges)
                if alerte_dims:
                    ligne += "\n    ⚠ dimensions du type ≠ dimensions du bloc"
                lignes.append(ligne)

            t.Commit()
        except Exception as ex:
            try:
                t.RollBack()
            except Exception:
                pass
            return False, "Création annulée (aucun type ni poteau ajouté) :\n{}".format(ex)

        message = ("Implantation terminée !")
        if miroirs:
            message += ("\n\n⚠ {} bloc(s) en miroir dans le DWG : Revit ne peut pas "
                        "miroiter un poteau, vérifiez leur sens.").format(miroirs)
        return True, message
