## [1.2.0] - 2026-11-03

### Ajouté

  - Nouvelle fonctionnalité **Poteaux depuis DWG** (`PoteauxDepuisDwg.pushbutton`) dans le panneau *Conception structurelle* :
  - Détection automatique et extraction des blocs de poteaux fermés (polylignes) dans les DWG liés ou importés.
  - Regroupement des blocs par dimensions réelles en centimètres, en tenant compte de l'échelle de transformation des blocs CAO paramétriques.
  - Test à blanc transactionnel annulé (`RollBack`) validant la capacité de la famille Revit choisie à piloter dynamiquement ses cotes ($b$ et $h$).
  - Création automatique par duplication des types Revit manquants avec nommage normalisé (ex. : `30x40`), et réutilisation intelligente des types existants compatibles.
  - Implantation automatique au centre géométrique des formes avec correction automatique de l'orientation à 90° et prise en compte de la rotation du bloc.
  - Interface WPF responsive et moderne avec gestion de la sélection par dimension, alertes sur les sections hors plage réaliste et aperçu en temps réel.
  - Architecture modulaire et robuste (`script.py`, `ui_manager.py`, `ui.xaml`, `dwg_service.py`, `column_service.py`, `validator.py`, `app_config.py`, `logger.py`, `revit_utils.py`, `config.json`).
  - Documentation technique exhaustive de chaque module et fonction dans le `README.md` du bouton.

## [1.1.0] - 2026-10-28

### Ajouté

- Architecture modulaire pour `quadrillageauto` : `app_config.py`, `grid_service.py`, `ui_manager.py`, `validator.py`, `logger.py` et `config.json`.
- Prise en charge dynamique des options de configuration (titre, dimensions de l'interface, styles/couleurs, unités, auteur).
- Journalisation utilisateur (`logger.py`) compatible IronPython 2.7 et CPython 3.

### Modifié

- Passage de la version du plugin à `v1.1.0` dans l'ensemble des fichiers (`config.json`, `script.py`, `ui.xaml`).
- Déplacement de `apercu.png` dans le dossier du bouton `quadrillageauto.pushbutton`.

### Corrigé

- Résolution du conflit lié au nom réservé pyRevit `config.py` via `app_config.py`.
- Correction de la faute d'orthographe dans le titre (`"Réseaud"` → `"Réseau"`).
- Correction de l'encodage des fichiers pour une compatibilité native avec IronPython.

## [1.0.1] - 2026-10-25

### Ajouté

- Nouveau README : présentation, tableau des fonctionnalités, exemple d'utilisation,
  installation par archive ou par Git, structure du dépôt.
- Aperçu de l'interface (`apercu.png`) mis à jour.

### Modifié

- Nettoyage du dossier `releases` pour le rendre plus propre.
- Retrait des références au laboratoire de développement, qui reste local et n'est pas publié.

### Corrigé

- Fautes d'orthographe et accents manquants dans le README.
