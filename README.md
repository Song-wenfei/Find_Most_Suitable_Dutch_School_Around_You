# Schoolradar VWO

A static website for exploring Dutch primary schools with DUO Open Onderwijsdata.

The VWO ratio is calculated from DUO's `Schooladviezen` file:

- default ratio: `(VWO + HAVO_VWO) / all definite final advice categories`
- strict ratio: `VWO / all definite final advice categories`
- DUO values published as `<5` are preserved as ranges, so the UI shows a percentage range when the exact count is privacy masked

## Data

The builder reads these official sources:

- DUO school advice: `https://duo.nl/open_onderwijsdata/images/04-leerlingen-bo-sbo-schooladviezen-2024-2025.csv`
- DUO pupil totals: `https://duo.nl/open_onderwijsdata/images/01.-leerlingen-po-soort-po-cluster-leeftijd-2025-2026.csv`
- DUO school addresses: `https://duo.nl/open_onderwijsdata/images/02.-alle-schoolvestigingen-basisonderwijs.csv`
- DUO/RIO locations: `https://onderwijsdata.duo.nl/dataset/c416acd1-e083-4ec6-9203-3b20f98fe143/resource/a7e3f323-6e46-4dca-a834-369d9d520aa8/download/onderwijslocaties.csv`
- DUO pupil origin by postcode4: `https://onderwijsdata.duo.nl/datasets/popostcode4-v1`
- DUO 5-year advice history: `https://onderwijsdata.duo.nl/datasets/wpoadvies-v1`
- DUO student background: `https://onderwijsdata.duo.nl/datasets/poachtergrond`

Pupil origin is shown as the ratio of pupils living in each 4-digit postcode area (`POSTCODE4_DEELNEMER`) for that school branch.
Student background is DUO's NOAT/CUMI/NNCA indicator. It is not individual nationality data.
Satisfaction sorting is present in the UI, but DUO does not provide a public school-level satisfaction score in these datasets.

## Build the dataset

```powershell
python .\tools\update_duo_data.py --refresh
```

Without `--refresh`, the script reuses CSV files already present in `data/raw`.

## Run locally

```powershell
python -m http.server 4173
```

Open `http://localhost:4173/`.

## Publish on GitHub Pages

This repository includes `.github/workflows/pages.yml`.

1. Create a GitHub repository with a `main` branch.
2. Upload/commit the source files in this folder, excluding `data/raw` and `data/schools.json`.
3. In GitHub, open **Settings -> Pages** and use **GitHub Actions** as the Pages source if GitHub asks.
4. Push to `main` or run the `Deploy GitHub Pages` workflow manually.

The workflow downloads DUO data and builds `data/schools.json` during deployment.
