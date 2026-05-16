# DiscounTracking

Türkiye'nin önde gelen e-ticaret ve moda sitelerindeki ürün fiyatlarını takip eden, fiyat düştüğünde Telegram üzerinden bildirim gönderen web uygulaması.

## Özellikler

- **16 site desteği** — Trendyol, Amazon, Hepsiburada, N11, Beymen, Boyner, Superstep, Fashfed, Sneaksup, Vakkorama, Occasion, MediaMarkt, Atasun Optik, Zara, H&M, Mango
- **Otomatik fiyat kontrolü** — Ayarlanabilir aralıklarla (varsayılan: saatte bir) fiyatlar kontrol edilir
- **Telegram bildirimi** — Fiyat düştüğünde veya hedef fiyata ulaşıldığında anlık mesaj gelir; birden fazla telefon desteklenir
- **Fiyat geçmişi** — Her ürün için fiyat değişimi grafikle gösterilir
- **Hedef fiyat** — Belirlediğiniz fiyatın altına düşünce bildirim alırsınız
- **macOS arka plan servisi** — Terminal kapalı olsa bile çalışmaya devam eder (~80 MB RAM)

### Gereksinimler

- Python 3.10+
- Telegram botu ([BotFather](https://t.me/BotFather) üzerinden oluşturulur)

## Kullanım

1. **Ürün ekle** — `+ Ürün Ekle` butonuna tıklayın, ürün URL'sini yapıştırın
2. **Hedef fiyat belirleyin** — İstediğiniz fiyatı girin; bu fiyatın altına düşünce Telegram'a bildirim gelir
3. **Fiyat geçmişini takip edin** — Ürün sayfasında fiyat değişimini grafikle görün
4. **Manuel kontrol** — "Şimdi Kontrol Et" butonu ile anlık fiyat güncellemesi yapın

## Desteklenen Siteler

| Site | Domain |
|------|--------|
| Trendyol | trendyol.com |
| Amazon | amazon.com.tr / amazon.de / amazon.co.uk |
| Hepsiburada | hepsiburada.com |
| N11 | n11.com |
| Beymen | beymen.com |
| Boyner | boyner.com.tr |
| Superstep | superstep.com.tr |
| Fashfed | fashfed.com |
| Sneaksup | sneaksup.com |
| Vakkorama | vakkorama.com |
| Occasion | occasion.com.tr |
| MediaMarkt | mediamarkt.com.tr |
| Atasun Optik | atasunoptik.com.tr |
| Zara | zara.com |
| H&M | hm.com |
| Mango | mango.com |

## Proje Yapısı

```
DiscounTracking/
├── app.py              # Flask uygulaması ve route'lar
├── models.py           # Veritabanı modelleri (SQLAlchemy)
├── scheduler.py        # Otomatik fiyat kontrolü (APScheduler)
├── notifier.py         # Telegram bildirimleri
├── config.py           # Ortam değişkenleri
├── setup_service.py    # macOS launchd servis yöneticisi
├── scrapers/
│   ├── base.py         # Temel scraper sınıfı
│   ├── trendyol.py
│   ├── amazon.py
│   └── ...             # Her site için ayrı modül
├── templates/          # HTML şablonları (Jinja2)
├── static/             # CSS
├── requirements.txt
└── .env.example
```

## Teknolojiler

- **Backend:** Python, Flask, SQLAlchemy, SQLite
- **Scraping:** requests, cloudscraper, BeautifulSoup4
- **Zamanlayıcı:** APScheduler
- **Bildirim:** Telegram Bot API
- **Frontend:** Vanilla HTML/CSS, Chart.js

## Lisans

MIT
