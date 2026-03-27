import cv2
import numpy as np
from ultralytics import YOLO
import os

# --- AYARLAR ---
# Senin yüklediğin o enkazlı fotoğrafın tam yolu (aynı klasörde varsayıyorum)
FOTO_YOLU = 'enkaz.webp' 
# İndirdiğimiz modelin tam yolu (yolov8m.pt adını böyle değiştirmiştik)
MODEL_YOLU = 'afet_modeli.pt'
# Yapay Zeka'nın "emin olma" seviyesi (Düşürerek her şeyi yakalamasını sağlayalım)
HASSASIYET = 0.05 

# --- ANA OPERASYON ---
def ana_görüntü_analizi():
    print("🧠 Yapay Zeka Beyni Yükleniyor...")
    if not os.path.exists(MODEL_YOLU):
        print(f"❌ HATA: '{MODEL_YOLU}' dosyası bulunamadı! Lütfen indirdiğin .pt dosyasını bu klasöre at ve adını değiştir.")
        return

    # 1. Modeli ve Fotoğrafı Oku
    model = YOLO(MODEL_YOLU)
    
    if not os.path.exists(FOTO_YOLU):
        print(f"❌ HATA: '{FOTO_YOLU}' fotoğrafı bulunamadı! Lütfen fotoğrafı bu klasöre at.")
        return
        
    img = cv2.imread(FOTO_YOLU)
    print(f"📸 Fotoğraf Okundu: {img.shape[1]}x{img.shape[0]} piksel.")

    # 2. YAPAY ZEKA TARAMASI VE ÖLÇÜMÜ (İstediğin Nokta Burası!)
    print(f"🕵️‍♂️ Görüntü taranıyor... (Hassasiyet: {HASSASIYET})")
    sonuclar = model(img, conf=HASSASIYET)
    
    # 3. Sonuçları İşle ve Ölç
    tespit_sayisi = 0
    analiz_img = img.copy() # Orijinal fotoğrafı bozmayalım

    for sonuc in sonuclar:
        for box in sonuc.boxes:
            tespit_sayisi += 1
            # Kutunun koordinatlarını al (piksel bazında)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Enkazı ölçen o kırmızı kutuyu fotoğrafın üzerine çiz
            cv2.rectangle(analiz_img, (x1, y1), (x2, y2), (0, 0, 255), 3) # Kalın kırmızı kutu
            
            # Üzerine kaçıncı enkaz olduğunu ve AI'nın güvenini yaz
            etiket = f"ENKAZ #{tespit_sayisi}"
            cv2.putText(analiz_img, etiket, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

    # 4. KANITLARI ORTAYA ÇIKAR
    print(f"🚨 KRİTİK ANALİZ TAMAMLANDI!")
    print(f"🏗️ Fotoğrafta Toplam ÖLÇÜLEN Enkaz Sayısı: {tespit_sayisi}")
    
    # Eğer enkaz bulduysa, analiz edilmiş fotoğrafı kaydet
    if tespit_sayisi > 0:
        cikti_yolu = 'analiz_sonucu.jpg'
        cv2.imwrite(cikti_yolu, analiz_img)
        print(f"✅ Analiz edilmiş, kırmızı kutulu fotoğraf '{cikti_yolu}' adıyla kaydedildi.")
        print("🔗 Lütfen bu klasörü aç ve o fotoğrafı incele. İstediğin ölçüm orada!")
    else:
        print("❌ Üzgünüm, Yapay Zeka bu hassasiyetle bir enkaz bulamadı.")
        print("🔗 Çözüm: Başka bir açıdan çekilmiş, daha net bir enkaz fotoğrafı dene.")

# Çalıştır
if __name__ == "__main__":
    ana_görüntü_analizi()
