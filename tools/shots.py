# Tar skjermbilder av appen (kjøres i GitHub Actions, der kartflisene kan lastes)
from playwright.sync_api import sync_playwright
U = "https://elenahjelpen.com/"
with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, locale="nb-NO")
    pg = c.new_page()
    pg.goto(U + "#kart"); pg.wait_for_timeout(6000)
    pg.evaluate("""() => { const r = map.data.find(x => x[0].includes('La Loma')); map.m.setView([r[1]+0.006, r[2]], 15);
        LF.popup({maxWidth:260}).setLatLng([r[1], r[2]]).setContent(popupHtml(r)).openOn(map.m); }""")
    pg.wait_for_timeout(5000)
    pg.evaluate("document.querySelector('#map').scrollIntoView({block:'end'})"); pg.wait_for_timeout(1500)
    pg.screenshot(path="tools/shots/kart-popup.png")
    pg.goto(U + "#kart"); pg.wait_for_timeout(5000)
    pg.fill("#mapQ", "Calle Caballero de Rodas 10, Torrevieja")
    pg.evaluate("() => { syncQx(); setPoint(37.9786, -0.6822, 'Calle Caballero de Rodas 10'); }")
    pg.wait_for_timeout(5000)
    pg.evaluate("document.querySelector('#mapNear').scrollIntoView({block:'end'})"); pg.wait_for_timeout(1500)
    pg.screenshot(path="tools/shots/kart-naer.png")
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(1000)
    pg.screenshot(path="tools/shots/kart-sok.png")
    b.close()
