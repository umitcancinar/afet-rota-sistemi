from ultralytics import YOLO
import cv2

def profesyonel_enkaz_analizi(fotograf_yolu, model_yolu='afet_modeli.pt'):
    print(f"🧠 Profesyonel Afet Modeli ({model_yolu}) yükleniyor...")
    
    try:
        # Kendi indirdiğimiz veya eğittiğimiz afet modelini yüklüyoruz
        # (Eğer afet_modeli.pt yoksa, test için geçici olarak 'yolov8n.pt' yazabilirsin)
        model = YOLO(model_yolu) 
    except Exception as e:
        print(f"❌ Model yüklenemedi! Dosya adını ve yolunu kontrol et. Hata: {e}")
        return []

    print(f"👁️ '{fotograf_yolu}' analiz ediliyor...")
    
    # Güven skoru (confidence) %60 ve üzeri olanları alıyoruz (0.6)
    # Bu sayede sistem her gördüğü ufak tefek çöpü enkaz sanmaz.
    sonuclar = model(fotograf_yolu, conf=0.6)
    
    tespit_edilen_enkazlar = []
    
    # Yapay zekanın bulduğu her bir sonucu işliyoruz
    for sonuc in sonuclar:
        kutular = sonuc.boxes
        
        for kutu in kutular:
            # Kutunun köşe koordinatları (x_min, y_min, x_max, y_max)
            x1, y1, x2, y2 = kutu.xyxy[0].tolist() 
            
            # Modelin bu tespitin "Enkaz" olduğundan yüzde kaç emin olduğu
            guven_skoru = float(kutu.conf[0])
            
            # Tespit edilen sınıfın (class) adı (örn: 'destroyed_building')
            sinif_id = int(kutu.cls[0])
            sinif_adi = model.names[sinif_id]

            enkaz_verisi = {
                "sinif": sinif_adi,
                "dogruluk_orani": round(guven_skoru * 100, 2),
                "piksel_koordinatlari": {
                    "sol_ust": (int(x1), int(y1)),
                    "sag_alt": (int(x2), int(y2))
                }
            }
            tespit_edilen_enkazlar.append(enkaz_verisi)
            
        # Analiz edilmiş fotoğrafı ekranda göster (Opsiyonel)
        sonuc.show()

    # Raporlama
    print("\n" + "="*40)
    print(f"🚨 TOPLAM {len(tespit_edilen_enkazlar)} ADET KRİTİK ENKAZ TESPİT EDİLDİ!")
    print("="*40)
    
    for i, enkaz in enumerate(tespit_edilen_enkazlar, 1):
        print(f"{i}. Nesne: {enkaz['sinif']} | Güvenilirlik: %{enkaz['dogruluk_orani']}")
        print(f"   Konum (Piksel): {enkaz['piksel_koordinatlari']}")
        print("-" * 30)
        
    return tespit_edilen_enkazlar

if __name__ == "__main__":
    # Test için çalıştırıyoruz
    # Gerçek modelini indirene kadar kod patlamasın diye 'yolov8n.pt' kullanabilirsin
    # Modelini indirdiğinde burayı 'afet_modeli.pt' yap.
    enkaz_listesi = profesyonel_enkaz_analizi('enkaz.webp', model_yolu='yolov8n.pt')