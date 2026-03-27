import requests
import cv2
import json

# --- AYARLAR ---
API_KEY = "YOUR_API_KEY"  # Roboflow profilinden aldığın API anahtarı
MODEL_ID = "earthquake-damage-detection-xmfgr/1" # Senin bulduğun o uzman model
FOTO_YOLU = "enkaz.webp"

def uzman_analiz_yap():
    print("🛰️ Uydu görüntüsü uzman modele gönderiliyor...")
    
    # 1. Fotoğrafı oku ve API'ye gönderilecek hale getir
    with open(FOTO_YOLU, "rb") as f:
        image_data = f.read()

    # 2. Roboflow API İsteği
    url = f"https://outline.roboflow.com/{MODEL_ID}?api_key={API_KEY}"
    
    response = requests.post(url, data=image_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if response.status_code != 200:
        print("❌ HATA: API bağlantısı kurulamadı. Anahtarını kontrol et!")
        return

    predictions = response.json().get('predictions', [])
    
    # 3. ÖLÇÜM VE KANIT (İstediğin yer burası!)
    print(f"🚨 ANALİZ TAMAMLANDI!")
    print(f"🏗️ Uzman AI, fotoğrafta tam {len(predictions)} adet enkaz noktası ÖLÇTÜ!")

    # Görsel üzerinde işaretleme yapalım
    img = cv2.imread(FOTO_YOLU)
    for p in predictions:
        x, y, w, h = int(p['x']), int(p['y']), int(p['width']), int(p['height'])
        # Koordinatları kutuya çevir
        x1, y1 = int(x - w/2), int(y - h/2)
        x2, y2 = int(x + w/2), int(y + h/2)
        
        # Kırmızı kutuyu çiz (Ölçümün kanıtı)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
        print(f"📍 Enkaz saptandı: Piksel Koordinatı ({x}, {y})")

    cv2.imwrite("uzman_kanit.jpg", img)
    print("✅ Ölçüm kanıtı 'uzman_kanit.jpg' olarak kaydedildi.")

if __name__ == "__main__":
    uzman_analiz_yap()