import time
import random
import json
import pandas as pd
import concurrent.futures
from playwright.sync_api import sync_playwright

# --- CONFIGURACIÓN ---
SESSION_ID = "77936143036%3AY0cNxGMpaRB6b8%3A17%3AAYjD3tfacMkTj2rangfvySHzA7Imm8Lh7cwkzLIUvw" 

def get_instagram_context(playwright, session_id):
    browser = playwright.chromium.launch(headless=True) 
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
    context.add_cookies([{
        'name': 'sessionid',
        'value': session_id,
        'domain': '.instagram.com',
        'path': '/'
    }])
    return browser, context

def fetch_data_from_page(url, session_id):
    """ Función universal para pedir datos desde el contexto real del navegador """
    with sync_playwright() as p:
        browser, context = get_instagram_context(p, session_id)
        page = context.new_page()
        try:
            # Primero vamos al home para validar la sesión
            page.goto("https://www.instagram.com/", wait_until="networkidle")
            
            # Ahora pedimos los datos usando el fetch interno del navegador (evita el Error 400)
            data = page.evaluate(f'''async () => {{
                const response = await fetch('{url}', {{
                    headers: {{ 'x-ig-app-id': '936619743392459' }}
                }});
                return await response.json();
            }}''')
            return data
        except Exception as e:
            print(f"⚠️ Error en la petición: {e}")
            return None
        finally:
            browser.close()

def get_user_details_pw(username, session_id):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    res = fetch_data_from_page(url, session_id)
    if res and 'data' in res:
        user = res['data'].get('user')
        if user:
            return {
                'Usuario': user.get('username'),
                'ID': user.get('id'),
                'Seguidores': user.get('edge_followed_by', {}).get('count', 0),
                'Seguidos': user.get('edge_follow', {}).get('count', 0),
                'Privada': user.get('is_private', False)
            }
    return None

def get_followings_list_pw(target_username, session_id):
    target_info = get_user_details_pw(target_username, session_id)
    if not target_info: return []

    target_id = target_info['ID']
    total_estimado = target_info['Seguidos']
    all_usernames = []
    max_id = ""
    last_max_id = None # Seguro 1: Para ver si se repite
    
    print(f"🔎 Objetivo: {target_username} | Siguiendo (aprox): {total_estimado}")

    while True:
        url = f"https://www.instagram.com/api/v1/friendships/{target_id}/following/?count=50"
        if max_id: url += f"&max_id={max_id}"
        
        data = fetch_data_from_page(url, session_id)
        
        # Seguro 2: Si no hay data o no hay usuarios, fuera.
        if not data or 'users' not in data or len(data['users']) == 0:
            print("🏁 No hay más usuarios o Instagram cortó el flujo.")
            break
            
        for u in data['users']:
            uname = u.get('username')
            if uname not in all_usernames: # Evitamos duplicados en la lista
                all_usernames.append(uname)
            
        print(f"✅ Recuperados: {len(all_usernames)} únicos...")

        # Seguro 3: Si el max_id es el mismo que el anterior, estamos en un bucle
        new_max_id = data.get('next_max_id')
        if not new_max_id or new_max_id == last_max_id:
            print("🏁 Fin de la paginación alcanzado.")
            break
            
        # Seguro 4: Límite de seguridad (Si David sigue a 150, pero ya vamos 1000, algo está mal)
        if len(all_usernames) > (total_estimado + 100) and total_estimado > 0:
            print("⚠️ Límite de seguridad alcanzado (posible error de API).")
            break

        last_max_id = new_max_id
        max_id = new_max_id
        time.sleep(random.uniform(2, 4))
        
    return list(set(all_usernames)) # Retornamos solo únicos por si acaso

def main():
    target = input("👤 Usuario a scrapear (sin @): ").strip()
    
    print(f"--- [FASE 1] Iniciando obtención de lista ---")
    lista_seguidos = get_followings_list_pw(target, SESSION_ID)
    
    if not lista_seguidos:
        print("❌ Error: No se obtuvo lista. Terminando.")
        return

    print(f"--- [FASE 2] Lista obtenida: {len(lista_seguidos)} perfiles ---")
    print(f"--- [FASE 3] Iniciando extracción de detalles (UNO POR UNO para evitar crasheos) ---")
    
    datos_finales = []
    total = len(lista_seguidos)

    for i, user in enumerate(lista_seguidos, 1):
        try:
            print(f"🔍 [{i}/{total}] Analizando a: {user}...", end="\r")
            res = get_user_details_pw(user, SESSION_ID)
            if res:
                datos_finales.append(res)
            
            # Cada 10 perfiles, guardamos un "backup" temporal por si se muere
            if i % 10 == 0:
                print(f"\n💾 Guardando progreso temporal ({i} perfiles)...")
                pd.DataFrame(datos_finales).to_excel(f"BACKUP_{target}.xlsx", index=False)
                
        except Exception as e:
            print(f"\n⚠️ Error procesando a {user}: {e}")
            continue

    print(f"\n--- [FASE 4] Procesamiento terminado. Guardando archivo final ---")
    
    if datos_finales:
        try:
            df = pd.DataFrame(datos_finales)
            nombre_final = f"REPORTE_FINAL_{target}.xlsx"
            df.to_excel(nombre_final, index=False)
            print(f"🏆 ¡ÉXITO TOTAL! Revisa el archivo: {nombre_final}")
        except Exception as e:
            print(f"❌ Error fatal al guardar el Excel: {e}")
            print("Tranquilo, te dejo los datos aquí en consola por si acaso:")
            print(datos_finales)
    else:
        print("❌ No se recolectaron datos finales.")

if __name__ == "__main__":
    main()