import asyncio
import json
import re
import random
from datetime import datetime
from playwright.async_api import async_playwright

# ============================================================
# CONFIGURACIÓN
# ============================================================
TARGET_PROFILE = "amarantavp"
OUTPUT_JSON = "perfil_amarantavp_final.json"
TU_SESSION = "78502088557:g9UdNvtwGssxUa:22:AYjgwaoeV-fi1UA--Y_cYpgy2zGAzneGEyRiPg27Uw"
# ============================================================

async def extract_list_humano(page, modal_url_part, limit=100):
    users = []
    try:
        print(f"   [→] Abriendo lista de {modal_url_part}...")
        await page.wait_for_selector(f'a[href*="/{modal_url_part}/"]', state="visible")
        await page.locator(f'a[href*="/{modal_url_part}/"]').first.click()
        await page.wait_for_selector('div[role="dialog"]', timeout=10000)
        await asyncio.sleep(3)

        intentos_sin_nuevos = 0
        while len(users) < limit and intentos_sin_nuevos < 8:
            cantidad_anterior = len(users)
            
            # Extraer nombres visibles
            nuevos = await page.evaluate("""() => {
                const dialog = document.querySelector('div[role="dialog"]');
                if (!dialog) return [];
                const links = dialog.querySelectorAll('a[href^="/"][role="link"]');
                return Array.from(links).map(a => a.innerText.trim()).filter(t => t && !t.includes('\\n') && t !== "Verificado");
            }""")
            
            for u in nuevos:
                if u not in users: users.append(u)

            print(f"      - Obtenidos: {len(users)}/{limit}")
            if len(users) >= limit: break

            if len(users) == cantidad_anterior: intentos_sin_nuevos += 1
            else: intentos_sin_nuevos = 0

            # Scroll Físico (Simulando humano)
            enlaces = page.locator('div[role="dialog"] a[href^="/"][role="link"]')
            count = await enlaces.count()
            if count > 0:
                await enlaces.nth(count - 1).scroll_into_view_if_needed()
                await page.mouse.wheel(0, 1000)
            
            await asyncio.sleep(random.uniform(2.5, 4.0))

        await page.keyboard.press("Escape")
        await asyncio.sleep(2)
    except Exception as e:
        print(f"   [!] Error en lista {modal_url_part}: {e}")
    return users[:limit]

async def ejecutar_scraper_final():
    print("=" * 55)
    print(" 🕵️‍♂️ INSTAGRAM PROFILE SCRAPER — VERSIÓN FINAL")
    print("=" * 55)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False) # Para que veas el proceso
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        await context.add_cookies([{
            'name': 'sessionid', 'value': TU_SESSION, 'domain': '.instagram.com', 'path': '/'
        }])

        page = await context.new_page()
        
        try:
            print(f"[1] Cargando perfil @{TARGET_PROFILE}...")
            await page.goto(f"https://www.instagram.com/{TARGET_PROFILE}/", wait_until="networkidle")
            await asyncio.sleep(5)

            # --- EXTRACCIÓN DE CABECERA (STATS Y BIO) ---
            print("[2] Extrayendo Bio y Estadísticas...")
            data_header = await page.evaluate("""() => {
                const stats = Array.from(document.querySelectorAll('header ul li'))
                                   .map(li => li.innerText.replace(/\\n/g, ' ').trim())
                                   .filter(t => /\\d/.test(t));
                
                const section = document.querySelector('header section');
                let bio = "";
                if (section) {
                    const divs = Array.from(section.children);
                    bio = divs[divs.length - 1] ? divs[divs.length - 1].innerText : "";
                }
                
                const bioLimpia = bio.split('\\n').filter(l => 
                    !l.includes("Seguir") && !l.includes("Mensaje") && l.trim() !== ""
                ).join(' | ');

                return { stats, bioLimpia };
            }""")

            final_data = {
                "usuario": TARGET_PROFILE,
                "estadisticas": data_header["stats"],
                "descripcion_biografia": data_header["bioLimpia"],
                "seguidores": await extract_list_humano(page, "followers", 100),
                "seguidos": await extract_list_humano(page, "following", 100),
                "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            
            print("\n" + "=" * 55)
            print(f" ✅ ¡TODO LISTO! Datos guardados en {OUTPUT_JSON}")
            print("=" * 55)

        except Exception as e:
            print(f"\n[!] Error General: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(ejecutar_scraper_final())