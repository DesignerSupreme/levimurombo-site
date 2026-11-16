# levimurombo.space

Portfolio and CV site for Levison (Levi) T. Murombo, designer and art director in Harare.
One static page, no build step. Hosted on Vercel from this repo:

- Push to `main` = live on levimurombo.space in about a minute.
- Push any other branch = Vercel preview URL (shown in the GitHub commit status / PR checks).

## How to make a change

1. Read the relevant part of `index.html` first. Make the smallest change that does the job.
2. Work on a branch named `edit/<short-topic>` unless Levi says "push it live".
3. Run `python3 tools/qa.py` from the repo root. Every check must pass. Never weaken a check to get a pass.
4. Push the branch, open a PR, and give Levi the Vercel preview link plus a short checks table
   (requirement, verdict, evidence). Merge to `main` only when he approves.
5. Report what changed, what passed and anything still open.

Ask before anything that publishes, deletes or spends. Previous versions live in git history, so revert with a new commit rather than rewriting history.

## Stack (keep it this way)

- Single `index.html`: all CSS in `<head>`, all JS at the end of `<body>`. No framework, no npm, no bundler.
- CDN libraries pinned to exact versions: GSAP 3.12.5 + ScrollTrigger (cdnjs), Lenis 1.1.13 (jsdelivr), three.js r128 (cdnjs).
- The hero bust is built in three.js inside the `bust()` function (contour rings plus a dark occluder, head and torso groups).
  It is a stand-in. When Levi's scan exists as `img/bust.glb`, set `BUST_GLB` and add GLTFLoader r128.
- Fonts from Google Fonts: Big Shoulders Display (variable 100..900), Instrument Sans, Instrument Serif, JetBrains Mono, Mrs Saint Delafield (stand-in signature).

## Map of index.html

v2 layout (Nov 2026), modelled on the structure of landonorris.com. Sections in page order: loader (counter), nav, `#hero` (name LEVI / MUROMBO behind a 3D contour bust that turns to follow the cursor; `#lockBtn` "tap to lock"; "now building" status; Start a project and View CV), client marquee, note (bold key words + signature that draws itself), `#strip` (captioned work strip, pinned horizontal on wide screens, with the ZITF award marker and pull lines), On Brief / Off Brief split, `#onbrief` (index of 21 client projects with hover preview, built from `INDEX`), `#offbrief` (NHAKA, Harare 3D, poster wall), `#hall` (hall of fame, mark then mark in use on hover, built from `HOF`), `#films` (six films, play on select, built from `FILMS`), `#contact` (work with me), footer wordmark. Overlays: `#case` (case study), `#lb` (poster lightbox), `#termx` (hidden terminal: lock the bust three times, or type "levi").

Key JS objects:

- `CASES`: all 22 case studies. Fields: `t` (title lines), `client`, `scope`, `region`, `desc`, `img` (gallery).
  Gallery item formats: `['slug']` image, `['slug','full']` full-width image, `['slug','','v','poster-slug']` video.
  Slugs map to files in `img/` (`img/<slug>.webp`, videos `img/<slug>.mp4`).
- `ORDER`: the order of the 22 cases (drives numbering "01 / 22" and the terminal `ls`).
- `C2`: terminal commands. `INDEX`, `HOF`, `FILMS`: data for the On Brief index, hall of fame and films.
- Any `<button data-case="<key>">` opens that case study.
- Deep links: `levimurombo.space/#<case-key>` opens that case study.
- `cv.html` (served at `/cv`): one-page CV that prints to PDF. Every fact on it must already be on the main site. Swap for Levi's own PDF when he supplies one.

## Adding work

- Images: WebP, long edge 1600 to 2000 px, ideally under 350 KB. Give every `<img>` width and height attributes.
- Videos: H.264 MP4, silent web cut, under about 6 MB, with a poster image.
- New case study: add it to `CASES` and `ORDER`, then add it to `INDEX` (and optionally the strip or `HOF`).

## Content rules from Levi (non-negotiable)

- Never use em dashes anywhere (copy, code comments, commit messages).
- Never invent testimonials, client quotes, ratings or results.
- AURA Technologies internal numbers are not approved for public use. The "fastest-growing Starlink reseller" recognition can be mentioned.
- Do not present AI-generated imagery as client work.
- No photos of AURA colleagues.
- The site must not read like an AURA website. AURA is one client among many.
- Contact details: levimurombo@gmail.com, +263 773 766 393.
- The 12 brand-index descriptions were written from the visuals. Levi still needs to confirm them.

## Design language

Bold and kinetic (references: dopaminestudio.io, carterogunsola.com). Dark by choice.
Tokens on `:root`: `--bg #0E0D0B`, `--bg-2 #181612`, `--ink #F1ECE2`, `--mute #9A9488`, `--line #2B2823`, `--zuva #F4B52C` (accent), `--on-zuva #14110A`, `--ok #7CFC9A`.
Respect `prefers-reduced-motion` (no loader, 3D shown fully built, no smooth scroll). Mobile (390 px) must have no horizontal overflow.

## Gotchas

- `[hidden]{display:none!important}` exists because `img,video{display:block}` would otherwise beat the `hidden` attribute.
- The main script is one big function scope. Search for a `var` name before adding one; a duplicate `lastY` once broke the hide-on-scroll nav.
- three.js r128 with sRGB output: pass colours through `lin(0xRRGGBB)` or materials render washed out.
- Headless test browsers render WebGL slowly (2 to 7 FPS). That is the test machine, not the site.
- `tools/out/` holds QA screenshots and is git-ignored.
