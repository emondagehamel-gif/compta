"""Logo de l'application : la feuille des factures, blanche sur un carré vert arrondi. Produit les icônes (PWA, Windows) et un aperçu."""
import asyncio, subprocess, os
from playwright.async_api import async_playwright
OUT = "logo"; os.makedirs(OUT, exist_ok=True)
LEAF = ('<path d="M30 70C17.6 40 55.9 29.9 74 26C70.1 44.1 60 82.4 30 70Z" fill="#FFFFFF"/>'
        '<path d="M30.5 69.5L21 79" stroke="#FFFFFF" stroke-width="4.6" stroke-linecap="round" fill="none"/>'
        '<path d="M33 67C44 56 55 45 66.5 33.5" stroke="#2C6B39" stroke-width="3.2" stroke-linecap="round" fill="none"/>')
def svg(size, radius, scale):
    r = radius * 100
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{size}" height="{size}">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="#3F8C4D"/><stop offset="1" stop-color="#235A2F"/></linearGradient></defs>'
            f'<rect width="100" height="100" rx="{r}" fill="url(#g)"/>'
            f'<g transform="translate(50 50) scale({scale}) translate(-48 -52)">{LEAF}</g></svg>')
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        jobs = [("icon-feuille-512", 512, .22, 1.12), ("icon-feuille-192", 192, .22, 1.12), ("icon-feuille-maskable", 512, 0, .92), ("apple-touch-icon-feuille", 180, 0, 1.08),
                ("ico-256", 256, .2, 1.15), ("ico-48", 48, .2, 1.2), ("ico-32", 32, .2, 1.25), ("ico-16", 16, .18, 1.3)]
        for name, size, rad, sc in jobs:
            pg = await b.new_page(viewport={"width": size, "height": size})
            await pg.set_content('<html><body style="margin:0;background:transparent">' + svg(size, rad, sc) + "</body></html>")
            await pg.screenshot(path=f"{OUT}/{name}.png", omit_background=True, clip={"x": 0, "y": 0, "width": size, "height": size}); await pg.close()
        await b.close()
    subprocess.run(["convert", f"{OUT}/ico-16.png", f"{OUT}/ico-32.png", f"{OUT}/ico-48.png", f"{OUT}/ico-256.png", f"{OUT}/Comptabilite.ico"], check=True)
    open(f"{OUT}/feuille.svg", "w").write(svg(512, .22, 1.12))
asyncio.run(main())
print("ok")
