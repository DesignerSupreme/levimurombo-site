"""Smoke test for levimurombo.space. Run from the repo root before every push:

    python3 tools/qa.py

Checks: missing image references, em dashes, page errors, failed requests,
horizontal overflow at 1440 / 768 / 390 px, hero fits above the fold, 3D bust renders and
locks, captioned strip, On/Off Brief split, hall of fame hover swap, films, every project link
opening the right case study, poster lightbox, hidden terminal, reduced motion.
Exits with code 1 if anything fails. Screenshots go to tools/out/.
"""
import asyncio, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', 'out')
os.makedirs(OUT, exist_ok=True)
PORT = 8791
fails = []


def check(ok, label):
    print(('PASS  ' if ok else 'FAIL  ') + label)
    if not ok:
        fails.append(label)


# ---------- static checks ----------
html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
refs = set(re.findall(r'''(?:src|href|poster)=["'](img/[^"']+)["']''', html))
refs |= {'img/%s.webp' % n for n in re.findall(r"""\[['"]([a-z0-9-]+)['"](?:,['"](?:full|v)?['"])*""", html)
         if os.path.exists(os.path.join(ROOT, 'img', n + '.webp'))}
missing = sorted(r for r in refs if not os.path.exists(os.path.join(ROOT, r)))
check(not missing, 'image references resolve %s' % (missing[:5] or ''))
check(chr(0x2014) not in html, 'no em dashes in index.html')
check(html.lstrip().lower().startswith('<!doctype html>'), 'index.html is a full document')

# ---------- browser checks ----------
try:
    from playwright.async_api import async_playwright
except ImportError:
    print('Playwright not installed: pip install playwright && playwright install chromium')
    sys.exit(1)

srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '-d', ROOT],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
URL = 'http://localhost:%d/index.html' % PORT
GL = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']


async def launch(p):
    try:
        return await p.chromium.launch(args=GL)
    except Exception:
        return await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=GL)


async def main():
    async with async_playwright() as p:
        b = await launch(p)
        for w, h, mob in [(1440, 900, False), (768, 1024, True), (390, 844, True)]:
            pg = await b.new_page(viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob)
            errs, bad = [], []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('response', lambda r: bad.append(r.url) if r.status >= 400 else None)
            await pg.goto(URL)
            await pg.wait_for_timeout(4200)
            await pg.screenshot(path=os.path.join(OUT, 'hero-%d.png' % w))
            H = await pg.evaluate('document.documentElement.scrollHeight')
            sw = []
            for f in (.15, .35, .55, .75, .95):
                await pg.evaluate('window.scrollTo(0,%d)' % int(f * H))
                await pg.wait_for_timeout(500)
                sw.append(await pg.evaluate('document.documentElement.scrollWidth'))
            check(max(sw) <= w, '%dpx no horizontal overflow (max scrollWidth %d)' % (w, max(sw)))
            check(not errs, '%dpx no page errors %s' % (w, errs[:2] or ''))
            check(not bad, '%dpx no failed requests %s' % (w, bad[:3] or ''))
            if w == 1440:
                for vw, vh in ((1440, 900), (1366, 660)):
                    await pg.set_viewport_size({'width': vw, 'height': vh})
                    await pg.evaluate('window.scrollTo(0,0)')
                    await pg.wait_for_timeout(700)
                    fb = await pg.evaluate("document.querySelector('.hero-foot').getBoundingClientRect().bottom")
                    check(fb <= vh, 'hero name and buttons fit above the fold at %dx%d (bottom %d)' % (vw, vh, fb))
                await pg.set_viewport_size({'width': w, 'height': h})
                cta = await pg.evaluate("[...document.querySelectorAll('.hero-cta a')].map(a=>a.getAttribute('href'))")
                check(cta == ['#contact', 'cv.html'] and os.path.exists(os.path.join(ROOT, 'cv.html')), 'hero has Start a project and View CV buttons %s' % cta)
                bs = await pg.evaluate("[!!(window.BUST&&BUST.ready), (window.BUST&&BUST.frames)||0]")
                check(bs[0] and bs[1] > 0, '3D bust renders (frames %d)' % bs[1])
                await pg.evaluate("window.scrollTo(0,0)")
                await pg.wait_for_timeout(400)
                await pg.click('#lockBtn')
                lk = await pg.evaluate("[document.getElementById('lockBtn').getAttribute('aria-pressed'), BUST.locked]")
                await pg.click('#lockBtn')
                lk2 = await pg.evaluate("document.getElementById('lockBtn').getAttribute('aria-pressed')")
                check(lk == ['true', True] and lk2 == 'false', 'tap to lock toggles the bust %s %s' % (lk, lk2))
                fg = await pg.evaluate("[...document.querySelectorAll('#track figure')].filter(f=>f.querySelector('img')&&f.querySelector('figcaption b')).length")
                check(fg >= 8, 'captioned work strip has 8+ captioned images (%d)' % fg)
                sp = await pg.evaluate("[...document.querySelectorAll('.split a')].map(a=>a.getAttribute('href'))")
                check(sp == ['#onbrief', '#offbrief'], 'On Brief / Off Brief split links %s' % sp)
                nix = await pg.evaluate("document.querySelectorAll('#ix button').length")
                check(nix == 21, 'On Brief index lists every client project except NHAKA (%d)' % nix)
                hc = await pg.evaluate("[...document.querySelectorAll('.hc')].filter(c=>c.querySelectorAll('.ph img').length===2).length")
                check(hc >= 8, 'hall of fame has 8+ cards with a hover pair (%d)' % hc)
                await pg.evaluate("document.getElementById('hall').scrollIntoView()")
                await pg.wait_for_timeout(1500)
                await pg.hover('.hc >> nth=0')
                await pg.wait_for_timeout(900)
                op = await pg.evaluate("+getComputedStyle(document.querySelector('.hc .ph img.b')).opacity")
                check(op > .9, 'hall of fame hover swaps to the in-use image (opacity %.2f)' % op)
                fl = await pg.evaluate("[...document.querySelectorAll('.film video')].filter(v=>v.getAttribute('poster')&&v.dataset.src).length")
                check(fl == 6, 'six films with posters (%d)' % fl)
                await pg.evaluate("document.querySelector('.film').click()")
                await pg.wait_for_timeout(300)
                fs = await pg.evaluate("!!document.querySelector('.film video').getAttribute('src')")
                check(fs, 'selecting a film loads it')
                await pg.evaluate("document.querySelector('.film[data-on=true]')&&document.querySelector('.film[data-on=true]').click()")
                res = []
                n = await pg.locator('main [data-case]').count()
                for i in range(n):
                    k = await pg.locator('main [data-case]').nth(i).get_attribute('data-case')
                    await pg.wait_for_function("document.getElementById('case').hidden", timeout=5000)
                    await pg.wait_for_timeout(150)
                    await pg.evaluate("document.querySelectorAll('main [data-case]')[%d].click()" % i)
                    try:
                        await pg.wait_for_function("location.hash==='#%s' && !document.getElementById('case').hidden" % k, timeout=4000)
                        res.append((k, True))
                    except Exception:
                        res.append((k, False))
                    await pg.keyboard.press('Escape')
                badk = [k for k, ok in res if not ok]
                check(len(res) >= 30 and not badk, 'all %d project links open their case study %s' % (len(res), badk[:6] or ''))
                await pg.wait_for_function("document.getElementById('case').hidden", timeout=5000)
                await pg.evaluate("document.getElementById('posterBtn').click()")
                await pg.wait_for_timeout(300)
                check(await pg.evaluate("!document.getElementById('lb').hidden && document.getElementById('lbImg').naturalWidth>=0"), 'poster wall opens the lightbox')
                await pg.keyboard.press('Escape')
                await pg.evaluate("window.scrollTo(0,0)")
                await pg.wait_for_timeout(500)
                for _ in range(3):
                    await pg.click('#lockBtn')
                    await pg.wait_for_timeout(120)
                await pg.wait_for_timeout(300)
                check(await pg.evaluate("!document.getElementById('termx').hidden"), 'locking the bust three times opens the hidden terminal')
                await pg.fill('#tin', 'open soul')
                await pg.press('#tin', 'Enter')
                await pg.wait_for_timeout(1200)
                check(await pg.evaluate("location.hash==='#soul' && document.getElementById('termx').hidden"), 'terminal "open soul" opens Soul Avenue')
                await pg.keyboard.press('Escape')
                await pg.wait_for_timeout(1000)
                await pg.keyboard.type('levi')
                await pg.wait_for_timeout(200)
                check(await pg.evaluate("!document.getElementById('termx').hidden"), 'typing "levi" opens the hidden terminal')
                await pg.keyboard.press('Escape')
            await pg.close()
        ctx = await b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        pg = await ctx.new_page()
        await pg.goto(URL)
        await pg.wait_for_timeout(1200)
        st = await pg.evaluate("[getComputedStyle(document.getElementById('loader')).display, !!(window.BUST&&BUST.static&&BUST.frames>0)]")
        check(st[0] == 'none' and st[1], 'reduced motion: no loader, bust shown fully built and still %s' % st)
        await pg.screenshot(path=os.path.join(OUT, 'reduced-1440.png'))
        await b.close()

try:
    asyncio.run(main())
finally:
    srv.terminate()

print('\n%d check(s) failed' % len(fails) if fails else '\nAll checks passed')
sys.exit(1 if fails else 0)
