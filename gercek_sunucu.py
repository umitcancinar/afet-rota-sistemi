from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from inference_sdk import InferenceHTTPClient
import osmnx as ox
import networkx as nx
import cv2
import numpy as np
import os

# --- 🚀 TURBO AYARLAR ---
ox.settings.use_cache = True
ox.settings.log_console = False

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🧠 AI BEYNİ
CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key="n1d0mIipj5CVoIl2sCpi")
MODEL_ID = "earthquake-damage-detection-xmfgr/1"

# 🌍 TARSUS'U RAM'E YÜKLE
print("🌍 Tarsus Yol Ağı RAM'e yükleniyor, bekle moruk...")
try:
    G_TARSUS = ox.graph_from_place("Tarsus, Mersin, Turkey", network_type='drive')
    print("✅ Tarsus Hazır! Artık hata payı sıfır.")
except Exception as e:
    print(f"❌ Harita yüklenemedi: {e}")

@app.post("/api/otonom-analiz")
async def otonom_analiz(
    nw_lat: float = Form(...), nw_lon: float = Form(...),
    se_lat: float = Form(...), se_lon: float = Form(...),
    baslangic_lat: float = Form(...), baslangic_lon: float = Form(...),
    hedef_lat: float = Form(...), hedef_lon: float = Form(...),
    uydu_fotosu: UploadFile = File(...)
):
    print("\n--- 📥 ANALİZ BAŞLADI (Zırhlı Mod) ---")
    temp_path = "viewport_capture.png"
    try:
        content = await uydu_fotosu.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # 1. AI Analizi
        result = CLIENT.infer(temp_path, model_id=MODEL_ID)
        predictions = result.get('predictions', [])
        h, w = cv2.imread(temp_path).shape[:2]

        def piksel_to_gps(px, py):
            lat = nw_lat - (py / h) * (nw_lat - se_lat)
            lon = nw_lon + (px / w) * (se_lon - nw_lon)
            return (lat, lon)

        # 🎯 2. ANA HARİTA ÜZERİNDEN İŞLEM
        # Küçük kutuyla kesmek yerine ana haritayı kopyalıyoruz
        G_active = G_TARSUS.copy()

        # 3. SADECE EKRANDAKİ ENKAZLARI KAPAT
        bulunan_enkazlar = []
        for p in predictions:
            e_lat, e_lon = piksel_to_gps(p['x'], p['y'])
            bulunan_enkazlar.append([e_lat, e_lon])
            try:
                # Enkazın en yakınındaki yolu bul ve devasa haritadan o anlık sil
                node = ox.distance.nearest_nodes(G_active, X=e_lon, Y=e_lat)
                if node in G_active:
                    G_active.remove_node(node)
            except: continue

        # 🚙 4. ROTA HESAPLA (Mıknatıs Modu Aktif)
        # Artık "Source not in G" hatası alamazsın çünkü her iki nokta da G_active içinde!
        start_node = ox.distance.nearest_nodes(G_active, X=baslangic_lon, Y=baslangic_lat)
        end_node = ox.distance.nearest_nodes(G_active, X=hedef_lon, Y=hedef_lat)
        
        path = nx.shortest_path(G_active, start_node, end_node, weight='length')
        
        route_coords = [[G_active.nodes[n]['y'], G_active.nodes[n]['x']] for n in path]
        print(f"✅ Rota Başarıyla Oluşturuldu: {len(route_coords)} nokta.")

        return {
            "durum": "basarili",
            "tespit_sayisi": len(bulunan_enkazlar),
            "enkazlar": bulunan_enkazlar,
            "guvenli_rota": route_coords
        }

    except Exception as e:
        print(f"❌ HATA: {e}")
        return {"durum": "hata", "mesaj": "Rota bulunamadı! Belki enkazlar tüm yolları kapatmıştır."}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)