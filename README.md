# levimurombo.space

Portfolio and CV of Levison T. Murombo, designer and art director, Harare.

Static single-page site: a three.js bust hero that follows the cursor, a captioned work strip, On Brief / Off Brief, a hall of fame, films, 22 case studies and a hidden terminal. No build step.

## Run locally

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Deploy

Hosted on Vercel, connected to this repo.

- `main` deploys to production (levimurombo.space).
- Every other branch gets its own preview URL.

## Edit with Claude

Open a Claude chat that has GitHub access and say, for example:

> In DesignerSupreme/levimurombo-site, swap the Max Unisex Salon images for the new ones I attached. Put it on a preview branch.

Claude reads `CLAUDE.md`, makes the change, runs `python3 tools/qa.py`, pushes a branch and sends the preview link. Merge the pull request (or tell Claude to) when you are happy, and it goes live.

## Checks

```
pip install playwright
python3 tools/qa.py
```
