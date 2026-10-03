# SmartBL Pharma - Synthetic BL Dataset Generator

Generateur de donnees synthetiques pour bons de livraison pharmaceutiques marocains (francais), destine a l'entrainement OCR / Document AI (LayoutLM, extraction tabulaire, KIE).

## Fonctionnalites

- Generation de 1000+ bons de livraison realistes
- Multiples fournisseurs (PHARMANORD, BUMAGECO, KENIPHARMA, REPHAL, SARP, PH KASBAH)
- Chargement automatique des fournisseurs depuis `data/suppliers.csv` (ou fallback Desktop)
- Generation automatique d'un template dedie par fournisseur dans `templates/suppliers/`
- Profils fournisseur distincts (entetes, colonnes, totaux, pied de page) selon chaque repartiteur
- 4 layouts differents:
  - clean
  - dense
  - receipt-like
  - colored columns
- Tableau produits avec variation:
  - 1 a 15 lignes
  - lignes fusionnees
  - valeurs manquantes
  - texte legerement desaligne
- Colonnes optionnelles: PPH, TVA, code produit
- Colonnes avancees selon profil fournisseur: lot, peremption, remise
- Totalisation HT, TVA, TTC
- Prix produits lies a des fourchettes par medicament (si base medicaments contient les prix)
- Augmentations image:
  - rotation legere
  - flou gaussien
  - variation de luminosite
  - bruit manuscrit simule
  - cachet et signature simules
- Annotation JSON par image

## Architecture

- `config.py`: configuration globale
- `data_generator.py`: generation de structure BL + anomalies
- `data/suppliers.csv`: base fournisseurs reelle
- `data/medicines.csv` ou `data/medicaments.csv` (optionnel): base medicaments externe
- `templates/*.html`: layouts HTML/Jinja2
- `renderer.py`: rendu HTML -> image + augmentations
- `main.py`: point d'entree

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Utilisation

Generer 1000 documents:

```bash
python main.py -n 1000
```

Generer 100 documents pour test:

```bash
python main.py -n 100
```

## Dataset v2 - Generation realiste calibree

Le mode `dataset_v2` produit une structure separee sans ecraser `dataset_v1`.

Commande de generation:

```bash
python main.py --dataset-version v2 --num-docs 5000 --output-dir dataset_v2 --no-augmentation
```

Structure de sortie:

```text
dataset_v2/
  images/train|
  images/val|
  images/test|
  annotations/train|
  annotations/val|
  annotations/test|
  _html/
  reports/
  previews/
  metadata/
```

Regles principales:

- 3 a 6 lignes: small BL
- 7 a 12 lignes: medium BL
- 13 a 20 lignes: large BL
- 21 a 30 lignes: hard cases
- quantites majoritairement entieres
- lots et dates de peremption partiellement presentes et varies
- prix limites a des bandes realistes par type de produit
- annotations ciblees Wellys: `bl_number`, `bl_date`, `supplier_name`, `items[]`

Limites connues:

- `total_global` et `line_total` ne sont pas des cibles OCR dans le JSON final
- les previews et rapports sont generes automatiquement apres production v2
- les templates sont fournis par `templates/suppliers/`

## Bases de donnees metier

- Fournisseurs: placez votre fichier dans `data/suppliers.csv`.
- Medicaments: placez votre fichier dans `data/medicines.csv` ou `data/medicaments.csv`.
- Colonnes medicaments supportees automatiquement: `designation`, `name`, `medicament`, `medicine`, `produit`, `libelle`.
- Colonnes prix reconnues automatiquement:
  - bornes: `min_price`, `max_price`, `prix_min`, `prix_max`, `pu_min`, `pu_max`
  - valeur unique: `price`, `prix`, `unit_price`, `pu`, `pph`, `ppv`, `pht`, `tarif`, `montant`

Si la base medicaments n'est pas presente, le generateur utilise une liste interne de secours.

## Sortie

- Images: `output/images/*.png` ou `dataset_v2/images/{train,val,test}/*.png`
- Annotations: `output/annotations/*.json` ou `dataset_v2/annotations/{train,val,test}/*.json`

Exemple annotation:

```json
{
  "doc_id": "bl_000001",
  "bl_number": "KEN-26-00001-523991",
  "date": "14/04/2026",
  "supplier": {
    "name": "KENIPHARMA",
    "address": "Lotissement Industriel, Skhirat",
    "phone": "05 37 30 70 00",
    "city": "Skhirat"
  },
  "products": [
    {
      "designation": "VENTOLINE AEROSOL",
      "qty": 2,
      "unit_price": 42.2,
      "line_total": 84.4,
      "pph": 56.8,
      "tva": 0.07,
      "code_produit": "348192"
    }
  ],
  "totals": {
    "ht": 84.4,
    "tva": 5.91,
    "ttc": 90.31,
    "total_qty": 2
  }
}
```
