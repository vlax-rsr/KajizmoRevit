<div align="center">

# Kajizmo Revit - Quadrillage automatique

**Extension pyRevit qui génère un réseau de quadrillages orthogonaux dans Autodesk Revit à partir d'une liste d'espacements.**

[![Version](https://img.shields.io/github/v/release/vlax-rsr/KajizmoRevit-QuadrillageAuto?label=version&color=c0392b)](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/releases/latest)
[![Téléchargements](https://img.shields.io/github/downloads/vlax-rsr/KajizmoRevit-QuadrillageAuto/total?label=t%C3%A9l%C3%A9chargements)](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/releases)
[![Revit](https://img.shields.io/badge/Revit-2019%2B-186BFF)](#pr%C3%A9requis)
[![pyRevit](https://img.shields.io/badge/pyRevit-4.8%2B-2E7D32)](#pr%C3%A9requis)
[![Licence](https://img.shields.io/github/license/vlax-rsr/KajizmoRevit-QuadrillageAuto?label=licence)](LICENSE)

[Télécharger](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/releases/latest) ·
[Fonctionnalités](#fonctionnalités) ·
[Installation](#installation) ·
[Utilisation](#utilisation) ·
[Journal des modifications](CHANGELOG.md)

</div>

---

## Présentation

**Kajizmo Revit** est une extension [pyRevit](https://github.com/pyrevitlabs/pyRevit)
qui ajoute un onglet dédié dans le ruban d'Autodesk Revit.

Elle crée un réseau de quadrillages (grilles) orthogonaux à partir d'une liste
d'espacements saisie par l'utilisateur : le traitement est
directement exécuté par l'API Revit. Le résultat est rapide.

L'extension est **autonome** : elle ne dépend d'aucun script externe pour fonctionner.

## Aperçu de l'interface

<div align="center">

<img src="apercu.png" alt="Interface de l'extension Kajizmo Revit" width="860">

</div>

## Fonctionnalités

- **Saisie par espacements** : entrez les distances successives entre les files
  verticales (X) et horizontales (Y). Valeurs séparées par une virgule (`,`), un
  point-virgule (`;`) ou un espace.
- **Aperçu en temps réel** : l'emprise totale et le nombre de files se mettent à jour
  pendant la saisie (par ex. `Emprise : 16.00 m × 18.00 m (5 × 5 files)`) ; une saisie
  invalide affiche un message et désactive la création.
- **Notation au choix, par axe** : files numérotées (`1`, `2`, `3`, …) ou lettrées
  (`A`, `B`, `C`, …). Par défaut : axes verticaux numérotés, axes horizontaux lettrés.
- **Unités** : mètres (m), millimètres (mm) ou centimètres (cm).
- **Type de quadrillage** : reprend les types présents dans le modèle, avec
  **Bulle 6.5mm** proposé par défaut.
- **Couleur** : **Rouge**, **Noir** ou
  **Conserver la couleur actuelle**. La couleur des lignes est appliquée au type de
  quadrillage ainsi qu'aux extrémités (bulles) du quadrillage.
- **Débordement des extrémités** : marge réglable au-delà des extrémités, au clavier ou
  avec les boutons **+ / −** (pas de 0,1 m / 1 cm / 10 mm selon l'unité choisie).
- **Création intelligente** : quadrillage généré sur le niveau actif, étendu
  verticalement sur **tous les niveaux** et affiché en vue 3D.

## Prérequis

| Élément | Version |
| :-- | :-- |
| Autodesk Revit | 2019 ou version ultérieure |
| pyRevit | 4.8 ou version ultérieure (dernière version recommandée) |

> Non testé sur l'ensemble des versions de Revit.
>
> pyRevit **7.0.0 ou ultérieur** est recommandé : les versions antérieures souffrent
> d'un ralentissement connu à l'exécution des commandes pyRevit.

## Installation

### Option 1 — Téléchargement de l'archive (recommandé)

1. Téléchargez et installez la dernière version de [pyRevit](https://github.com/pyrevitlabs/pyRevit/releases).
2. Téléchargez la dernière archive :
   [**KajizmoRevit-0.1.1.rar**](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/releases/latest/download/KajizmoRevit-0.1.1.rar)
   (ou consultez la page [Versions](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/releases/latest)).
3. Décompressez l'archive (WinRAR, 7-Zip ou équivalent) : vous obtenez le dossier
   `KajizmoRevit.extension`.
4. Copiez ce dossier dans le répertoire des extensions pyRevit :
   - `%APPDATA%\pyRevit\Extensions`
   - soit en clair : `C:\Users\<votre-nom>\AppData\Roaming\pyRevit\Extensions`
5. Dans Revit, ouvrez l'onglet **pyRevit** → **Reload** (ou menu **pyRevit** → **Reload**).

> Le nom du dossier **doit** se terminer par `.extension`, sinon pyRevit ne le
> reconnaît pas.

### Option 2 — Installation par Git

```powershell
cd "$env:APPDATA\pyRevit\Extensions"
git clone https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto.git KajizmoRevit.extension
```

Pour mettre à jour une installation existante :

```powershell
cd "$env:APPDATA\pyRevit\Extensions\KajizmoRevit.extension"
git pull
```

### Rechargement

Après toute installation ou mise à jour, rechargez pyRevit :

- Onglet **pyRevit** → **Reload**, ou
- en terminal : `pyrevit reload`

## Utilisation

1. Ouvrez un projet Revit et placez-vous sur la vue du niveau souhaité.
   Une pastille dans la fenêtre indique le niveau détecté.
2. Dans le ruban, cliquez sur l'onglet **Kajizmo Revit** → panneau **Quadrillage**
   → **Réseau de quadrillage**.
3. Renseignez les **distances entre files** pour les axes verticaux (X) et
   horizontaux (Y), puis réglez au besoin la notation, l'unité, le type de
   quadrillage, la couleur et le débordement (champ ou boutons + / −).
4. Vérifiez l'aperçu de l'emprise, puis validez avec **Entrée** ou le bouton
   **Créer les quadrillages**.

### Exemple

| Axe | Espacements saisis | Positions des axes (m) |
| :-- | :-- | :-- |
| X (vertical) | `3, 5, 4, 4` | 0 · 3 · 8 · 12 · 16 |
| Y (horizontal) | `4, 5, 5, 4` | 0 · 4 · 9 · 14 · 18 |

Dans cet exemple, l'emprise totale affichée est de **16.00 m × 18.00 m** (5 × 5 files).

## Structure du dépôt

```text
KajizmoRevit.extension/
├── .gitattributes
├── .gitignore
├── LICENSE
├── CHANGELOG.md
├── README.md
├── apercu.png
└── Kajizmo Revit.tab/
    └── Quadrillage.panel/
        └── CreerQuadrillage.pushbutton/
            ├── bundle.yaml
            ├── icon.png
            ├── icon.dark.png
            ├── ui.xaml
            └── script.py
```

## Contribution et assistance

- Pour signaler un bug ou proposer une amélioration, ouvrez une
  [issue](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/issues).

## Licence

Distribué sous licence **MIT**. Voir le fichier [LICENSE](LICENSE).
