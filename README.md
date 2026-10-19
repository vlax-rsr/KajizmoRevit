# Kajizmo Revit — Extension pyRevit

Cette extension ajoute un onglet dédié **Kajizmo Revit** dans le ruban Autodesk Revit pour générer rapidement des quadrillages orthogonaux selon la logique de votre script Dynamo `Quadrillage_input_list.dyn`.

---

## 📁 Structure du dossier

```text
Quadrillage.extension/
└── Kajizmo Revit.tab/                   <-- Onglet « Kajizmo Revit » dans le ruban
    └── Quadrillage.panel/               <-- Panneau dans l'onglet
        └── CreerQuadrillage.pushbutton/ <-- Bouton d'action
            ├── bundle.yaml              <-- Métadonnées (titre, infobulle)
            ├── icon.png                 <-- Icône thème clair
            ├── icon.dark.png            <-- Icône thème sombre (Revit 2024+)
            ├── ui.xaml                  <-- Interface graphique moderne (WPF)
            ├── script.py                <-- Script d'exécution & API Revit
            └── Quadrillage_input_list.dyn <-- Copie autonome du script Dynamo
```

---

## 🚀 Fonctionnalités

1. **Saisie intuitive des distances** :
   - Entrez les espacements successifs entre files verticales (X) : ex. `3, 5, 4, 4` ou `3; 5; 4; 4`.
   - Entrez les espacements successifs entre files horizontales (Y) : ex. `4, 5, 5, 4`.
   - Accepte virgules, points-virgules, espaces et crochets `[ ]`.

2. **Aperçu en temps réel** :
   - Calcule automatiquement les positions cumulées des axes :
     - Pour `[3, 5, 4, 4]` : axes placés à **0, 3, 8, 12, 16 m**
     - Pour `[4, 5, 5, 4]` : axes placés à **0, 4, 9, 14, 18 m**
   - Affiche les dimensions totales de l'emprise (ex. **16.00 m × 18.00 m**).

3. **Options personnalisables** :
   - **Unités** : Mètres (m), Millimètres (mm), Centimètres (cm).
   - **Nommage séquentiel** :
     - Premier axe vertical (ex. `1` → `1, 2, 3, 4, 5`)
     - Premier axe horizontal (ex. `A` → `A, B, C, D, E`)
   - **Débordement des extrémités** : Marge au-delà de la dernière intersection (par défaut `1.0 m`, ou `0.0` comme dans Dynamo).
   - **Synchronisation Dynamo** : Met à jour directement les blocs de code `distList` dans le fichier `Quadrillage_input_list.dyn`.

4. **Bouton « Ouvrir le .dyn »** :
   - Permet d'ouvrir directement l'emplacement du script Dynamo dans l'Explorateur Windows.

---

## 🔄 Comment charger / recharger dans Revit

Puisque `c:\Users\riana\OneDrive\Documents\REVIT\Dynamo\extensions` est déjà configuré dans les chemins de recherche pyRevit :

1. Dans Revit, allez sur l'onglet **pyRevit** > menu **pyRevit** > cliquez sur **Reload**.
2. Ou via le terminal PowerShell :
   ```powershell
   pyrevit reload
   ```
3. Le nouvel onglet **Quadrillage** apparaîtra instantanément dans le ruban Revit avec le bouton **Créer Quadrillage** !
