# 📦 Lojistik Maliyet Hesaplama Sistemi

Trakya Üniversitesi Gümrük İşletme Bölümü için geliştirilmiş, web tabanlı lojistik maliyet hesaplama ve otomatik puanlama platformu.

Bu proje, 58 öğrencinin uluslararası lojistik maliyetlerini (gümrük vergisi, nakliye, ÖTV, KDV vb.) hesaplamalarını ve cevaplarını otomatik olarak puanlandırmalarını sağlayan interaktif bir platform sunar. Streamlit teknolojisi kullanarak masaüstü, tablet ve mobil cihazlardan erişilebilir.

## Proje Yapısı

```
lojistik-maliyet-hesaplama/
├── streamlit_app.py            # Ana Streamlit web uygulaması
├── requirements.txt            # Python bağımlılıkları
├── README.md                   # Bu dosya
├── .gitignore                  # Git ignore kuralları
└── data/
    └── database/
        └── logistics.db        # SQLite veritabanı
```

## 🚀 Çalıştırma

### Lokal (Geliştirme)

```bash
# Repository'i klonla
git clone https://github.com/USERNAME/lojistik-maliyet-hesaplama.git
cd lojistik-maliyet-hesaplama

# Sanal ortam oluştur
python -m venv .venv
.\.venv\Scripts\activate  # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Streamlit'i başlat
streamlit run streamlit_app.py
```

Ardından tarayıcınız otomatik açılacak: `http://localhost:8501`

### Production (Streamlit Cloud)

1. Repoyu GitHub'a push et
2. https://streamlit.io/cloud adresine git
3. Repository'i bağla
4. `streamlit_app.py` dosyasını belirt
5. Deploy et

Deployment: 2-3 dakika  
URL Format: `https://something.streamlit.app`