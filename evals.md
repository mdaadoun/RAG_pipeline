# 🧪 Évaluation Manuelle et Tests - RAG Pipeline (`projects/6_RAG_pipeline`)

Ce document décrit les procédures complètes pour tester, évaluer et valider manuellement la pipeline d'ingestion et d'audit de qualité RAG une fois le développement terminé.

---

## 🎯 Vue d'ensemble des méthodes d'évaluation

Le projet dispose de **4 modes d'évaluation manuelle** principaux via l'interface CLI Typer (`src/ingestion/cli.py`) et la suite de tests Pytest :

| Mode | Commande | Objectif |
| :--- | :--- | :--- |
| **Quality Gates** | `ingest verify` | Valide la conformité du code, le linting, le typage strict et la release |
| **Benchmark** | `ingest benchmark` | Compare les stratégies `FixedSizeChunker` vs `RecursiveStructuralChunker` |
| **Exécution Ingestion** | `ingest run` | Ingeste un corpus, génère les chunks JSONL et le rapport `rapport_ingestion.json` |
| **Suite de Tests** | `pytest` | Exécute les 145 tests unitaires et d'intégration |

---

## 1. Vérification Globale des Quality Gates (`verify`)

Permet de contrôler si le projet satisfait l'ensemble des critères de qualité requis pour une mise en production (*Release Ready*).

### Commande :
```bash
# Avec Python de l'environnement virtuel local :
PYTHONPATH=src ./.venv/bin/python -m ingestion.cli verify

# Ou via Poetry :
poetry run ingest verify
```

### Contraintes & Portes de Qualité vérifiées :
* **Mypy Strict Check** : 100% de couverture en typage strict.
* **Ruff Lint Check** : Absence d'erreurs de style ou d'importation.
* **Pytest Test Suite** : 100% de succès sur la suite de tests.
* **Coverage Ratio** : Cible $\ge 98\%$ de préservation de caractères.
* **Vérification du Livrable** : Conformité du schéma JSON du rapport `rapport_ingestion.json`.

---

## 2. Benchmark Comparatif des Stratégies (`benchmark`)

Permet de mesurer l'impact qualitatif et la vitesse entre la découpe rigide à taille fixe et la découpe récursive structurelle.

### Commande :
```bash
# Benchmark par défaut sur les fixtures de test :
PYTHONPATH=src ./.venv/bin/python -m ingestion.cli benchmark --input ./tests/fixtures

# Benchmark avec paramètres personnalisés :
PYTHONPATH=src ./.venv/bin/python -m ingestion.cli benchmark --chunk-size 512 --overlap 64
```

### Métriques d'évaluation :
* **Temps d'exécution (ms)** : Latence du traitement.
* **Char Coverage Ratio** : Ratio de conservation des caractères ($\ge 0.98$).
* **Duplicate Char Ratio** : Taux de duplication aux bordures de chevauchement.
* **Orphan Blocks** : Détection des blocs de code ou tables Markdown découpés/orphelins.
* **Recommandation Stratégie** : Sélection automatique de la meilleure stratégie.

---

## 3. Exécution et Audit Manuel du Pipeline (`run`)

Permet d'exécuter le pipeline d'ingestion complet sur un dossier cible (`./tests/fixtures` ou `./data/input`).

### Commande :
```bash
PYTHONPATH=src ./.venv/bin/python -m ingestion.cli run \
  --input ./tests/fixtures \
  --output ./data/output \
  --strategy recursive \
  --chunk-size 512 \
  --overlap 64 \
  --min-chunk-size 50 \
  --report ./rapport_ingestion.json
```

### Résultat attendu en console :
* Affichage Rich Console décrivant le statut fichier par fichier.
* Tableau récapitulatif global (`Ingestion Audit Results`).
* Code de sortie `0` en cas de succès, `1` si des portes de qualité échouent (ex: blocs orphelins détectés).

---

## 4. Inspection Manuelle des Livrables

### A. Rapport d'Audit (`rapport_ingestion.json`)
Vérifier la présence et la valeur des clés dans le rapport JSON généré :
```json
{
  "global_metrics": {
    "coverage_ratio": 1.0,
    "orphan_block_count": 0,
    "documents_in_error": 0,
    "status": "PASSED"
  }
}
```

### B. Chunks JSONL (`data/output/*.jsonl`)
Inspecter visuellement les chunks générés dans `data/output/` pour valider :
1. La préservation de l'intégrité des tables Markdown (pas de séparation en-tête / lignes).
2. L'intégrité des blocs de code.
3. La présence des métadonnées de chunk (`document_id`, `chunk_index`, `token_count`).

---

## 5. Exécution de la Suite de Tests (`pytest`)

Exécuter la suite complète de 145 tests unitaires et d'intégration :

```bash
# Via l'interpréteur virtuel :
./.venv/bin/python -m pytest -v

# Via Makefile :
make test
```
