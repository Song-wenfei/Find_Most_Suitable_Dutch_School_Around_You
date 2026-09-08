# Home AI Handoff: Schoolradar VWO

Use this document to continue the project in another AI environment.

## Project Objective

Build and publish a public website for finding Dutch primary schools around a postcode/place, using DUO Open Onderwijsdata.

The main ranking metric is the share of pupils receiving VWO final advice. The site also shows:

- schools within a selected radius
- BO/SBO filtering
- VWO ratio ranking, distance ranking, international/background ranking, and placeholder satisfaction ranking
- map and distribution map
- 5-year VWO advice history
- student origin by postcode4
- DUO background indicators: NNCA/NOAT/CUMI

## Local Project Path

```text
C:\DATA\Projects\Codex_projects\duo-school-vwo
```

Upload-ready folder:

```text
C:\DATA\Projects\Codex_projects\duo-school-vwo\github-upload
```

The `github-upload` folder contains only small source files and is intended for manual GitHub upload.

## Last Local Refresh

The local DUO dataset was refreshed on 2026-09-07.

Generated file:

```text
data/schools.json
```

Current generated-data stats:

- schools: 6,452
- schools with advice ratio data: 6,323
- schools with 5-year advice history: 6,341
- schools with origin postcode4 data: 6,357
- schools with background ratio data: 6,385
- schools with coordinates: 5,986

National BO strict-VWO sanity check after refresh:

- p10: 4.2%
- p25: 12.1%
- median: 19.9%
- p75: 27.9%
- p90: 36.4%
- p95: 43.4%

## GitHub Repository

```text
Song-wenfei/Find_Most_Suitable_Dutch_School_Around_You
```

Expected public GitHub Pages URL:

```text
https://song-wenfei.github.io/Find_Most_Suitable_Dutch_School_Around_You/
```

## Important Upload Rule

Do not manually upload:

```text
data/
data/schools.json
data/raw/
.edge-profile/
```

`data/schools.json` is about 26 MB and exceeds GitHub web upload limits. It must be generated during GitHub Actions deployment.

Upload only:

```text
index.html
app.js
styles.css
README.md
.gitignore
tools/update_duo_data.py
.github/workflows/pages.yml
```

The workflow file must be exactly:

```text
.github/workflows/pages.yml
```

Not `.github`, not `pages.yml` at root.

## Current Deployment Workflow

The workflow name is:

```text
Deploy GitHub Pages
```

It runs on:

- push to `main`
- manual `workflow_dispatch`

It does:

1. checkout repo
2. install Python 3.11
3. run `python tools/update_duo_data.py --refresh`
4. remove `data/raw`
5. upload the whole static site as the GitHub Pages artifact
6. deploy to Pages

If the Actions tab does not show `Deploy GitHub Pages`, the workflow file is missing or in the wrong path.

## Data Sources

The data builder uses official DUO sources:

- DUO school advice 2024-2025
- DUO pupil totals 2025-2026
- DUO school addresses
- DUO/RIO locations
- DUO pupil origin by postcode4
- DUO 5-year advice history
- DUO background data

Main builder:

```text
tools/update_duo_data.py
```

Generated site data:

```text
data/schools.json
```

## VWO Ratio Rules

The VWO ratio must be presented conservatively and transparently.

Default metric:

```text
VWO / all definite final advice categories
```

Optional broader metric:

```text
(VWO + HAVO_VWO) / all definite final advice categories
```

Important:

- `ADVIES_NIET_MOGELIJK` must be excluded from the denominator.
- DUO privacy values `<5` and API `-1` are treated as range `1-4`.
- The UI must show a range when exact values are privacy-masked.
- VWO sorting uses the lower bound first, then midpoint as tie-breaker.
- International sorting uses the lower bound of DUO NNCA/background percentage first, then midpoint and VWO as tie-breakers.
- Do not present masked data as exact percentages.

Example:

```text
VWO 22 / 54-60 definite advice cohort
```

## Previous VWO Bug That Was Fixed

There was a bad range problem where a school such as De Triangel Houten could show `6%-100%`.

Fixes already applied:

- historical advice code `12` / `ADVIES_NIET_MOGELIJK` is excluded
- BO and SBO source rows are type-matched before merging history/background
- ratio bounds are calculated with constrained numerator/other-category ranges
- the frontend and Python builder use the same bounded-ratio logic

Do not revert these changes.

## NNCA / NOAT / CUMI Meaning

Do not describe this as exact nationality.

- NNCA = Niet-Nederlandse Culturele Achtergrond
- NOAT = Nederlands Onderwijs aan Anderstaligen, used for regular BO context
- CUMI = cultural-minority indicator, used for SBO/SO/VSO context

In this app, these are DUO background indicators, not individual passport/citizenship data.

## UI State

Current intended UI behavior:

- strict VWO is default
- HAVO/VWO is optional via checkbox
- sort options include VWO-ratio, distance, international, and satisfaction
- international sort uses DUO NNCA/NOAT/CUMI background ratio; it is not exact nationality
- cards show `VWO count / advice cohort`
- uncertainty chip: `breed DUO-bereik`
- detail panel shows the calculation line
- map uses Leaflet/OpenStreetMap, not Google Maps
- distribution map explanation:
  - color = VWO ratio, orange lower to green higher
  - size = number of pupils in the advice cohort
  - each dot = one school

## Local Run

From the project root:

```powershell
python -m http.server 4173
```

Open:

```text
http://localhost:4173/
```

Example query:

```text
http://localhost:4173/?q=3992&radius=2.5&type=Bo&sort=vwo
```

## Build Data Locally

Use:

```powershell
python tools/update_duo_data.py --refresh
```

Without `--refresh`, the script reuses existing files in `data/raw`.

## Known Constraints

- Git is not installed in the current local environment.
- GitHub connector could read the repo but failed to write with `403 Resource not accessible by integration`.
- Manual GitHub upload was being used.
- GitHub web upload rejects files over 25 MB, so `data/schools.json` must not be uploaded.
- The GitHub workflow must build `data/schools.json` during deployment.

## Next Likely Tasks

1. Confirm GitHub repo contains:

```text
index.html
app.js
styles.css
README.md
.gitignore
tools/update_duo_data.py
.github/workflows/pages.yml
```

2. In GitHub:

```text
Settings -> Pages -> Source: GitHub Actions
Actions -> Deploy GitHub Pages -> Run workflow
```

3. If workflow fails:

- inspect the failed step log
- most likely causes are missing `tools/update_duo_data.py`, wrong workflow path, or DUO download/source change

4. After deploy succeeds, test:

```text
https://song-wenfei.github.io/Find_Most_Suitable_Dutch_School_Around_You/
```

## Prompt For Home AI Model

Copy this section into the other AI model:

```text
You are continuing a static website project named Schoolradar VWO.

Goal: help publish and improve a Dutch school finder using DUO Open Onderwijsdata.

Read HOME_AI_HANDOFF.md, README.md, app.js, tools/update_duo_data.py, index.html, and styles.css first.

Preserve these data rules:
- default VWO ratio is strict VWO / all definite final advice categories
- exclude ADVIES_NIET_MOGELIJK from denominators
- treat DUO <5 and API -1 privacy values as 1-4 ranges
- show percentage ranges instead of fake exact values
- rank VWO conservatively by lower bound first
- NNCA/NOAT/CUMI are background indicators, not exact nationality

Deployment target:
GitHub Pages for Song-wenfei/Find_Most_Suitable_Dutch_School_Around_You.

Do not upload data/schools.json or data/raw. The GitHub Actions workflow must generate data/schools.json during deployment.

Current likely next step: verify the GitHub repo has .github/workflows/pages.yml and tools/update_duo_data.py, then run the Deploy GitHub Pages workflow.
```
