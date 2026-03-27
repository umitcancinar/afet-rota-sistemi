import requests
import cv2
import numpy as np

# --- AYARLAR ---
API_KEY = "BURAYA_API_KEYINI_YAPISTIR" 
MODEL_ID = "earthquake-damage-detection-xmfgr/1" 
FOTO_YOLU = "enkaz.webp" # Klasöründeki fotoğrafın adı

def uzman_gozuyle_tarama():
    print("🛰️ Uydu görüntüsü uzman sisteme gönderiliyor...")
    
    # 1. Fotoğrafı oku
    with open(FOTO_YOLU, "rb") as f:
        image_data = f.read()

    # 2. Uzman Modele Danış (API Çağrısı)
    url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={API_KEY}"
    
    response = requests.post(url, data=image_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if response.status_code != 200:
        print("❌ HATA: API Bağlantısı kurulamadı. Anahtarını kontrol et!")
        return

    predictions = response.json().get('predictions', [])
    
    # 3. ÖLÇÜM VE KANIT
    print(f"🚨 ANALİZ TAMAMLANDI!")
    print(f"🏗️ Uzman AI, fotoğrafta tam {len(predictions)} adet enkaz noktası ÖLÇTÜ!")

    # Fotoğrafın üzerine ölçülen enkazları işaretleyelim
    img = cv2.imread(FOTO_YOLU)
    for p in predictions:
        x, y, w, h = int(p['x']), int(p['y']), int(p['width']), int(p['height'])
        x1, y1 = int(x - w/2), int(y - h/2)
        x2, y2 = int(x + w/2), int(y + h/2)
        
        # Enkazı ölçen o kırmızı kutuyu çiz
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
        print(f"📍 Enkaz saptandı: Piksel ({x}, {y})")

    cv2.imwrite("uzman_kanit.jpg", img)
    print("✅ Kanıt 'uzman_kanit.jpg' olarak kaydedildi. Açıp bakabilirsin!")

if __name__ == "__main__":
    uzman_gozuyle_tarama()