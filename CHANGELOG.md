# Journal des modifications

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format s'appuie sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le projet respecte le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié] — 0.2.3

### Corrigé

- **Nom du type de mur affiché sous forme d'ID** (ex. `29329`) dans la liste
  « Type de référence » : `.Name` peut échouer ou renvoyer une chaîne vide sous
  IronPython, et l'ancien repli affichait l'`ElementId`. Nouvel utilitaire
  `naming_utils.get_element_name()` en cascade : pyRevit `query.get_name` →
  paramètres de type (`SYMBOL_NAME_PARAM`, `ALL_MODEL_TYPE_NAME`) → `.Name` →
  `Element.Name.GetValue` → ID (journalisé en `WARNING`).
- Utilisé par les **trois** appelants (`script.py`, `cad_generate.py`,
  `cad_extract.py`) : le défaut cassait aussi la **réutilisation des types** en
  Couche 2 (comparaison par nom), qui dupliquait donc les types à chaque
  exécution.
- Diagnostic : le journal liste désormais les types de murs basiques détectés
  au démarrage (`Types de murs basiques : N (...)`).

## [Non publié] — 0.2.2

### Corrigé (audit des écarts spec ↔ code)

- **`filter_hatches` désactivé par défaut** dans `CadAnalysisParams`, en accord
  avec la case décochée de l'IHM : plus de rejet implicite de murs non pochés.
- **`UiParameters` est désormais réellement utilisé** : il est assemblé par
  `_build_ui_parameters()` et consommé par le recalcul (Couche 1) comme par la
  génération (Couche 2), au lieu d'être une classe morte.
- **`UiContext` ajouté** : la fenêtre reçoit `(doc, active_view, extraction,
  config)` via ce conteneur, conformément au contrat de la Couche 3.
- **Hachures** : récupération de `PatternName` lorsqu'un objet l'expose
  (duck typing) ; limitation documentée dans `cad_extract.py` (le motif n'est
  pas accessible pour les hachures CAO, donc pas de mapping matériau en v1).
- **`FUNCTION_PARAM`** : repli sur l'instance si une version l'y expose en
  écriture ; la documentation précise qu'il est normalement porté par le type.
- Documentation des **écarts assumés** de la Couche 1 dans l'en-tête de
  `cad_core.py` : découpage aux intersections, parcours de faces, classification
  géométrique (et absence de `shared_count`), ouvertures limitées aux murs droits.

## [Non publié] — 0.2.1

### Corrigé

- **Import impossible sous Revit 2026** (`ImportError: Cannot import name Circle`) :
  l'API Revit n'expose pas de classe `Circle`. Un cercle est un `Arc` non borné
  (sans extrémités) ; il est désormais reconnu dans la branche `Arc` et converti
  en arc 360°. Les cercles complets restent exclus de l'appairage (un mur
  circulaire fermé n'existe pas dans Revit).
- Test de non-régression : `tests/test_couches_0_2_mock.py` simule une API sans
  `Circle` et vérifie qu'un arc 360° est bien extrait.

## [Non publié] — 0.2.0

### Ajouté

- Bouton **Murs depuis CAO** réécrit en **quatre couches** : extraction CAO (0),
  analyse (1), génération Revit (2), interface (3). Chaque couche a un contrat
  d'entrée/sortie explicite et la Couche 1 reste testable hors Revit.
- **Extraction typée** : lignes, arcs, cercles, polylignes (fermeture détectée),
  profils, blocs imbriqués (transformations cumulées) et hachures reconstruites
  depuis les boucles fermées. Compteurs par calque (entités CAO / segments).
- **Murs courbes** : appairage d'arcs concentriques, création via `Arc.Create`.
- **Pièces** : détection par parcours de faces du graphe planaire, y compris
  lorsque les murs se croisent (découpage aux intersections).
- **Classification** extérieur / intérieur testée de part et d'autre du mur.
- **Ouvertures** : calques portes/fenêtres, baies chaînées, lignes parallèles ;
  largeurs et positions reportées dans le bilan.
- **Filtrage par hachures** (murs pochés), désactivable dans l'IHM.
- **Types de murs automatiques** : `MUR_EXT_20cm`, `MUR_INT_15cm`, `MUR_20cm`,
  mur à couche unique, `FUNCTION_PARAM` appliqué au type.
- **Mode de hauteur** : niveau supérieur contraint (`WALL_HEIGHT_TYPE`) ou
  hauteur libre, avec validation hors transaction.
- **Sélecteur de calques** avec compteurs, boutons Tout / Aucun, et persistance
  complète des réglages (calques, seuils, hauteur, type de référence).
- **Bilan** : résumé compact dans la fenêtre + fenêtre `summary.xaml` détaillée
  (extraction, analyse, classification, ouvertures, génération, erreurs).
- **Journal fichier** avec rotation (5 × 2 Mo) dans `%APPDATA%\Kajizmo\logs`.

### Modifié

- `cad_core.py` ne contient plus l'extraction : elle est isolée dans
  `cad_extract.py`, et la génération dans `cad_generate.py`.
- La base d'épaisseurs est désormais consommée par la Couche 1 (tolérance ±1 cm).
- Les hachures et les calques portes/fenêtres sont conservés par le filtre de
  calques, sinon le filtrage et la détection d'ouvertures seraient inopérants.

### Corrigé

- Murs de périmètre classés « intérieur » lorsqu'un mur continu borde plusieurs
  pièces (règle `shared_count` remplacée par un test géométrique).
- Pièces non détectées lorsque les murs se croisent (aucun sommet commun).
- Cycles non minimaux comptés comme pièces (parcours de faces au lieu du DFS).
- Baies exprimées dans le mauvais repère, donc décalées le long du mur.
- Traits de porte/fenêtre interprétés comme des faces de murs (parois parasites).
- Types de murs créés à la mauvaise épaisseur en cas d'échec silencieux : le
  défaut est désormais journalisé et compté.
- Sens des arcs importés (contrôle de cohérence avec la longueur réelle).
- Orientation à 180° de la moyenne circulaire (axes inversés, baies négatives).

## [0.1.1] - 2026-10-19

### Modifié

- **Notation des files** : la numérotation commence désormais à `1` (`1`, `2`, `3`, …) ;
  les positions des axes partent toujours de `0` sur le plan.
- **Boutons + / −** du champ **Débordement** désormais fonctionnels (pas adapté à l'unité :
  0,1 m / 1 cm / 10 mm).
- Libellé du champ **Débordement** synchronisé avec l'unité sélectionnée.
- Bouton renommé : **Créer Quadrillage** → **Réseau de quadrillage**.

### Supprimé

- Import inutilisé (`sys`) dans `script.py`.
- Graphe Dynamo de référence `Quadrillage_input_list.dyn` (jamais exécuté par l'extension)
  et la règle `*.dyn` devenue inutile dans `.gitattributes`.

### Corrigé

- Incohérence entre le libellé « 1, 2, 3… » de l'interface et la numérotation réelle.

## [0.1.0] - 2026-10-19

### Ajouté

- Onglet **Kajizmo Revit** dans le ruban Revit (extension pyRevit).
- Panneau **Quadrillage** avec le bouton **Créer Quadrillage**.
- Interface WPF : saisie des distances entre files (axes X et Y), point de départ,
  unité (m / mm / cm), type de quadrillage, couleur et débordement des extrémités.
- Aperçu en temps réel de l'emprise générée.
- Génération d'un réseau de quadrillages orthogonaux sur le niveau actif, avec
  étendue verticale sur tous les niveaux et visibilité en vue 3D.
- Couleurs proposées : **Rouge** (texte et lignes rouges), **Noir** (par défaut) et
  **Conserver la couleur actuelle**, avec synchronisation des extrémités de
  quadrillage (`OST_GridHeads`).
- Type de quadrillage proposé par défaut : **Bulle 6.5mm**.
- Script autonome (aucune dépendance à Dynamo), transaction unique et suppression
  automatique des avertissements Revit pour une exécution rapide et sans dialogue.
- Graphe Dynamo de référence `Quadrillage_input_list.dyn` fourni à titre indicatif.
