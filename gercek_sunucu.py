from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import osmnx as ox
import networkx as nx
import cv2
import os

app = FastAPI(title="Afet Yönetimi Otonom Yapay Zeka Sunucusu")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🌍 Harita Verisi RAM'e yükleniyor...")
ox.settings.use_cache = True
G = ox.graph_from_place("Tarsus, Mersin, Turkey", network_type='drive')

print("🧠 Yapay Zeka (Gözler) Yükleniyor...")
# Profesyonel afet modelini arar. Yoksa standart modele (düşük güven ile) geçer.
if os.path.exists('afet_modeli.pt'):
    ai_model = YOLO('afet_modeli.pt')
    ai_conf = 0.5 # Profesyonel model için normal güven
    print("✅ PROFESYONEL AFET MODELİ AKTİF!")
else:
    ai_model = YOLO('yolov8n.pt')
    ai_conf = 0.05 # Standart modelle test yapabilmen için hileli (çok düşük) güven
    print("⚠️ UYARI: 'afet_modeli.pt' bulunamadı! Test için Nano model devrede.")

# --- Piksel / GPS Dönüşüm Motoru ---
def pikselden_gpse(px_x, px_y, img_w, img_h, sol_ust, sag_alt):
    lat_farki = sol_ust[0] - sag_alt[0]
    lon_farki = sag_alt[1] - sol_ust[1]
    hedef_lat = sol_ust[0] - (px_y / img_h) * lat_farki
    hedef_lon = sol_ust[1] + (px_x / img_w) * lon_farki
    return (hedef_lat, hedef_lon)

@app.post("/api/gercek-analiz")
async def gercek_zamanli_analiz(
    baslangic_lat: float = Form(...),
    baslangic_lon: float = Form(...),
    hedef_lat: float = Form(...),
    hedef_lon: float = Form(...),
    uydu_fotosu: UploadFile = File(...)
):
    foto_yolu = f"temp_{uydu_fotosu.filename}"
    try:
        # 1. Fotoğrafı Sunucuya Al
        with open(foto_yolu, "wb") as buffer:
            buffer.write(await uydu_fotosu.read())

        # 2. Yapay Zeka Taraması
        sonuclar = ai_model(foto_yolu, conf=ai_conf)
        
        img = cv2.imread(foto_yolu)
        img_h, img_w = img.shape[:2]

        # Tarsus için referans koordinat çerçevesi (Gerçekte GeoTIFF'ten okunur)
        foto_sol_ust_gps = (36.9350, 34.8700) 
        foto_sag_alt_gps = (36.9050, 34.9050)

        bulunan_enkaz_koordinatlari = []
        G_dinamik = G.copy() 

        # 3. Yıkılan Yolları Tespit Et ve Haritadan Sil
        for sonuc in sonuclar:
            for kutu in sonuc.boxes:
                x1, y1, x2, y2 = kutu.xyxy[0].tolist()
                merkez_x = (x1 + x2) / 2
                merkez_y = (y1 + y2) / 2

                enkaz_gps = pikselden_gpse(merkez_x, merkez_y, img_w, img_h, foto_sol_ust_gps, foto_sag_alt_gps)
                bulunan_enkaz_koordinatlari.append([enkaz_gps[0], enkaz_gps[1]])

                enkaz_node = ox.distance.nearest_nodes(G_dinamik, X=enkaz_gps[1], Y=enkaz_gps[0])
                try:
                    G_dinamik.remove_node(enkaz_node)
                except:
                    pass

        # 4. Arama Kurtarma İçin Güvenli Rotayı Çiz
        baslangic_node = ox.distance.nearest_nodes(G, X=baslangic_lon, Y=baslangic_lat)
        hedef_node = ox.distance.nearest_nodes(G, X=hedef_lon, Y=hedef_lat)

        rota_nodelari = nx.shortest_path(G_dinamik, source=baslangic_node, target=hedef_node, weight='length')
        rota_koordinatlari = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in rota_nodelari]

        return {
            "durum": "basarili",
            "tespit_edilen_enkaz_sayisi": len(bulunan_enkaz_koordinatlari),
            "enkazlar": bulunan_enkaz_koordinatlari,
            "guvenli_rota": rota_koordinatlari
        }

    except nx.NetworkXNoPath:
        return {"durum": "hata", "mesaj": "KRİTİK DURUM: Hedefe giden tüm yollar kapalı!"}
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
    finally:
        if os.path.exists(foto_yolu):
            os.remove(foto_yolu)