"""Smoke test for levimurombo.space. Run from the repo root before every push:

    python3 tools/qa.py

Checks: missing image references, em dashes, page errors, failed requests,
horizontal overflow at 1440 / 768 / 390 px, every project card and index row
opening the right case study, terminal and command palette, reduced motion.
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
                res = []
                for sel in ('#track .card', '#ix button'):
                    n = await pg.locator(sel).count()
                    for i in range(n):
                        k = await pg.locator(sel).nth(i).get_attribute('data-case')
                        await pg.wait_for_function("document.getElementById('case').hidden", timeout=5000)
                        await pg.wait_for_timeout(200)
                        await pg.evaluate("document.querySelectorAll('%s')[%d].click()" % (sel, i))
                        try:
                            await pg.wait_for_function("location.hash==='#%s' && !document.getElementById('case').hidden" % k, timeout=4000)
                            res.append((k, True))
                        except Exception:
                            res.append((k, False))
                        await pg.keyboard.press('Escape')
                badk = [k for k, ok in res if not ok]
                check(res and not badk, 'all %d cards and index rows open their case study %s' % (len(res), badk[:6] or ''))
                await pg.evaluate("document.getElementById('terminal').scrollIntoView()")
                await pg.wait_for_timeout(1500)
                await pg.fill('#tin', 'open soul')
                await pg.press('#tin', 'Enter')
                await pg.wait_for_timeout(1200)
                check(await pg.evaluate("location.hash==='#soul'"), 'terminal "open soul" opens Soul Avenue')
                await pg.keyboard.press('Escape')
                await pg.wait_for_timeout(1000)
                await pg.keyboard.press('Control+k')
                await pg.wait_for_timeout(300)
                await pg.keyboard.type('hurungwe')
                await pg.wait_for_timeout(200)
                await pg.keyboard.press('Enter')
                await pg.wait_for_timeout(1200)
                check(await pg.evaluate("location.hash==='#hurungwe'"), 'command palette opens Hurungwe')
                await pg.keyboard.press('Escape')
            await pg.close()
        ctx = await b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        pg = await ctx.new_page()
        await pg.goto(URL)
        await pg.wait_for_timeout(1200)
        st = await pg.evaluate("[getComputedStyle(document.getElementById('loader')).display, document.getElementById('encN').textContent===document.getElementById('encT').textContent]")
        check(st[0] == 'none' and st[1], 'reduced motion: no loader, 3D shown fully built')
        await b.close()

try:
    asyncio.run(main())
finally:
    srv.terminate()

print('\n%d check(s) failed' % len(fails) if fails else '\nAll checks passed')
sys.exit(1 if fails else 0)
