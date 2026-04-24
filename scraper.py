
import asyncio
import json
import re
import random
from datetime import datetime
from playwright.async_api import async_playwright

TARGET_PROFILE = "amarantavp"          
OUTPUT_JSON = "amarantavp_limpio.json" 

TU_SESSION = "78502088557%3Ag9UdNvtwGssxUa%3A22%3AAYgtbCby0F38d4q61q_ffMDFzGy9d0KANIepash_HQ"

class InstagramQuimera:
    def __init__(self, session_id):
        self.session_id = session_id
        self.posts = []

    async def get_post_links(self, page, profile: str, limit: int = 10) -> list[str]:
        print(f"[→] Entrando en modo sigilo a @{profile}...")
        await page.goto(f"https://www.instagram.com/{profile}/", wait_until="networkidle")
        await asyncio.sleep(4)

        for _ in range(4):
            await page.keyboard.press("End")
            await asyncio.sleep(random.uniform(1.5, 2.5))

        links = await page.eval_on_selector_all(
            'a[href*="/p/"], a[href*="/reel/"]',
            "els => [...new Set(els.map(e => e.href))]"
        )

        post_links = [l for l in links if "/p/" in l or "/reel/" in l][:limit]
        print(f"[✓] {len(post_links)} posts interceptados")
        return post_links

    async def extract_caption_and_comments(self, page, target_author: str) -> tuple[str, list[dict]]:
        caption = "Sin descripción"
        comments = []

        try:
            await page.wait_for_selector("span._ap3a", timeout=8000)
        except Exception:
            return caption, comments

        await asyncio.sleep(2)

        # CAPTION: Usando la clase mágica de tu amigo
        try:
            cap_el = page.locator('span.x126k92a').first
            if await cap_el.count():
                caption = (await cap_el.inner_text()).strip()
        except Exception:
            pass

        try:
            results = await page.evaluate("""() => {
                const out = [];
                const allAp3a = document.querySelectorAll('span._ap3a');

                for (const ap3a of allAp3a) {
                    let container = ap3a;
                    let level = 0;

                    while (container.parentElement && level < 15) {
                        container = container.parentElement;
                        level++;
                        const spans = container.querySelectorAll('span[dir="auto"]');

                        if (level <= 10 && spans.length >= 4) {
                            const author = spans[1] ? spans[1].innerText.trim() : '';
                            const text   = spans[3] ? spans[3].innerText.trim() : '';
                            if (author && text) {
                                out.push({ author, text });
                            }
                            break;
                        }
                    }
                }

                const seen = new Set();
                return out.filter(c => {
                    const key = c.author + '|' + c.text;
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                });
            }""")

            skip = {"responder", "reply", "me gusta", "like", "ver traducción", "view translation", "ver respuestas", "view replies"}

            for item in results:
                if len(comments) >= 10: 
                    break
                    
                author = item.get("author", "").strip()
                text   = item.get("text", "").strip()
                
                if not author or not text: continue
                if text.lower() in skip: continue
                if re.match(r'^\d+\s*(sem|h|d|w|min|s)\b', text.lower()): continue
                if author.lower() == target_author.lower(): continue
                
                comments.append({"autor": author, "texto": text})

        except Exception as e:
            print(f"      ⚠️ Error al parsear comentarios: {e}")

        return caption, comments

    async def run(self, profile: str) -> list[dict]:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            
            await context.add_cookies([{
                'name': 'sessionid',
                'value': self.session_id,
                'domain': '.instagram.com',
                'path': '/',
            }])

            page = await context.new_page()

            try:
                post_links = await self.get_post_links(page, profile, limit=10)

                for i, url in enumerate(post_links, 1):
                    print(f"\n📸 Post {i}/10: {url}")
                    await page.goto(url, wait_until="networkidle")
                    

                    await page.mouse.wheel(0, 500)
                    await asyncio.sleep(random.uniform(3, 5))

                    caption, comments = await self.extract_caption_and_comments(page, profile)

                    post_data = {
                        "url": url,
                        "fecha_scraped": datetime.now().isoformat()[:10],
                        "descripcion": caption,
                        "comentarios": comments
                    }
                    
                    self.posts.append(post_data)
                    print(f"   ✓ Desc: {caption[:30]}... | Comentarios limpios: {len(comments)}")

            except Exception as e:
                print(f"[ERROR] {e}")
            finally:
                await browser.close()

        return self.posts

async def main():
    print("=" * 50)
    print(" 🕷️ Instagram Quimera Scraper - Iniciando")
    print("=" * 50)

    scraper = InstagramQuimera(TU_SESSION)
    posts = await scraper.run(TARGET_PROFILE)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)
        
    print("\n" + "=" * 50)
    print(f" ✅ ¡Batahola terminada! Archivo {OUTPUT_JSON} guardado.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())