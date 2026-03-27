import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

def afet_rotasi_ciz():
    bolge = "Tarsus, Mersin, Turkey"
    print(f"[{bolge}] haritası yükleniyor...")
    
    # Sadece ana haritayı (arabalar için) indir
    G = ox.graph_from_place(bolge, network_type='drive')
    
    # Haritadaki tüm kavşakları bir listeye alalım
    dugumler = list(G.nodes())
    
    # Rastgele değil, birbirine uzak iki nokta seçelim ki rota belli olsun
    # (Tarsus grafında 100. ve 5000. düğümleri örnek alıyoruz)
    baslangic = dugumler[100]
    hedef = dugumler[5000]
    
    print(f"Arama Kurtarma Ekibi Çıkış Noktası: {baslangic}")
    print(f"Hedef Enkaz Bölgesi: {hedef}")

    try:
        # 1. ADIM: Normal, engelsiz rotayı hesapla
        normal_rota = nx.shortest_path(G, source=baslangic, target=hedef, weight='length')
        print("✅ Standart rota hesaplandı.")

        # 2. ADIM: Enkaz Simülasyonu
        # Rotanın tam ortasındaki sokağa enkaz düştüğünü varsayalım
        orta_nokta_indeksi = len(normal_rota) // 2
        enkaz_noktasi = normal_rota[orta_nokta_indeksi]
        
        print(f"⚠️ DİKKAT: Uydu görüntüsü {enkaz_noktasi} koordinatında yıkım tespit etti! Yol kapandı.")

        # O noktayı haritadan siliyoruz (Geçişi imkansız kılıyoruz)
        G_enkazli = G.copy()
        G_enkazli.remove_node(enkaz_noktasi)

        # 3. ADIM: Yeni Güvenli Rotayı Hesapla
        guvenli_rota = nx.shortest_path(G_enkazli, source=baslangic, target=hedef, weight='length')
        print("✅ Alternatif güvenli rota başarıyla oluşturuldu!")

        # 4. ADIM: Ekranda Göster
        print("\nHarita çizdiriliyor... Kırmızı: Eski/Kapalı Yol | Camgöbeği (Mavi): Yeni Güvenli Rota")
        
        # İki rotayı aynı haritada farklı renklerle çizdiriyoruz
        fig, ax = ox.plot_graph_routes(
            G,
            routes=[normal_rota, guvenli_rota],
            route_colors=['red', 'cyan'], # Kırmızı eski yol, Mavi yeni yol
            route_linewidths=[4, 4],
            node_size=0,
            bgcolor='#111111',
            show=True
        )

    except nx.NetworkXNoPath:
        print("❌ HATA: Hedefe giden tüm yollar kapalı, ulaşılamıyor!")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

if __name__ == "__main__":
    afet_rotasi_ciz()