# 🛰️ Afet Rota Sistemi 

> **Deprem sonrası afet bölgelerinde, uydu/drone görüntülerinden yapay zeka ile enkaz tespit ederek kurtarma ekipleri için güvenli rota hesaplayan web tabanlı komuta merkezi.**

---

## 🧠 Proje Nedir?

Türkiye gibi deprem riski yüksek ülkelerde, afet sonrası kurtarma ekiplerinin en büyük sorunlarından biri **enkaz dolu caddelerde güvenli yol bulmak** ve bunu hızlıca yapmaktır. Mevcut harita sistemleri gerçek zamanlı enkaz bilgisini taşımaz; kurtarma ekipleri çoğu zaman görsel değerlendirmeyle ilerlemek zorunda kalır.

Bu proje, **haritadaki anlık görüntüyü** yapay zeka ile analiz ederek enkazların konumunu tespit eder ve bu konumlardan kaçınan **en güvenli rotayı** otomatik olarak hesaplar. Kullanıcı sadece başlangıç ve hedef noktasını seçer; gerisi tamamen otomatik.

---

## 🚀 Özellikler

| # | Özellik | Açıklama |
|---|---------|----------|
| 🤖 | **AI Enkaz Tespiti** | Roboflow üzerinde eğitilmiş deprem hasar modeli ile ekran görüntüsünden otomatik enkaz algılama |
| 🎨 | **Görüntü Ön-İşleme** | CLAHE kontrast iyileştirme ve keskinleştirme filtresi — AI'a gitmeden önce görüntü kalitesini artırır |
| 🗺️ | **Akıllı Rota Hesaplama** | Enkaz koordinatlarını yol ağına işleyerek ağırlıklı en kısa yol algoritmasıyla güvenli güzergah bulur |
| ⚠️ | **Dinamik Tehlike Bölgesi** | Enkaz büyüklüğüne göre otomatik yarıçap hesabı — büyük enkaz = daha geniş kaçınma alanı |
| 🔄 | **Alternatif Rota** | Ana güvenli rota + karşılaştırmalı alternatif rota, ekiplere seçenek sunar |
| 🛰️ | **Gerçek Zamanlı Uydu Haritası** | Leaflet.js + Esri uydu görüntü katmanı ile yüksek çözünürlüklü zemin görünümü |
| ⚡ | **Önbelleğe Alınmış Harita** | Antakya yol ağı önceden indirilmiş ve repo'ya dahil — internet bağlantısı gerekmez |

---

## ⚙️ Sistem Nasıl Çalışır?

```
Kullanıcı A→B seçer
       │
       ▼
html2canvas haritanın ekran görüntüsünü yakalar
       │
       ▼
CLAHE + keskinleştirme (OpenCV) → görüntü iyileştirilir
       │
       ▼
Roboflow API → enkaz bounding box koordinatları
       │
       ▼
Pixel koordinatları → Gerçek lat/lng dönüşümü
       │
       ▼
Tehlike yarıçapları hesaplanır (enkaz büyüklüğüne göre)
       │
       ▼
OSMnx graf + NetworkX → ağırlıklı en kısa yol
       │
       ▼
Ana rota + Alternatif rota haritada çizilir
```

### 📸 Adım Adım Kullanım

1. **Haritada nokta seç** — `A` (başlangıç) ve `B` (hedef) noktalarını tıklayarak işaretle
2. **Bölgeye yakınlaş** — Enkaz tespiti için haritayı analiz edilecek alana odakla
3. **"Analiz Başlat"** butonuna tıkla
4. Sistem otomatik olarak:
   - 📷 Haritanın ekran görüntüsünü yakalar
   - 🤖 AI modeline gönderip enkazları tespit eder
   - 📍 Enkaz bölgelerini haritada kırmızı ile işaretler
   - 🔴 Tehlike yarıçaplarını hesaplar ve gösterir
   - 🟢 Enkazlardan kaçınan güvenli rotayı çizer
   - 🔵 Alternatif karşılaştırma rotasını gösterir

---

## 🏗️ Mimari

```
afet-rota-sistemi/
├── 📁 backend/
│   ├── app.py              # FastAPI sunucu — REST API + static dosya serve
│   ├── ai_engine.py        # AI enkaz tespit motoru (CLAHE + Roboflow)
│   ├── routing_engine.py   # Güvenli rota hesaplama (OSMnx + NetworkX)
│   └── config.py           # Merkezi konfigürasyon (.env yönetimi)
│
├── 📁 frontend/
│   ├── index.html          # Ana sayfa — harita arayüzü
│   ├── style2.css          # Premium dark theme
│   └── application.js      # Frontend controller (Leaflet + API calls)
│
├── 📁 cache/               # Görüntü ve rota önbelleği
│
├── antakya_graph.graphml   # 🗺️ Önceden indirilmiş Antakya yol ağı (14MB)
├── .env                    # API anahtarları (git'e dahil değil)
├── .env.example            # Örnek environment dosyası
├── requirements.txt        # Python bağımlılıkları
└── README.md
```

---

## 🔬 Teknik Detaylar

### AI Enkaz Tespiti — `ai_engine.py`

Görüntü doğrudan Roboflow'a gönderilmez. Önce **OpenCV ile ön-işleme** uygulanır:

- **CLAHE (Contrast Limited Adaptive Histogram Equalization)**: Uydu/drone görüntüleri düşük kontrastlı veya düzensız aydınlatmalı olabiliyor. CLAHE lokal kontrast iyileştirmesi yaparak enkaz sınırlarını belirginleştirir.
- **Keskinleştirme filtresi**: Detayları öne çıkarır, modelin doğruluğunu artırır.

Bu ön-işleme sonucunda Roboflow modeli daha yüksek güven skoru ile çalışır. Model çıktısı olarak enkaz bounding box koordinatları (pixel) ve güven skoru alınır.

### Rota Motoru — `routing_engine.py`

- **OSMnx** ile Antakya yol ağı yüklenir (`antakya_graph.graphml` önbelleğinden)
- AI'dan gelen pixel koordinatları gerçek lat/lng'ye dönüştürülür
- Her enkaz için büyüklüğe bağlı **dinamik tehlike yarıçapı** hesaplanır
- Tehlike bölgesindeki yol düğümlerine **yüksek maliyet ağırlığı** atanır
- **NetworkX** üzerinde ağırlıklı en kısa yol (Dijkstra/A*) çalıştırılır
- Ana rota + alternatif rota olmak üzere iki güzergah döndürülür

### Neden `antakya_graph.graphml` repo'da? 🤔

OSMnx her çalıştırmada OpenStreetMap'ten veri çeker — bu hem zaman alır hem de internet bağlantısı gerektirir. Harita verisini önceden indirip repo'ya dahil etmek:
- Demo/hackathon ortamında anında çalışmayı sağlar
- Ağ kesintilerinden bağımsız çalışma imkânı verir
- "Nokta bulunamadı" hatalarını ortadan kaldırır

---

## ⚡ Kurulum & Çalıştırma

### Gereksinimler

- Python 3.11+
- Roboflow API anahtarı ([roboflow.com](https://roboflow.com) üzerinden ücretsiz alınabilir)

### Hızlı Başlangıç

```bash
# 1. Repoyu klonla
git clone https://github.com/umitcancinar/afet-rota-sistemi
cd afet-rota-sistemi

# 2. Sanal ortam oluştur (önerilir)
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Environment dosyasını hazırla
cp .env.example .env
# .env dosyasını aç ve ROBOFLOW_API_KEY değerini gir

# 5. Sunucuyu başlat
python -m backend.app
```

Tarayıcıda `http://localhost:8000/static/index.html` adresine git.

> ⏳ **Not:** İlk açılışta `antakya_graph.graphml` (14MB) RAM'e yüklenirken **3-5 saniye** bekleme olabilir. Bu normaldir.

### Alternatif çalıştırma (uvicorn ile)

```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧰 Teknoloji Yığını

| Katman | Teknoloji | Amaç |
|--------|-----------|------|
| 🖥️ Backend | FastAPI, Python 3.11 | REST API sunucu |
| 🤖 AI Modeli | Roboflow (Earthquake Damage Detection) | Enkaz tespiti |
| 🎨 Görüntü İşleme | OpenCV, CLAHE | Görüntü ön-işleme |
| 🗺️ Harita & Rota | OSMnx, NetworkX | Graf tabanlı rota hesaplama |
| 🌍 Harita Kaynağı | OpenStreetMap | Yol ağı verisi |
| 🖼️ Frontend Harita | Leaflet.js + Esri | İnteraktif uydu haritası |
| 📸 Ekran Görüntüsü | html2canvas | Harita yakalama |

---

## 🌍 Kullanım Senaryoları

- 🚒 **Arama-kurtarma ekipleri** — Enkaz bölgelerini güvenle geçmek için güzergah planlaması
- 🚑 **Ambulans & acil lojistik** — Kritik konumlara en hızlı güvenli erişim rotası
- 🏛️ **AFAD / Kriz komuta merkezleri** — Bölge haritası üzerinde anlık durum analizi
- 🚛 **İnsani yardım konvoyu** — Yardım malzemelerinin güvenli dağıtım planlaması

---

## 📌 Bilinen Kısıtlamalar

- Mevcut harita verisi **Antakya bölgesi** için optimize edilmiştir
- Enkaz tespiti doğruluğu harita zoom seviyesine bağlıdır; **yakın zoom** daha iyi sonuç verir
- Roboflow API'ye internet bağlantısı gereklidir (rota hesaplama çevrimdışı çalışır)

---

## 🤝 Katkıda Bulunmak

Pull request'ler açıktır. Büyük değişiklikler için önce bir issue açın.

---
<br><br>
<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/b/b4/Flag_of_Turkey.svg" width="30" alt="Türkiye Cumhuriyeti" style="vertical-align: middle;">
  <b style="vertical-align: middle; margin-left: 8px;">Türkiye'nin afet yönetimi kapasitesini artırmak için geliştirilmiştir.</b>
</p>
