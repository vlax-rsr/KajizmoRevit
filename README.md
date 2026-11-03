<div align="center">

# KAJIZMO REVIT

**Extension pyRevit pour Autodesk Revit — automatisation.**

[![Version](https://img.shields.io/github/v/release/vlax-rsr/KajizmoRevit-QuadrillageAuto?label=version&color=c0392b)](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/releases/latest)
[![Téléchargements](https://img.shields.io/github/downloads/vlax-rsr/KajizmoRevit-QuadrillageAuto/total?label=t%C3%A9l%C3%A9chargements)](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/releases)
[![Revit](https://img.shields.io/badge/Revit-2019%2B-186BFF)](#prérequis)
[![pyRevit](https://img.shields.io/badge/pyRevit-4.8%2B-2E7D32)](#prérequis)
[![Licence](https://img.shields.io/github/license/vlax-rsr/KajizmoRevit-QuadrillageAuto?label=licence)](LICENSE)

[![BIM](https://img.shields.io/badge/BIM-0078D4?style=flat)](#)
[![Revit](https://img.shields.io/badge/Revit-186BFF?style=flat)](#)
[![Architecture](https://img.shields.io/badge/Architecture-607D8B?style=flat)](#)
[![Structure](https://img.shields.io/badge/Structure-795548?style=flat)](#)
[![Automatisation](https://img.shields.io/badge/Automatisation-2E7D32?style=flat)](#)

[Installation](#installation) · [Fonctionnalités](#fonctionnalités) · [Automatisation quadrillage](#automatisation-quadrillage) · [Poteaux depuis DWG](#poteaux-depuis-dwg) · [Journal des modifications](CHANGELOG.md)

</div>

---

## Présentation

**Kajizmo Revit** est une extension [pyRevit](https://github.com/pyrevitlabs/pyRevit)
qui ajoute un onglet dédié dans le ruban d'Autodesk Revit.

**Tâche réalisée : automatisation de la conception structurelle.**

L'extension est **autonome** : elle ne dépend d'aucun script externe ni bibliothèque tierce pour fonctionner.

## Fonctionnalités

- **Automatisation quadrillage** - voir la section [Automatisation quadrillage](#automatisation-quadrillage).
- **Poteaux depuis DWG** - voir la section [Poteaux depuis DWG](#poteaux-depuis-dwg).

---

## Automatisation quadrillage

Génère un réseau de quadrillages (grilles) orthogonaux dans Revit à partir d'une
liste d'espacements saisie par l'utilisateur. Le traitement est exécuté directement
par l'API Revit : le résultat est rapide.

### Fonctionnalités

- **Saisie par espacements** : entrez les distances successives entre les files
  verticales (X) et horizontales (Y). Valeurs séparées par une virgule (`,`), un
  point-virgule (`;`) ou un espace.
- **Aperçu en temps réel** : l'emprise totale et le nombre de files se mettent à
  jour pendant la saisie (par ex. `Emprise : 16.00 m x 18.00 m (5 x 5 files)`) ;
  une saisie invalide affiche un message et désactive la création.
- **Notation au choix, par axe** : files numérotées (`1`, `2`, `3`, …) ou lettrées
  (`A`, `B`, `C`, …). Par défaut : axes verticaux numérotés, axes horizontaux
  lettrés.
- **Unités** : mètres (m), millimètres (mm) ou centimètres (cm).
- **Type de quadrillage** : reprend les types présents dans le modèle, avec
  **Bulle 6.5mm** proposé par défaut.
- **Couleur** : **Rouge**, **Noir** ou **Conserver la couleur actuelle**. La
  couleur des lignes est appliquée au type de quadrillage ainsi qu'aux extrémités
  (bulles) du quadrillage.
- **Débordement des extrémités** : marge réglable au-delà des extrémités, au
  clavier ou avec les boutons **+ / -** (pas de 0,1 m / 1 cm / 10 mm selon
  l'unité choisie).
- **Création intelligente** : quadrillage généré sur le niveau actif, étendu
  verticalement sur **tous les niveaux** et affiché en vue 3D.

### Aperçu de l'interface

<div align="center">

<img src="Kajizmo Revit.tab/Conception structurelle.panel/quadrillageauto.pushbutton/apercu.png" alt="Interface du plugin Quadrillage automatique" width="400">

</div>

### Utilisation

1. Ouvrez un projet Revit et placez-vous sur la vue du niveau souhaité. Une
   pastille dans la fenêtre indique le niveau détecté.
2. Dans le ruban, cliquez sur l'onglet **Kajizmo Revit** → panneau **Conception structurelle**
   → **Réseau de quadrillage**.
3. Renseignez les **distances entre files** pour les axes verticaux (X) et
   horizontaux (Y), puis réglez au besoin la notation, l'unité, le type de
   quadrillage, la couleur et le débordement (champ ou boutons + / -).
4. Vérifiez l'aperçu de l'emprise, puis validez avec **Entrée** ou le bouton
   **Créer les quadrillages**.
5. Cliquez sur un point de la zone de dessin de la vue qui sera l'origine du quadrillage.

### Exemple

| Axe | Espacements saisis | Positions des axes (m) |
| :-- | :-- | :-- |
| X (vertical) | `3, 5, 4, 4` | 0 → 3 → 8 → 12 → 16 |
| Y (horizontal) | `4, 5, 5, 4` | 0 → 4 → 9 → 14 → 18 |

Dans cet exemple, l'emprise totale affichée est de **16.00 m x 18.00 m**
(5 x 5 files).

---

## Poteaux depuis DWG

Implante automatiquement des poteaux structurels dans Revit à partir des blocs d'un fichier DWG lié ou importé. Le script détecte les dimensions réelles des blocs, vérifie l'aptitude de la famille choisie, crée automatiquement un type par dimension détectée et positionne les poteaux au centre géométrique avec correction d'orientation.

### Fonctionnalités

- **Détection automatique des blocs DWG** : analyse les polylignes des blocs dans les DWG de la vue active ou du projet et extrait les coordonnées, l'orientation et l'échelle réelle appliquée par Revit.
- **Regroupement par dimensions** : regroupe automatiquement les blocs ayant la même section (par exemple $30 \times 40\text{ cm}$ et $40 \times 30\text{ cm}$ forment un même groupe), avec gestion de tolérance et arrondi paramétrable.
- **Test à blanc de la famille** : vérifie en amont que la famille de poteau structurel sélectionnée est paramétrique et que ses cotes de largeur ($b$) et profondeur ($h$) pilotent réellement sa géométrie, au moyen d'une transaction sécurisée immédiatement annulée (`RollBack`).
- **Création automatique des types** : crée dynamiquement les types Revit manquants par duplication avec nommage automatique (ex. `30x40`) ou réutilise les types existants de section identique (à $1\text{ mm}$ près).
- **Positionnement et orientation intelligents** : implante les poteaux au centre géométrique exact de la forme, applique la rotation du bloc CAO et pivote automatiquement le poteau de $90^\circ$ si l'axe principal du bloc est perpendiculaire à celui de la famille.
- **Aperçu et validation en temps réel** : affiche le décompte total des poteaux, la liste détaillée des sections avec le type prévu, et bloque l'implantation si des incohérences sont détectées.
- **Contrôle des échelles et unités** : alerte l'utilisateur si les sections calculées sont hors de la plage réaliste (ex. $10$ à $200\text{ cm}$), signe direct d'une unité d'import DWG erronée.

### Aperçu de l'interface

<div align="center">

<img src="Kajizmo Revit.tab/Conception structurelle.panel/PoteauxDepuisDwg.pushbutton/apercu.png" alt="Interface du plugin Poteaux depuis DWG" width="400">

</div>

### Utilisation

1. Ouvrez un projet Revit et placez-vous sur une vue en plan associée au niveau souhaité. Le niveau et son altitude sont automatiquement détectés.
2. Dans le ruban, cliquez sur l'onglet **Kajizmo Revit** → panneau **Conception structurelle** → **Poteaux depuis DWG**.
3. Sélectionnez le **fichier DWG** lié dans le projet contenant les blocs de poteaux.
4. Choisissez la **famille de poteau structurel** à utiliser : le test automatique valide instantanément si la famille est compatible.
5. Dans la liste des **dimensions détectées**, cochez ou décochez les sections à implanter et vérifiez le nom du type prévu (existant ou à créer).
6. Vérifiez le résumé dans le cadre **Aperçu**, puis cliquez sur **Implanter les poteaux**.

### Exemple

| Dimension détectée | Nombre de blocs | Action effectuée | Type Revit affecté |
| :-- | :-- | :-- | :-- |
| $30 \times 40\text{ cm}$ | 12 | Création dynamique | `30x40` ($b = 30\text{ cm}$, $h = 40\text{ cm}$) |
| $40 \times 40\text{ cm}$ | 8 | Réutilisation | `40x40` (type existant dans la famille) |
| $25 \times 50\text{ cm}$ | 4 | Création dynamique | `25x50` ($b = 25\text{ cm}$, $h = 50\text{ cm}$) |

---

## Prérequis

| Élément | Version |
| :-- | :-- |
| Autodesk Revit | 2019 ou version ultérieure |
| pyRevit | 4.8 ou version ultérieure (dernière version recommandée) |

> Non testé sur l'ensemble des versions de Revit.
>
> pyRevit **7.0.0 ou ultérieur** est recommandé : les versions antérieures
> souffrent d'un ralentissement connu à l'exécution des commandes pyRevit.

## Installation

1. Téléchargez et installez la dernière version de
   [pyRevit](https://github.com/pyrevitlabs/pyRevit/releases).
2. Téléchargez la dernière archive disponible dans les [Releases](https://github.com/vlax-rsr/KajizmoRevit/releases).
3. Décompressez l'archive : vous obtenez le dossier `KajizmoRevit.extension`.
4. Copiez ce dossier dans le répertoire des extensions pyRevit :
   - `%APPDATA%\pyRevit\Extensions`
   - soit en clair : `C:\Users\<votre-nom>\AppData\Roaming\pyRevit\Extensions`
   *(Il est conseillé de supprimer la précédente version de KajizmoRevit avant de coller la nouvelle version).*
5. Dans Revit, ouvrez l'onglet **pyRevit** → **Reload** / **Recharger**.

> Le nom du dossier **doit** se terminer par `.extension`, sinon pyRevit ne le
> reconnaît pas.

### Rechargement

Après toute installation ou mise à jour, rechargez pyRevit :

- Onglet **pyRevit** → **Recharger**, ou
- en terminal : `pyrevit reload`

## Contribution et assistance

- Pour signaler un bug ou proposer une amélioration, ouvrez une
  [issue](https://github.com/vlax-rsr/KajizmoRevit-QuadrillageAuto/issues).

## Tags

#BIM #automatisation #Revit #Structure #Architecture

## Licence

Distribué sous licence **MIT**. Voir le fichier [LICENSE](LICENSE).
