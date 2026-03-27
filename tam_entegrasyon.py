import osmnx as ox
import networkx as nx

# Önbelleği açalım ki harita hızlı yüklensin
ox.settings.use_cache = True

def pikselden_gpse(px_x, px_y, img_genislik, img_yukseklik, sol_ust_gps, sag_alt_gps):
    """
    Yapay zekanın bulduğu piksel koordinatını, gerçek Dünya GPS koordinatına çevirir (Afin Dönüşümü).
    """
    lat_farki = sol_ust_gps[0] - sag_alt_gps[0]
    lon_farki = sag_alt_gps[1] - sol_ust_gps[1]

    hedef_lat = sol_ust_gps[0] - (px_y / img_yukseklik) * lat_farki
    hedef_lon = sol_ust_gps[1] + (px_x / img_genislik) * lon_farki

    return (hedef_lat, hedef_lon)

def sistemi_calistir():
    print("🌍 Tarsus haritası hafızaya alınıyor...")
    G = ox.graph_from_place("Tarsus, Mersin, Turkey", network_type='drive')
    
    # --- 1. SİMÜLASYON: Uydu Görüntüsü Verileri ---
    # Varsayalım ki dronumuz/uydumuz tam olarak bu GPS koordinatları arasının fotoğrafını çekti:
    foto_sol_ust = (36.9250, 34.8800) # Enlem, Boylam
    foto_sag_alt = (36.9150, 34.8950)
    foto_genislik = 1920 # Piksel
    foto_yukseklik = 1080 # Piksel

    # --- 2. SİMÜLASYON: Yapay Zeka Çıktısı ---
    # Yapay zeka kodu çalıştı ve fotoğrafın şu piksellerinde bir enkaz bulduğunu söyledi:
    enkaz_piksel_x = 960  # Fotoğrafın tam ortası
    enkaz_piksel_y = 540

    # --- 3. BÜYÜK BİRLEŞME: Pikseli GPS'e Çevir ---
    enkaz_gps = pikselden_gpse(
        enkaz_piksel_x, enkaz_piksel_y, 
        foto_genislik, foto_yukseklik, 
        foto_sol_ust, foto_sag_alt
    )
    print(f"🚨 YAPAY ZEKA TESPİTİ: Enkazın gerçek GPS koordinatı hesaplandı: {enkaz_gps}")

    # --- 4. ROTA MOTORU: Enkazı Haritaya İşle ve Rota Çiz ---
    # Tarsus grafından rastgele iki başlangıç ve bitiş noktası seçelim
    dugumler = list(G.nodes())
    baslangic = dugumler[500]
    hedef = dugumler[3000]

    # Enkaza en yakın harita düğümünü (kavşağı) bul ve o kavşağı sil (Geçişi kapat)
    enkaz_node = ox.distance.nearest_nodes(G, X=enkaz_gps[1], Y=enkaz_gps[0])
    G_enkazli = G.copy()
    
    try:
        G_enkazli.remove_node(enkaz_node)
        print("🚧 Enkaz bölgesi haritadan silindi, yol ulaşıma kapatıldı.")
    except:
        pass # Eğer düğüm zaten yoksa hata vermesin

    try:
        # Yeni Güvenli Rotayı Hesapla
        print("🗺️ Alternatif güvenli rota hesaplanıyor...")
        guvenli_rota = nx.shortest_path(G_enkazli, source=baslangic, target=hedef, weight='length')
        
        # Haritayı Çizdir
        print("✅ Sistem başarıyla çalıştı! Harita ekrana yansıtılıyor...")
        fig, ax = ox.plot_graph_routes(
            G, 
            routes=[guvenli_rota], 
            route_colors=['cyan'], 
            route_linewidths=[4], 
            node_size=0, 
            bgcolor='#111111',
            show=True
        )
    except nx.NetworkXNoPath:
         print("❌ HATA: Hedefe giden tüm alternatif yollar kapalı!")

if __name__ == "__main__":
    sistemi_calistir()
