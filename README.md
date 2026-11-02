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

> **Veri repoda yoktur:** `data/` içeriği (veritabanı, Excel, yedekler) git'e girmez. Mevcut Excel listenizi aktarmak için dosyayı `data/source/patent-takip.xlsx` olarak koyup aşağıdaki "Excel aktarımı" adımlarını izleyin; Excel yoksa boş veritabanı ile başlanır.

### Veritabanı

```bash
(cd backend && alembic upgrade head)     # data/patent.db oluşur (WAL); hangi dizinden çalıştırılırsa çalıştırılsın aynı dosya
```

Şema değişiklikleri yalnızca Alembic migration ile yapılır (`0001` ilk şema, `0002` durum/tescil tarihi/vekil firma alanları/Telif Hakkı). `0002` downgrade'i SQLite `DROP COLUMN` kullanır (tablo yeniden oluşturulmaz, bu yüzden `foreign_keys` kapatmaya gerek kalmaz; ileride batch/yeniden oluşturma gerektiren bir migration için o not geçerlidir) ve "Telif Hakkı" türünü yalnızca hiçbir patente bağlı değilse siler (`create_all` kullanılmaz). `alembic.ini` içinde DB yolu yoktur.

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

### Excel dışa aktarma

Patent Listesi'nde **Excel Dışa Aktar** düğmesi, ekrandaki filtre ve sıralamayla (sayfalamasız, yalnızca aktif kayıtlar) `patent-takip-YYYY-MM-DD.xlsx` indirir; sütunlar Şartname Madde 3 sırasıdır. Doğrudan: `GET /api/patents/export?q=...&sort_by=...` (liste ucuyla aynı parametreler). Metin hücreleri formül olarak çalışmaz.

### Yedekleme

Uygulama KAPALIYKEN `data/patent.db` dosyasını kopyalayın (WAL kullanıldığından `-wal`/`-shm` dosyaları varsa onlarla birlikte) ya da çalışırken güvenli yol olarak:

```bash
sqlite3 data/patent.db ".backup 'data/source/patent-yedek-YYYYMMDD.db'"
```

`data/**/*.db*` ve `data/**/*.xlsx` git'e girmez; yedekler yalnızca yerelde tutulur.

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
- Madde 7'deki 27 uç ve `/api/health` gerçektir; ek olarak `GET /api/patents/export`, `GET /api/partners`, `GET /api/departments/summary` ve `GET /api/attorney_firms/summary` ve `GET /api/applicants/summary` vardır. `/api/settings` uçları backend'de durur ama arayüzde Ayarlar sayfası yoktur.
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

## Şartnameden onaylanan sapmalar (tek liste)

Şartname metni (`docs/`) değiştirilmemiştir; aşağıdakiler kullanıcı onayıyla yapılan sapma ve eklemelerdir.

1. **Silme sadeleştirmesi ve Adım 10 kuralı (Madde 6/2 kısmi):** bağlı AKTİF patent varsa silme engellenir (N'li mesaj); yalnızca silinmiş patentler bağlıysa onlar ortaklarıyla fiziksel silinir. Pasife alma yönlendirmesi uygulanmadı.
2. **Arayüz paleti ve fontlar:** `docs/stitch-tasarim.html` esas alındı; Inter/Manrope ve Material Symbols Google Fonts'tan yüklenir (internetsiz çalışma şartı kaldırıldı).
3. **Patent formu çekmecedir** (`/patents/new`, `/patents/:id`); çekmecede alan yanındaki "+" ile **hızlı kayıt ekleme** (başvuru sahibi, bölüm, FSMH türü, vekil firma) ve başvuru sahibi seçilince **varsayılan bölümün otomatik seçilmesi** vardır.
4. **Ayarlar sayfası arayüzden çıkarıldı;** backend uçları (Madde 7) duruyor. Sayfa boyutu varsayılanı 25'tir.
5. **Vekil Durumu özet kartı çıkarıldı;** filtre çubuğundaki Vekil Durumu seçimi durur.
6. **Başvuru tarihi (bitiş) filtresi arayüzden çıkarıldı;** "Başvuru tarihinden itibaren" kaldı. Backend `date_to` parametresi durur.
7. **E-posta, İletişim Bilgisi ve Durum (aktif/pasif) alanları arayüzden çıkarıldı;** düzenlemede mevcut değerleri korunarak geri gönderilir, yeni kayıtta e-posta/iletişim boş, `is_active` true.
8. **Madde 7 tablosuna ek uç:** `GET /api/patents/export` (Excel dışa aktarma, `openpyxl`).
9. **Ek dosyalar/yapılandırma:** `backend/pytest.ini`, `app/core/text.py` (`normalize_tr`), `core/spa.py`, `core/root_path.py`, `core/security_headers.py`; `.gitignore`'da `data/**/*.db*` ve `data/**/*.xlsx` kuralları; `components/`, `pages/`, `lib/` altındaki ek dosyalar.
10. **Varsayılan bölümler** `data/source/patent-takip.xlsx`'e göre bir kerelik API ile atandı (11 kişi; "AYRILDI" olan boş bırakıldı). Veri değişikliğidir, kodda yoktur.

11. **Durum ve Tescil Tarihi (Adım 11):** `patents.registration_date` ve `patents.status` (`Tescillendi` / `Süreç Devam Ediyor` / `Reddedildi`) eklendi (migration `0002`). "Mevcut Durum" Şartname 2.2'den kullanıcı kararıyla çıkarılmıştı; bu alanla kısmen geri geldi. Tescil tarihi başvuru tarihinden önce olamaz (422). Mükerrer kontrolü değişmedi. Excel dışa aktarma bu iki sütunu da içerir; Excel import scripti değişmedi.
12. **Vekil firma yeni alanları:** `tax_no` (10 veya 11 haneli rakam), `title` (unvan), `email`; hepsi isteğe bağlı. `contact_info` ve `is_active` backend'de durur, arayüzde yoktur.
13. **Telif Hakkı türü:** `fsmh_types` seed'ine `0002` ile "Telif Hakkı" eklendi (Şartname 5.3 seed'i 4 türdü; artık 5).
14. **Yeni salt okunur uçlar (Madde 7 tablosuna ek):** `GET /api/partners`, `GET /api/departments/summary`, `GET /api/attorney_firms/summary`. Ortaklar ayrı tablo değildir; aktif patentlerin `patent_partners` kayıtlarından `normalize_tr` ile gruplanarak türetilir (görünen ad: grubun en küçük id'li yazımı). Arayüzde Ortaklar sayfası salt okunurdur; Başvuru Sahipleri, Bölümler, Vekil Firmalar ve Ortaklar sayfalarındaki "Patent Sayısı" düğmesi, kayda bağlı patent başlıklarını gösteren sağdan açılan özet panelini açar (başlığa tıklamak `/patents/{id}` düzenleme çekmecesini açar). Patent çekmecesinde Durum üç düğmeli radiogroup'tur (seçiliye tekrar tıklamak seçimi kaldırır); arayüzde "Varsayılan Bölüm" yerine "Bölüm" yazar.

Ayrıntılı teknik kararlar yukarıdaki "Onaylanan Kararlar" bölümündedir.

- **Görünüm (Adım 13):** özet kartları çerçeveli/gölgeli, başlıkları kabartmalı mor hap içinde; sayfa zemini `surface-container-low`, kart, filtre ve tablo kabukları ince çerçeve ve `shadow-card` kullanır (`tailwind.config.js` `boxShadow`, `index.css` `.emboss-text`). Veri ve davranış değişmedi.

## Madde 13 doğrulama matrisi

| Gereksinim (Madde 13) | Kanıt | Durum |
|---|---|---|
| Her router için duman testi | `tests/test_api_skeleton.py`, `test_patents.py`, `test_patent_list.py`, `test_applicants.py`, `test_departments.py`, `test_fsmh_types.py`, `test_attorney_firms.py`, `test_settings.py`, `test_patent_export.py` | Tamam |
| Ortak ad tekrarı (normalize) | `test_normalized_duplicate_409_on_post_and_put` (4 lookup), `test_normalize.py` | Tamam |
| Soft delete davranışı | `test_patents.py::test_soft_delete_hides_record_but_keeps_row`, `test_patent_list.py::test_default_order_is_id_ascending_and_soft_deleted_are_hidden` | Tamam |
| Mükerrer patent uyarısı (Madde 6/4) | `test_patents.py::test_duplicate_warning_409_then_confirm_saves` ve komşu testler | Tamam |
| Migration boş DB'de `alembic upgrade head` | `tests/test_migrations.py` (`test_upgrade_head_creates_tables`, `test_upgrade_twice_is_noop`, `test_downgrade_then_upgrade_again`) | Tamam |
| `PRAGMA journal_mode` = `wal` | `tests/test_database.py::test_pragmas_applied` | Tamam |
| `npm run build` hatasız | `cd frontend && npm run build` | Tamam |
| Production'da `/` ve `/api/health` aynı porttan | `tests/test_static.py`; elle: `python -m app.main` ile `curl :8001/`, `/api/health` (Kapanış turu) | Tamam |
| `frame-ancestors 'self'` varsayılan, `X-Frame-Options` yok; `FRAME_ANCESTORS` ile değişir | `test_api_skeleton.py::test_default_frame_ancestors_header`, `test_custom_frame_ancestors_header`, `test_x_frame_options_stripped_if_inner_app_sets_it`; `test_static.py::test_frame_ancestors_on_static_and_fallback` | Tamam |
| `ROOT_PATH` altında statik dosyalar ve `/api` | `test_static.py::test_root_path_with_static_and_api`, `test_api_skeleton.py::test_root_path_*` | Tamam |
| `VITE_BASE_PATH` ile alt yol | Otomatik test yok; yalnızca elle doğrulandı | Elle doğrulandı |
| Madde 6/2 bağlı patent varken silme engeli | `tests/test_delete_rule.py` | Kısmen (aktif patent bağlıysa engel; pasife alma yönlendirmesi yok) |
| Madde 6/2 pasife alma yönlendirmesi | — | MVP'de ertelendi |
| Migration `0002` (yeni sütunlar, Telif Hakkı seed'i, idempotent, downgrade) | `tests/test_migrations.py` (`test_0002_*`, `test_models_and_migration_in_sync`) | Tamam |
| Durum / tescil tarihi kuralları | `tests/test_patent_status.py` | Tamam |
| Vekil firma vergi no / e-posta doğrulaması | `tests/test_attorney_firms.py::test_new_fields_trimmed_empty_to_none_and_validated` | Tamam |
| Özet uçları (ortaklar, bölüm, vekil firma, başvuru sahibi) | `tests/test_summaries.py` | Tamam |
| Madde 6/6 tarih biçimi (ISO / GG.AA.YYYY) | `test_schemas.py`; arayüzde `lib/format.ts` (elle) | Tamam |

## Yol haritası

- a) Pasife alma yönlendirmesi (Madde 6/2): silme engelinde başvuru sahibi / vekil firma için `is_active=false` önerisi.
- b) Ana sisteme entegrasyon (iframe / reverse proxy / API; B9, B10): `ROOT_PATH`, `VITE_BASE_PATH` ve `frame-ancestors` ayarları entegrasyon biçimi netleşince gerçek ortamda denenecek.
- c) Şartname dışı alanlar gerekirse (Kapsam, Komisyon, Mevcut Durum, Masraf); şu an Excel aktarımında atlanıyor.
- d) `q` aramasına bölüm adı eklenmesi.
- e) Excel'deki yazım düzeltmeleri (örn. "İtfayecilik" yazımı).
- f) `settings` backend uçlarının sadeleştirilmesi veya kaldırılması kararı.
- g) FSMH türleri için yönetim sayfası (düzenleme/silme şu an yalnızca API ile).
- h) Durum filtresi ve durum özet kartı (Patent Listesi).
- i) Ortak adı düzeltme aracı (yazım farklarını tek adda birleştirme; ortaklar şu an yalnızca patent kayıtlarında düzeltilir).
