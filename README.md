# Schoolradar Nederland

A static website for exploring Dutch primary and secondary schools with DUO Open Onderwijsdata.

Primary schools use the BO/SBO type filter. Secondary schools have a separate programme filter for VMBO, HAVO, and VWO; it can be combined with postcode radius up to 65 km and distance sorting.

## VWO measures

Primary education (BO/SBO) uses final school advice:

- default: `VWO / all definite final advice categories`
- optional: `(VWO + HAVO_VWO) / all definite final advice categories`

Secondary education (VO) uses actual enrollment by level:

- default: `VWO pupils / pupils with a defined PRO, vmbo, havo, HAVO/VWO, or vwo level`
- optional: `(VWO + mixed HAVO/VWO pupils) / pupils with a defined level`
- bridge classes and pupils outsourced to VAVO are excluded from this level denominator

DUO values published as `<5` are preserved as ranges. The UI shows percentage ranges and ranks by the conservative lower bound first. The BO/SBO and VO percentages describe different stages and should not be interpreted as the same measure.

## Data

Local refresh completed on 2026-09-21:

- generated schools: 8,138
- primary locations: 6,452
- secondary locations: 1,686
- primary locations with advice ratios: 6,323
- secondary locations with enrollment ratios: 1,391
- secondary locations with a full five-year enrollment history: 1,354
- locations with postcode-origin data: 7,810
- locations with background/residence ratios: 7,838
- locations with coordinates: 7,564

The builder reads these official DUO sources:

- PO school advice: `https://duo.nl/open_onderwijsdata/images/04-leerlingen-bo-sbo-schooladviezen-2024-2025.csv`
- PO pupil totals: `https://duo.nl/open_onderwijsdata/images/01.-leerlingen-po-soort-po-cluster-leeftijd-2025-2026.csv`
- PO school addresses: `https://duo.nl/open_onderwijsdata/images/02.-alle-schoolvestigingen-basisonderwijs.csv`
- VO school addresses: `https://duo.nl/open_onderwijsdata/images/02.-alle-vestigingen-vo.csv`
- VO pupils by level, 2021-2025: `https://duo.nl/open_onderwijsdata/voortgezet-onderwijs/aantal-leerlingen/aantal-leerlingen.jsp`
- VO pupils by home postcode, 2025: `https://duo.nl/open_onderwijsdata/images/02.-leerlingen-per-vestiging-naar-postcode-en-leerjaar-2025.csv`
- DUO/RIO coordinates: `https://onderwijsdata.duo.nl/dataset/c416acd1-e083-4ec6-9203-3b20f98fe143/resource/a7e3f323-6e46-4dca-a834-369d9d520aa8/download/onderwijslocaties.csv`
- PO pupil origin by postcode4: `https://onderwijsdata.duo.nl/datasets/popostcode4-v1`
- PO five-year advice history: `https://onderwijsdata.duo.nl/datasets/wpoadvies-v1`
- PO student background: `https://onderwijsdata.duo.nl/datasets/poachtergrond`

For BO/SBO, international sorting uses DUO's NOAT/CUMI/NNCA background indicator; this is not exact nationality. For VO, it uses the share of pupils whose published residence category is Belgium, Germany, or other foreign country. Unknown addresses are excluded. This is residence, not nationality or cultural background.

Satisfaction sorting remains visible, but these DUO files do not publish a comparable school-level satisfaction score.

## Build the dataset

```powershell
python .\tools\update_duo_data.py --refresh
```

Without `--refresh`, the script reuses source files already present in `data/raw`.

## Validate the project

```powershell
python .\tools\validate_project.py
```

This checks JavaScript and Python syntax, HTML/CSS structure, the Pages workflow, generated-data invariants, published statistics, and the optional `github-upload` mirror. The GitHub Pages workflow runs the same validation after every data refresh.

## Run locally

```powershell
python -m http.server 4173
```

Open `http://localhost:4173/`.

## Publish on GitHub Pages

This repository includes `.github/workflows/pages.yml`.

1. Upload or commit the source files, excluding `data/raw` and `data/schools.json`.
2. In GitHub, open **Settings -> Pages** and select **GitHub Actions** if requested.
3. Push to `main` or manually run **Deploy GitHub Pages**.

The workflow downloads DUO data and builds `data/schools.json` during deployment. The generated JSON is over GitHub's browser-upload limit and should not be uploaded manually.
