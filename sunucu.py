from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import osmnx as ox
import networkx as nx

# Web sunucumuzu başlatıyoruz
app = FastAPI(title="Afet Rota API")

# Web sitesinin bu sunucuya bağlanabilmesi için CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🌍 Tarsus haritası RAM'e yükleniyor, lütfen bekleyin...")
ox.settings.use_cache = True
G = ox.graph_from_place("Tarsus, Mersin, Turkey", network_type='drive')
print("✅ Harita sunucuya yüklendi! API istek almaya hazır.")

@app.get("/api/guvenli-rota")
def guvenli_rota_hesapla():
    # 1. Başlangıç ve Bitiş (Örnek: 500. ve 3000. kavşaklar)
    dugumler = list(G.nodes())
    baslangic = dugumler[500]
    hedef = dugumler[3000]

    # 2. Yapay Zekanın bulduğu Enkaz (Simülasyon Koordinatı)
    enkaz_gps = (36.9200, 34.8875)
    enkaz_node = ox.distance.nearest_nodes(G, X=enkaz_gps[1], Y=enkaz_gps[0])
    
    # 3. Yolu Kapat ve Yeni Rota Çiz
    G_enkazli = G.copy()
    try:
        G_enkazli.remove_node(enkaz_node)
    except:
        pass

    try:
        rota_nodelari = nx.shortest_path(G_enkazli, source=baslangic, target=hedef, weight='length')
        
        # 4. Bulunan rotadaki her bir noktanın Enlem/Boylam'ını bir listeye çevir (Web için şart)
        rota_koordinatlari = []
        for node in rota_nodelari:
            lat = G.nodes[node]['y']
            lon = G.nodes[node]['x']
            rota_koordinatlari.append([lat, lon]) # Leaflet.js [Enlem, Boylam] ister
            
        return {
            "durum": "basarili",
            "enkaz_koordinati": [enkaz_gps[0], enkaz_gps[1]],
            "rota": rota_koordinatlari
        }
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
