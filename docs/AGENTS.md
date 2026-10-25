# Projet : Plugin pyRevit « Murs depuis CAO »

## 1. Contexte & Architecture
Plugin pyRevit (IronPython 2.7 / CPython 3) qui reconstitue des murs Revit natifs depuis un DWG.
Architecture stricte en 4 couches :
- **C0 (Extraction)** : `cad_extract.py` (Lecture DWG, textes, hachures)
- **C1 (Analyse)** : `cad_core.py` (Directions, appairage, pièces preview)
- **C2 (Génération)** : `cad_generate.py` (Création Revit, pièces, types)
- **C3 (IHM)** : `script.py`, `ui.xaml`, `options.xaml` (Interface WPF, flux 2 boutons)
- **T0 (Tests)** : `test_parasites.dwg`, `compare_surfaces.py`

## 2. Structure de dossiers (STRICTE)
Chaque fichier doit être créé **exactement** à cet emplacement :

KajizmoRevit.extension/
│
├── Kajizmo Revit.tab/
│   └── Laboratoire.panel/
│       └── MursDepuisCAO.pushbutton/
│           ├── bundle.yaml          # Métadonnées pyRevit
│           ├── icon.png             # Icône du bouton
│           ├── script.py            # Contrôleur principal (C3)
│           ├── cad_extract.py       # Couche 0 (Extraction)
│           ├── cad_core.py          # Couche 1 (Analyse)
│           ├── cad_generate.py      # Couche 2 (Génération)
│           ├── cad_model.py         # Objets de données (Params, Results)
│           ├── ui.xaml              # Fenêtre principale
│           ├── options.xaml         # Fenêtre options avancées
│           ├── db.xaml              # Fenêtre base d'épaisseurs
│           └── summary.xaml         # Fenêtre bilan détaillé
│
├── lib/                             # Modules & helpers réutilisables
│   ├── __init__.py
│   ├── geometry_utils.py            # Conversions cm / m / feet & helpers
│   └── logging_utils.py             # Logger unique (rotation 5x2 Mo)
│
├── docs/                            # Spécifications (fichiers .md)
│   ├── Couche_0.md
│   ├── Couche_1.md
│   ├── Couche_2.md
│   ├── Couche_3.md
│   └── T1.md
│
├── tests/                           # Scripts de test (T1)
│   ├── compare_surfaces.py
│   └── run_tests.bat
│
├── .gitignore
└── README.md

## 3. Règles de Développement
- **Aucun seuil en dur** : Tout passe par des objets `*Params`.
- **Respect des couches** : C0 = géométrie pure (pas d'interprétation), C1 = analyse (pas d'API Revit), C2 = Revit (création), C3 = IHM (pas de calcul).
- **Unités** : Toujours en mètres dans C0-C1, conversion en pieds (`m_to_ft`) uniquement en C2.
- **Objets de transfert** : Chaque étape produit un objet `*_Result` avec un dictionnaire `stats`.

## 4. Documentation de Référence
Les algorithmes détaillés, les paramètres par défaut et les contrats d'interface sont dans `docs/*.md`. **Tu dois t'y référer impérativement** avant de coder.