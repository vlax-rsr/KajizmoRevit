# Journal des modifications

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format s'appuie sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le projet respecte le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

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
