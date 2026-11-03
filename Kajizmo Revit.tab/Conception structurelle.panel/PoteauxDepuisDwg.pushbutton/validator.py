# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class DataValidator(object):
    def __init__(self):
        pass

    def check_selection(self, lignes, famille_nom, famille_valide, famille_msg=None):
        """
        lignes         : liste de dict(use, dims) – une par dimension détectée.
        famille_nom    : famille choisie (None si aucune).
        famille_valide : True si la vérification de la famille a réussi.
        famille_msg    : message d'erreur de la vérification (si refusée).
        Retourne (ok, [messages d'erreur]).
        """
        erreurs = []
        if not lignes:
            erreurs.append("Aucune dimension détectée : choisissez un DWG contenant des blocs de poteaux.")
            return False, erreurs
        if not famille_nom:
            erreurs.append("Choisissez une famille de poteau.")
        elif not famille_valide:
            detail = " ({})".format(famille_msg.split("\n")[0]) if famille_msg else ""
            erreurs.append("La famille « {} » ne permet pas de créer les dimensions voulues{}."
                           .format(famille_nom, detail))
        if not any(l.get("use") for l in lignes):
            erreurs.append("Cochez au moins une dimension à implanter.")
        return (len(erreurs) == 0), erreurs
