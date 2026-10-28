## [1.1.0] - 2026-10-28

### Ajouté

- Architecture modulaire pour `quadrillageauto` : `app_config.py`, `grid_service.py`, `ui_manager.py`, `validator.py`, `logger.py` et `config.json`.
- Prise en charge dynamique des options de configuration (titre, dimensions UI, styles/couleurs, unités, auteur).
- Journalisation utilisateur (`logger.py`) compatible IronPython 2.7 et CPython 3.

### Modifié

- Passage de la version du plugin à `v1.1.0` dans l'ensemble des fichiers (`config.json`, `script.py`, `ui.xaml`).
- Déplacement de `apercu.png` au sein du dossier du bouton `quadrillageauto.pushbutton`.

### Corrigé

- Résolution du conflit lié au nom réservé pyRevit `config.py` via `app_config.py`.
- Correction de la faute d'orthographe dans le titre (`"Réseaud"` -> `"Réseau"`).
- Correction de l'encodage des fichiers pour une compatibilité native IronPython.

## [1.0.1] - 2026-10-25

### Ajouté

- Nouveau README : présentation, tableau des fonctionnalités, exemple d'utilisation,
  installation par archive ou par Git, structure du dépôt.
- Aperçu de l'interface (`apercu.png`) mis à jour.

### Modifié

- Nettoyage du releases pour un dossier `releases` plus propre.
- Références au laboratoire de développement, qui reste local et n'est pas publié.

### Corrigé

- Fautes d'orthographe et accents manquants dans le README.