# Patent Takip Otomasyonu

Bağlayıcı teknik şartname: [docs/patent-takip-otomasyon-plan.md](docs/patent-takip-otomasyon-plan.md) (v1.4).
Şartname bu dosyada değiştirilmez; aşağıdaki kararlar onaylanmış uygulama detaylarıdır.

## Çalıştırma

Gereksinimler: Python 3.11+ (burada `python3.12`), Node.js ve npm. Tüm komutlar proje kökünden verilmiştir.

### İlk kurulum

```bash
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
(cd frontend && npm install)
cp .env.example .env          # .env git'e girmez; değerleri ihtiyaca göre düzenleyin
```

### Veritabanı

```bash
(cd backend && alembic upgrade head)     # data/patent.db oluşur (WAL); hangi dizinden çalıştırılırsa çalıştırılsın aynı dosya
```

Şema değişiklikleri yalnızca Alembic migration ile yapılır (`create_all` kullanılmaz). `alembic.ini` içinde DB yolu yoktur.

### Geliştirme modu (iki terminal)

```bash
# Terminal 1 - backend (HOST/PORT .env'den okunur; varsayılan http://127.0.0.1:8001)
cd backend && python -m app.main
# alternatif: cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8001

# Terminal 2 - frontend (http://127.0.0.1:5173, /api -> 8001 proxy)
cd frontend && npm run dev
```

Arayüze http://127.0.0.1:5173/ adresinden girilir. Backend sağlık kontrolü: http://127.0.0.1:8001/api/health.

### Production modu (tek port)

```bash
(cd frontend && npm run build)           # frontend/dist üretir
cd backend && python -m app.main         # HOST/PORT .env'den okunur
# alternatif: cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8001
```

`python -m app.main`, `uvicorn.run` çağrısını `.env`/ortam değişkenlerindeki `HOST` ve `PORT` ile yapar (örn. `PORT=8011 python -m app.main`). `uvicorn` komutunu doğrudan kullanırsanız host/port `--host/--port` ile verilir. Komut `backend/` dizininden çalıştırılmalıdır.

Arayüz ve API aynı porttan gelir: http://127.0.0.1:8001/ ve http://127.0.0.1:8001/api/health. `frontend/dist` backend başlarken denetlenir; build sonradan alındıysa backend yeniden başlatılmalıdır.

### Excel aktarımı (tek seferlik, `scripts/excel_import.py`)

```bash
backend/.venv/bin/python scripts/excel_import.py            # DRY-RUN: DB'ye yazmaz, rapor verir (varsayılan)
(cd backend && alembic upgrade head)                        # --apply için DB hazır olmalı
backend/.venv/bin/python scripts/excel_import.py --apply    # tek transaction ile yazar
backend/.venv/bin/python scripts/excel_import.py --file yol.xlsx
```

Varsayılan kaynak `data/source/patent-takip.xlsx`. Dry-run gerçek DB'ye dokunmaz (DB varsa kopyası, yoksa Alembic ile hazırlanmış geçici DB kullanılır). Aynı dosya iki kez `--apply` edilse kayıt çoğalmaz (mükerrer: normalize başlık + başvuru sahibi + tarih).

### Testler

```bash
(cd backend && pytest)                   # backend: birim ve duman testleri
(cd frontend && npm run build)           # frontend: tip denetimi (tsc) + derleme
```

### .env değişkenleri

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `HOST` | `127.0.0.1` | Backend dinleme adresi (`python -m app.main`) |
| `PORT` | `8001` | Backend portu (`python -m app.main`) |
| `CORS_ORIGINS` | dev: `http://localhost:5173,http://127.0.0.1:5173` | Virgülle ayrılmış izinli origin listesi. Kod varsayılanı boş (kapalı/aynı origin); production'da boş bırakın |
| `FRAME_ANCESTORS` | `"'self'"` | `Content-Security-Policy: frame-ancestors` kaynakları (boşlukla ayrılmış). `;` ve satır sonu reddedilir. `X-Frame-Options` hiç gönderilmez |
| `ROOT_PATH` | boş | Reverse proxy alt yolu, örn. `/patent` (proxy öneki siler varsayımı) |
| `VITE_BASE_PATH` | boş | Frontend alt yolu, örn. `/patent/`; Vite tarafından okunur |

> **Uyarı:** `VITE_BASE_PATH` build zamanında `index.html` ve asset yollarına gömülür. Değeri değiştirirseniz `npm run build` yeniden alınmalıdır. `VITE_BASE_PATH` ve `ROOT_PATH`, proxy'nin dışarıya sunduğu alt yolla tutarlı olmalıdır.

### Bilinen sınırlamalar

- Kimlik doğrulama yoktur; uygulamaya erişen herkes tüm işlemleri yapabilir (şartname gereği).
- Router'ların durumu: Madde 7'deki 27 uç gerçektir (`patents` liste/yazma, `applicants`, `departments`, `fsmh_types`, `attorney_firms`, `settings`) ve `/api/health` çalışır; iskelet (501) uç kalmadı. Madde 6/2 silme engeli kısmen uygulandı: aktif patent bağlıysa silme engellenir; silinmiş patentler fiziksel temizlenir. Pasife alma yönlendirmesi ertelendi (bkz. Onaylanan Kararlar). Arayüzde Patent Listesi ve form çekmecesi (Adım 7B) ile Başvuru Sahipleri, Bölümler ve Vekil Firmalar sayfaları tamamdır; Excel dışa aktarma çalışır (Adım 9). Arayüz sapmaları için bkz. "Adım 9 sapmaları".
- 500 (işlenmeyen sunucu hatası) yanıtlarında `frame-ancestors` başlığı eklenmeyebilir (Starlette `ServerErrorMiddleware`).
- Proxy'nin öneki silmediği bir kurulumda `ROOT_PATH` yollarda çift önek oluşturur: `/patent/api/...` istekleri JSON yerine `index.html` (200), uzantılı dosyalar (`/patent/assets/...`) 404 döner. Bu durum entegrasyon aşamasında ele alınacaktır.
- `normalize_tr` (karşılaştırma/arama anahtarı, `core/text.py`) sınırları: (1) zaten küçük harfli ayrışık `i`+U+0307 girdisi `i`'ye eşitlenmez (`İ` ve `I`+U+0307 doğru işlenir); bilinçli sınırdır, Excel import (Aşama 13) öncesi yeniden değerlendirilecek. (2) Büyük `I` Türkçe kuralıyla `ı` olur: `Isparta` ≠ `isparta`; İngilizce yazılmış `FIRMA` ile `firma` eşleşmez. (3) `None` desteklenmez (`AttributeError`); çağıran boş/None değeri önceden ele almalıdır. (4) Aksan katlanmaz (`şaban` ≠ `saban`).
- Patent listesinde `q` araması Türkçe büyük/küçük harf duyarsızdır ama **aksan katlamaz**: `şaban` araması `saban` kaydını, `saban` araması `şaban` kaydını bulmaz; `I`→`ı` kuralı geçerlidir (`IŞIK` ↔ `ışık`). `q` Python tarafında (normalize edilerek) çalışır; liste filtre+sıralama sonrası bellekte sayfalanır (küçük ölçek varsayımı).
- Liste sıralamasında tarihi/bölümü/vekil firması boş kayıtlar `asc` ve `desc` yönünde de sona atılır; eşitlikte `id` artan.
- Testlerde Starlette `TestClient`, `httpx2` kurulmasını öneren bir kullanımdan-kaldırma uyarısı verir (zararsız).

## Onaylanan Kararlar

- Şartname `docs/` altına kopyalanır; proje içeriği doğrudan `PATENT/` köküne kurulur.
- Boş klasörlere `.gitkeep`; Python paketlerine (`app/`, `schemas/`, `routers/`, `services/`, `core/`) boş `__init__.py`.
- `routers/health.py` açılmaz; `GET /api/health` Aşama 8'de `main.py` içinde tanımlanır.
- Frontend ek dosyaları (`index.html`, `tsconfig*.json`, `postcss.config.js`, `App.tsx`, `index.css`, `components/AppShell.tsx`) Aşama 9'da eklenir.
- `created_at`/`updated_at` 5 tabloda bulunur (patents, applicants, departments, fsmh_types, attorney_firms).
- Silme kuralı (Adım 10, Madde 6/2'nin kısmi uygulaması; applicants, departments, fsmh_types, attorney_firms): kayda bağlı AKTİF patent varsa `409 "Bu kayıt N aktif patentte kullanılıyor, silinemez."`; bölüm silinirken varsayılan bölüm olarak kullanan başvuru sahipleri de engeldir (`"Bu bölüm N başvuru sahibinin varsayılan bölümü olarak kullanılıyor, silinemez."`, ikisi varsa mesajlar birleşir). Yalnızca SİLİNMİŞ patentler bağlıysa onlar ortaklarıyla (CASCADE) fiziksel silinir ve kayıt tek transaction'da silinir. Beklenmeyen FK hatası genel `409 "Bu kayıt başka kayıtlarca kullanıldığı için silinemez."` olarak kalır. Pasife alma yönlendirmesi ertelendi. Patent soft delete (`deleted_at`) aynen kalır.
- `normalize_tr`: `İ→i`, `I→ı`, casefold, Unicode NFC, iç boşluk tekilleştirme (tek yardımcı, `core/` içinde).
- Mükerrer uyarısı: `409` + `{"duplicate": true}`; `?confirm_duplicate=true` ile onaylanıp kaydedilir.
- Tailwind **v3.4.x**; sanal ortam `.venv`, **python3.12** ile oluşturulur.
- Reverse proxy: proxy'nin prefix'i sildiği varsayılır (`ROOT_PATH`). SPA fallback `/api` ve uzantılı yollar hariç `index.html`'e düşer.
- `VITE_BASE_PATH` build zamanında gömülür; değiştirilirse frontend yeniden build edilmelidir.
- `FRAME_ANCESTORS` doğrulanır (`;` ve satır sonu reddedilir). `CORS_ORIGINS` varsayılanı dev değerleridir; production'da boşaltılır.
- FSMH türü seed'i ilk migration'da yapılır; `settings` seed edilmez.
- Her aşamanın testi o aşamada yazılır.
- `backend/pytest.ini` şartname ağacında yoktur; çıplak `pytest` komutunun `app` paketini bulabilmesi için eklenmiş araç yapılandırmasıdır.
- `SessionLocal` varsayılan `autoflush=True` ile, `expire_on_commit=False` olarak kurulur (commit sonrası nesneler API yanıtında okunabilsin).
- `is_active`, `sort_order`, `created_at`, `updated_at` NOT NULL tanımlıdır (şartname NULL durumunu belirtmez).
- Veritabanından gelen naive `datetime` değerleri UTC kabul edilir (Aşama 7 şemalarında uygulanacak).
- `Patent` many-to-one ilişkileri (applicant, department, fsmh_type, attorney_firm) vardır; `Applicant.department` ilişkisi eklenmez.
- Migration revizyon kimliği `0001` elle verildi (`--rev-id 0001`).
- İleride SQLite batch migration yazılırken `foreign_keys=ON` risklidir; FK'lar migration süresince geçici kapatılmalıdır (Alembic batch dokümanı).
- Settings değerleri kırpılır; boş string geçerlidir.
- Kırpma sonrası çakışan Settings anahtarları 422 döner.
- `PatentListQuery` bilinmeyen query parametresini 422 ile reddeder.
- Patent ortaklarının sırası servis katmanında id'ye göre verilecektir.
- 500 yanıtlarında CSP başlığı Starlette `ServerErrorMiddleware` yüzünden eklenmeyebilir (bilinen sınırlama); entegrasyon aşamasında iframe testinde yeniden bakılacak.
- API yolları alt çizgilidir: `/api/fsmh_types`, `/api/attorney_firms`.
- `POST` başarı kodu 201, `DELETE` başarı kodu 204.
- `ROOT_PATH`, `FastAPI(root_path=...)` (deprecated) yerine `core/root_path.py` ASGI middleware ile uygulanır; en dışta çalışır, boşsa scope değiştirilmez.
- Vite dev server host `127.0.0.1` (Node 26 `localhost`'u yalnızca IPv6'da dinliyor) ve `strictPort: true`.
- UI fontları (Inter, Manrope) ve ikonlar (Material Symbols Outlined) Google Fonts'tan yüklenir; internetsiz çalışma şartı kullanıcı kararıyla kaldırıldı. Tailwind CDN kullanılmaz (derlenmiş Tailwind v3.4); yeni NPM bağımlılığı yoktur.
- Arayüz tasarımı `docs/stitch-tasarim.html` (Stitch çıktısı) esas alınarak yapıldı; tema `tailwind.config.js` içindedir. Patent formu ayrı sayfa değil sağdan açılan çekmecedir: `/patents/new` ve `/patents/:id` adresleri liste sayfasını ilgili modda açar.
- `NotFound` ve diğer bileşenler (`components/`, `pages/`, `lib/`) Madde 8 ağacında yoktur; `components/` ve `pages/` içeriği serbest olduğu için eklendi.
- `@types/react` ve `@types/react-dom` JSX derlemesi için eklendi.
- Production tek port: `frontend/dist`, FastAPI tarafından aynı porttan servis edilir (`core/spa.py`). `/assets` StaticFiles ile (`Cache-Control: public, max-age=31536000, immutable`), diğer bilinmeyen GET/HEAD yolları `index.html`'e düşer (`no-cache`). `/api` ve altı asla `index.html` dönmez; uzantılı veya gizli (`.`ile başlayan) yol yoksa 404.
- `dist` (ve `index.html`) yoksa uygulama çökmez: `/api` çalışır, kök yol "Frontend derlenmemiş" 404 JSON döner. `dist` varlığı uygulama başlarken denetlenir; frontend build edildikten sonra backend yeniden başlatılmalıdır.
- `ROOT_PATH` ve `VITE_BASE_PATH`, proxy'nin dışarıya sunduğu alt yolla tutarlı olmalıdır (örn. ikisi de `/patent`). Backend `index.html` içindeki asset yollarını yeniden yazmaz; bunlar build zamanındaki `VITE_BASE_PATH`'e bağlıdır. `VITE_BASE_PATH` değişirse frontend yeniden build edilmelidir.
- `RootPathMiddleware`, proxy prefix'i sildiği için `scope["path"]`/`raw_path`'e `ROOT_PATH` önekini geri ekler (ASGI'de `path` `root_path`'i içerir); Starlette yönlendirmede öneki çıkarır, uygulama yolları prefix'siz kalır. Aksi halde `Mount`/StaticFiles yanlış yol çözer.
- `python -m app.main` (`if __name__ == "__main__"` bloğu) `uvicorn.run`'ı `settings.HOST`/`settings.PORT` ile çağırır (Madde 11); import anında sunucu başlamaz.
- Excel aktarımı: `data/**/*.xlsx` `.gitignore`'dadır (gerçek veri commit'e girmez); `openpyxl==3.1.5` (+ `et_xmlfile==2.0.0`) `scripts/excel_import.py` ve dışa aktarma ucu (`services/patent_export.py`) içindir. Varsayılan kaynak `data/source/patent-takip.xlsx`; dry-run varsayılandır, `--apply` tek transaction'dır.
- Excel aktarımı kuralları: başlıklar ada göre eşlenir ("Ortaklar ve Oranları", "Notlar", "Bölüm", "Komisyon Onay Durumu" takma adları kabul); `No` ve şema dışı sütunlar (Kapsam, Komisyon Toplantı Tarihi/Onay Durumu, Mevcut Durum, Masraf) atlanır; Notlar aynen aktarılır; bölüm sütunundaki `"AYRILDI"` bölüm sayılmaz, bölüm BOŞ bırakılır ve raporda satır numaralarıyla listelenir; yeni başvuru sahibinin `department_id` değeri NULL kalır; tarihi boş veya çözülemeyen satır tarihsiz aktarılır ve raporlanır; boş satırlar tek satır "boş satır, atlandı" olarak raporlanır.
- `.` ile başlayan yol segmentleri statik servisten 404 döner (güvenlik).
- `/api` altında GET-only yollara HEAD/POST → 405 döner; bilinmeyen `/api` yolları 404 JSON'dur.
- `RootPathMiddleware`, proxy'nin ÖNEKİ SİLDİĞİ varsayımıyla scope path'ine öneki geri ekler; proxy öneki silmiyorsa yollar çift önek olur (`/patent/api/...` JSON yerine `index.html` 200, uzantılı dosyalar 404 döner), bu durumda entegrasyon aşamasında ayrıca ele alınır.

### Adım 9 sapmaları (kullanıcı kararıyla)

- **Ayarlar sayfası arayüzden çıkarıldı**; backend uçları (Madde 7: `GET/PUT /api/settings`) duruyor. Patent Listesi `default_page_size` okumaz, sayfa boyutu varsayılanı 25'tir.
- **Vekil Durumu özet kartı çıkarıldı** (Toplam Kayıt ve Türe Göre kaldı); filtre çubuğundaki Vekil Durumu seçimi durur.
- **Başvuru tarihi (bitiş) filtresi çıkarıldı**; "Başvuru tarihinden itibaren" kaldı. Backend `date_to` parametresi durur, arayüz göndermez.
- **E-posta, İletişim Bilgisi ve Durum (aktif/pasif) alanları arayüzden çıkarıldı** (Başvuru Sahipleri ve Vekil Firmalar). Backend alanları durur; düzenlemede mevcut değerleri değiştirilmeden geri gönderilir, yeni kayıtta e-posta / iletişim boş, `is_active` true olur.
- **Formdan hızlı kayıt ekleme:** patent çekmecesinde Başvuru Sahibi, Bölüm / Birim, FSMH Türü ve Vekil Firma alanlarının yanındaki "+" ile alan altında mini satırdan yeni kayıt eklenir (FSMH türü `sort_order` = mevcut en büyük + 1). Lookup listeleri tek ortak noktadan (`lib/lookups.tsx`) yüklenir ve yenilenir.
- **Başvuru sahibinin varsayılan bölümü:** patent çekmecesinde başvuru sahibi seçilince Bölüm / Birim boşsa kişinin varsayılan bölümü otomatik seçilir. Varsayılan bölümler Excel'e (`data/source/patent-takip.xlsx`) göre bir kerelik API ile atandı (11 kişi; "AYRILDI" olan boş bırakıldı); bu veri değişikliğidir, commit'e girmez.
- **Excel dışa aktarma — Madde 7 tablosuna ek uç:** `GET /api/patents/export` (liste ucuyla aynı filtre ve sıralama parametreleri, sayfalama yok, yalnızca aktif kayıtlar; `patent-takip-YYYY-MM-DD.xlsx`). Sütunlar Madde 3 sırasıyla; tarih gerçek tarih hücresi (GG.AA.YYYY); metin hücreleri string tipindedir, `=`, `+`, `-`, `@` ile başlayan değerler formül olarak çalışmaz. Kullanım: Patent Listesi'nde "Excel Dışa Aktar" düğmesi, aktif filtre ve sıralamayla indirir. `openpyxl` artık çalışma zamanında da kullanılır (zaten `requirements.txt`'te).
