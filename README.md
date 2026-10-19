<div align="center">

# Kajizmo Revit

**Extension pyRevit qui génère un réseau de quadrillages orthogonaux dans Autodesk Revit à partir d'une simple liste d'espacements.**

[![Version](https://img.shields.io/github/v/release/vlax-rsr/KajizmoRevit?label=version&color=c0392b)](https://github.com/vlax-rsr/KajizmoRevit/releases/latest)
[![Téléchargements](https://img.shields.io/github/downloads/vlax-rsr/KajizmoRevit/total?label=t%C3%A9l%C3%A9chargements)](https://github.com/vlax-rsr/KajizmoRevit/releases)
[![Revit](https://img.shields.io/badge/Revit-2019%2B-186BFF)](#pr%C3%A9requis)
[![pyRevit](https://img.shields.io/badge/pyRevit-4.8%2B-2E7D32)](#pr%C3%A9requis)
[![Licence](https://img.shields.io/github/license/vlax-rsr/KajizmoRevit?label=licence)](LICENSE)

[Télécharger](https://github.com/vlax-rsr/KajizmoRevit/releases/latest) ·
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
d'espacements saisie par l'utilisateur, sans passer par Dynamo : le traitement est
directement exécuté par l'API Revit, dans une seule transaction, et les avertissements
sont automatiquement acceptés. Le résultat est rapide, sans boîte de dialogue bloquante.

L'extension est **autonome** : elle ne dépend d'aucun script externe pour fonctionner.

## Fonctionnalités

- **Saisie par espacements** : entrez les distances successives entre les files
  verticales (X) et horizontales (Y) — séparateurs acceptés : `,` `;` espace et `[ ]`.
- **Aperçu en temps réel** : les positions cumulées des axes et l'emprise totale
  (par ex. `16,00 m × 18,00 m`) sont affichées pendant la saisie.
- **Départ personnalisable** : numérotation des files verticales (à partir de `1`, `2`, …)
  et lettrage des files horizontales (à partir de `A`, `B`, …).
- **Unités** : mètres (m), millimètres (mm) ou centimètres (cm).
- **Type de quadrillage** : reprend les types présents dans le modèle, avec
  **Bulle 6.5mm** proposé par défaut.
- **Couleur** : **Rouge** (texte et lignes rouges), **Noir** (valeur par défaut) ou
  **Conserver la couleur actuelle**. La couleur des lignes est appliquée au type de
  quadrillage ainsi qu'aux extrémités (bulles) du quadrillage.
- **Débordement des extrémités** : marge réglable au-delà de la dernière intersection.
- **Création intelligente** : quadrillage généré sur le niveau actif, étendu
  verticalement à tous les niveaux et visible en vue 3D.

## Prérequis

| Élément | Version |
| :-- | :-- |
| Autodesk Revit | 2019 ou version ultérieure |
| pyRevit | 4.8 ou version ultérieure (dernière version recommandée) |

> Non testé sur l'ensemble des versions de Revit.

## Installation

### Option 1 — Téléchargement de l'archive (recommandé)

1. Téléchargez la dernière archive :
   [**KajizmoRevit-0.1.0.rar**](https://github.com/vlax-rsr/KajizmoRevit/releases/latest/download/KajizmoRevit-0.1.0.rar)
   (ou consultez la page [Versions](https://github.com/vlax-rsr/KajizmoRevit/releases/latest)).
2. Décompressez l'archive (WinRAR, 7-Zip ou équivalent) : vous obtenez le dossier
   `KajizmoRevit.extension`.
3. Copiez ce dossier dans le répertoire des extensions pyRevit :
   - `%APPDATA%\pyRevit\Extensions`
   - soit en clair : `C:\Users\<votre-nom>\AppData\Roaming\pyRevit\Extensions`
4. Dans Revit, ouvrez l'onglet **pyRevit** → **Reload** (ou menu **pyRevit** → **Reload**).

> Le nom du dossier **doit** se terminer par `.extension`, sinon pyRevit ne le
> reconnaît pas.

### Option 2 — Installation par Git

```powershell
cd "$env:APPDATA\pyRevit\Extensions"
git clone https://github.com/vlax-rsr/KajizmoRevit.git KajizmoRevit.extension
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

1. Ouvrez un projet Revit et placez-vous sur la vue du niveau souhaité
   (le niveau de la vue active est utilisé). La barre de titre de la fenêtre
   affiche le niveau détecté.
2. Dans le ruban, cliquez sur l'onglet **Kajizmo Revit** → panneau **Quadrillage**
   → **Créer Quadrillage**.
3. Renseignez les **distances entre files** pour les axes verticaux (X) et
   horizontaux (Y), puis ajustez au besoin le départ, l'unité, le type de
   quadrillage, la couleur et le débordement.
4. Vérifiez l'aperçu de l'emprise, puis validez avec **Entrée** ou le bouton
   **Créer les Quadrillages**.

### Exemple

| Axe | Espacements saisis | Positions des axes (m) |
| :-- | :-- | :-- |
| X (vertical) | `3, 5, 4, 4` | 0 · 3 · 8 · 12 · 16 |
| Y (horizontal) | `4, 5, 5, 4` | 0 · 4 · 9 · 14 · 18 |

Dans cet exemple, l'emprise totale affichée est de **16,00 m × 18,00 m** (5 × 5 files).

## Structure du dépôt

```text
KajizmoRevit/                            <-- dépôt (à renommer en KajizmoRevit.extension)
├── LICENSE
├── CHANGELOG.md
├── README.md
└── Kajizmo Revit.tab/                   <-- onglet dans le ruban Revit
    └── Quadrillage.panel/               <-- panneau de l'onglet
        └── CreerQuadrillage.pushbutton/ <-- bouton
            ├── bundle.yaml              <-- métadonnées du bouton (titre, infobulle)
            ├── icon.png                 <-- icône (thème clair)
            ├── icon.dark.png            <-- icône (thème sombre)
            ├── ui.xaml                  <-- interface graphique (WPF)
            ├── script.py                <-- logique et API Revit
            └── Quadrillage_input_list.dyn <-- graphe Dynamo de référence
```

Le fichier `Quadrillage_input_list.dyn` est conservé à titre de référence
(équivalent Dynamo du générateur) : il n'est pas exécuté par l'extension.

## Versionnage

Ce projet suit le [versionnage sémantique](https://semver.org/lang/fr/) :

- **MAJOR** — modification incompatible ;
- **MINOR** — nouvelle fonctionnalité rétrocompatible ;
- **PATCH** — correction de bug.

Chaque version est publiée sous forme de **tag** `vX.Y.Z` et accompagnée d'une
archive `.rar` dans les [Versions](https://github.com/vlax-rsr/KajizmoRevit/releases)
ainsi que d'une entrée dans le [journal des modifications](CHANGELOG.md).

## Contribution et assistance

- Pour signaler un bug ou proposer une amélioration, ouvrez une
  [issue](https://github.com/vlax-rsr/KajizmoRevit/issues).

## Licence

Distribué sous licence **MIT**. Voir le fichier [LICENSE](LICENSE).
