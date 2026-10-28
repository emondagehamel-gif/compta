import asyncio
from playwright.async_api import async_playwright
BOOK = '<path d="M5 5a2 2 0 0 1 2-2h11v15H7a2 2 0 0 0-2 2z"/><path d="M5 20a2 2 0 0 0 2 1h11v-3"/><path d="M9 7h6M9 11h4"/>'
def page(size, radius, scale):
    ic = size * scale
    return f'''<html><body style="margin:0;background:transparent"><div style="width:{size}px;height:{size}px;border-radius:{radius*size}px;background:linear-gradient(160deg,#2F58C4,#1D3C8F);display:flex;align-items:center;justify-content:center">
<svg viewBox="0 0 24 24" width="{ic}" height="{ic}" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{BOOK}</svg></div></body></html>'''
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, size, rad, sc in [("icon-512", 512, .22, .58), ("icon-192", 192, .22, .58), ("icon-maskable", 512, 0, .46), ("apple-touch-icon", 180, 0, .58)]:
            pg = await b.new_page(viewport={"width": size, "height": size})
            await pg.set_content(page(size, rad, sc))
            await pg.screenshot(path=f"pwa/dist/{name}.png", omit_background=True, clip={"x":0,"y":0,"width":size,"height":size})
            await pg.close()
        await b.close()
asyncio.run(main())
