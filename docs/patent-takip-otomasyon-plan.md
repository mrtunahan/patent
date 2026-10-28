# Patent Takip Otomasyonu — Teknik Şartname (v1.4)

> Bu doküman projenin TEK ve BAĞLAYICI teknik şartnamesidir.
> Mimari, veri modeli, klasör yapısı, MVP kapsamı ve yerel çalışma modeli buna birebir uyularak geliştirilecektir.
> Dokümanda olmayan özellik eklenmez; mevcut gereksinim basitleştirilmez veya değiştirilmez.
> Belirsiz/riskli noktalar uygulamadan ÖNCE "Belirsizlikler" başlığında (Madde 14) raporlanır ve onay beklenir.

---

## 1. Projenin Amacı

Teknoloji Transfer Ofisi (TTO) için, şu anda Excel'de tutulan **patent / FSMH (Fikri ve Sınai Mülkiyet Hakları) takip listesini** yerelde çalışan bir web uygulamasına dönüştürmek.

- Mevcut TTO Otomasyonu ile aynı mimari felsefe (FastAPI + SQLite + React, tek port) kullanılır.
- Bu uygulama şimdilik **yerelde bağımsız** çalışır. İleride Çankırı Karatekin Üniversitesi Mühendislik Fakültesi ana web sistemine modül olarak entegre edilecektir; **entegrasyon biçimi (iframe, reverse proxy veya yalnızca API tüketimi) otomasyon tamamlandıktan sonra belirlenecektir.** Üçüne de uyumlu hazırlık Madde 11'de yapılır.
- Kendi kullanıcı girişi/kimlik doğrulaması yoktur. Şimdilik uygulamaya erişen herkes tüm işlemleri yapabilir; ana sisteme entegre edildiğinde kimlik ve yetkilendirme ana sistemin sorumluluğundadır.
- Kendi veritabanını kullanır (TTO Otomasyonu veritabanından ayrı).
- Excel'deki mevcut kayıtlar ileride bir aktarım scripti ile içeri alınacaktır (bkz. Madde 12, Aşama 13). Bu aşamada **yazılmaz**.

## 2. Kapsam

### 2.1 Kapsam İçi (MVP)
- Patent/FSMH kayıtlarının listelenmesi, eklenmesi, düzenlenmesi, silinmesi (soft delete, veritabanı seviyesinde).
- Arama, filtreleme, sıralama, sayfalama.
- Başvuru sahibi, bölüm/birim, vekil firma için ayrı referans (lookup) tabloları ve yönetimi.
- Ortak kurumların (yalnızca ad olarak) kayıtla ilişkilendirilmesi.
- Yerelde çalışma; tek port üzerinden API + arayüz.
- Ana sisteme ileride entegrasyona hazırlık; biçim sonra belirlenecek (Madde 11).

**MVP sonrası (her biri ayrı onayla, Madde 12):** Excel import, Excel export, ana sisteme entegrasyon.

### 2.2 Kapsam Dışı (bu sürümde YOK)
Aşağıdaki Excel sütunları **bilinçli olarak** şema dışı bırakılmıştır (Excel görselinde üstü çizili; gerekirse sonradan eklenebilir):
- Kapsam (Ulusal/Uluslararası)
- Komisyon Toplantı Tarihi
- Komisyon Oy/Karar Durumu
- Mevcut Durum
- Masraf

Bu nedenle sistemde **parasal alan yoktur**. İleride masraf takibi eklenirse parasal alanlar `Numeric(12, 2)` + Python `Decimal` ile tanımlanır (TTO Otomasyonu kuralı ile aynı).

Ayrıca şunlar **yoktur**: kullanıcı girişi / şifre / oturum (login ekranı, users ve sessions tabloları dahil), rol bazlı yetkilendirme, Windows kurulum/servis yapılandırması, otomatik yedekleme, silinen kayıtları geri alma arayüzü (yalnızca veritabanında `deleted_at` tutulur), ortak payı/oran takibi, e-posta/bildirim, belge (PDF) yükleme, çoklu dil, dış sistem entegrasyonları (TÜRKPATENT vb.).

## 3. Alan Haritası (Excel → Sistem)

Tablo başlıkları ve sırası (UI'da ve Excel export'ta aynı sırayla gösterilir):

| # | Başlık | Sistem alanı | Zorunlu | Not |
|---|--------|--------------|---------|-----|
| 1 | Buluş Başlığı | `title` | Evet | Serbest metin, uzun olabilir (örn. "Modüler Dış Mekan Özelleştirilebilir Tuz Lambası") |
| 2 | Başvuru Sahibi | `applicant_id` → `applicants` | Evet | **Tek** kişi; aynı kişi birden çok kayıtta yer alabilir |
| 3 | Bölüm / Birim | `department_id` → `departments` | Hayır | Bölüm veya birim: "Peyzaj Mimarlığı", "Şabanözü MYO" gibi |
| 4 | FSMH Türü | `fsmh_type_id` → `fsmh_types` | Evet | Patent, Faydalı Model, Tasarım Tescili, Marka |
| 5 | Vekil Firma | `attorney_firm_id` → `attorney_firms` | Hayır | Excel'de çoğu satırda boş; dolu örnekler: "Simaj", "Destek Patent" |
| 6 | Ortaklar & Oranları | `patent_partners` tablosu | Hayır | Başlık Excel'deki adıyla korunur; **yalnızca kurum adı** tutulur, sayısal oran yok (örn. "Ankara Üni.") |
| 7 | Başvuru Tarihi | `application_date` (DATE) | Hayır | GG.AA.YYYY gösterilir, ISO saklanır; Excel'de çoğu satırda boş |
| 8 | Notlar / Açıklama | `notes` (TEXT) | Hayır | Serbest metin (örn. "Ödeme yapılması gerekiyor.") |

Ek sistem alanları: `id`, `created_at`, `updated_at`, `deleted_at`.
Excel'deki "No" sütunu **yalnızca sıra numarasıdır**; veritabanında saklanmaz. Arayüzde ve Excel export'ta listedeki satır sırasına göre (1'den başlayarak, sayfalama ofsetiyle birlikte) otomatik üretilir. Kalıcı takip numarası değildir; kaydın kimliği `id`'dir.

## 4. Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ORM / Migration | SQLAlchemy 2.x, Alembic |
| Veritabanı | SQLite (WAL modu) |
| Doğrulama | Pydantic v2 |
| Frontend | React + Vite + Tailwind CSS |
| Auth | **Yok** (entegrasyon sonrası ana sistemin sorumluluğunda) |
| Çalışma ortamı | Yerel, tek port (varsayılan 8001) |

## 5. Veri Modeli

`settings` hariç tüm tablolarda `id` INTEGER PK autoincrement'tir; `patents`, `applicants`, `departments`, `fsmh_types`, `attorney_firms` tablolarında ayrıca `created_at`, `updated_at` (UTC DATETIME) bulunur. `patent_partners` ve `settings` tablolarında zaman damgası yoktur.

### 5.1 `applicants` (Başvuru Sahipleri)
| Alan | Tip | Kısıt |
|------|-----|-------|
| id | Integer | PK |
| full_name | String(200) | NOT NULL, UNIQUE (ham değer üzerinde; normalize edilmiş mükerrer kontrolü uygulama katmanında yapılır, bkz. Madde 6/5) |
| department_id | FK → departments.id | NULL olabilir (varsayılan birim) |
| email | String(200) | NULL |
| is_active | Boolean | default true |

### 5.2 `departments` (Bölüm / Birim)
| Alan | Tip | Kısıt |
|------|-----|-------|
| id | Integer | PK |
| name | String(200) | NOT NULL, UNIQUE |

### 5.3 `fsmh_types` (FSMH Türleri)
| Alan | Tip | Kısıt |
|------|-----|-------|
| id | Integer | PK |
| name | String(100) | NOT NULL, UNIQUE |
| sort_order | Integer | default 0 |

Başlangıç seed değerleri: `Patent`, `Faydalı Model`, `Tasarım Tescili`, `Marka` (Excel'deki yazımla uyumlu).

### 5.4 `attorney_firms` (Vekil Firmalar)
| Alan | Tip | Kısıt |
|------|-----|-------|
| id | Integer | PK |
| name | String(200) | NOT NULL, UNIQUE |
| contact_info | Text | NULL |
| is_active | Boolean | default true |

### 5.5 `patents` (Ana kayıt tablosu)
| Alan | Tip | Kısıt |
|------|-----|-------|
| id | Integer | PK |
| title | String(500) | NOT NULL |
| applicant_id | FK → applicants.id | NOT NULL |
| department_id | FK → departments.id | NULL (bölüm/birim bilgisi patent kaydında tutulur) |
| fsmh_type_id | FK → fsmh_types.id | NOT NULL |
| attorney_firm_id | FK → attorney_firms.id | NULL |
| application_date | Date | NULL |
| notes | Text | NULL |
| deleted_at | DateTime | NULL (NULL = aktif kayıt; dolu = silinmiş) |
| created_at / updated_at | DateTime | |

İndeksler: `title`, `applicant_id`, `fsmh_type_id`, `application_date`, `deleted_at`.

### 5.6 `patent_partners` (Ortaklar)
Bir patentin ortak kurumları; **yalnızca ad** tutulur (Excel'de "Çankırı Karatekin Üni.", "Ankara Üni." gibi). Sayısal oran/pay alanı yoktur.

| Alan | Tip | Kısıt |
|------|-----|-------|
| id | Integer | PK |
| patent_id | FK → patents.id | NOT NULL, ON DELETE CASCADE |
| partner_name | String(200) | NOT NULL |

Kurallar:
- Aynı patentte aynı `partner_name` iki kez eklenemez (normalize edilmiş karşılaştırma uygulama katmanında yapılır).
- Ortak yoksa kayıt geçerlidir.
- Ortak adları serbest metindir (Excel'deki yazımla aynen saklanır); ayrı bir kurum tablosu yoktur.

### 5.7 `settings`
| Alan | Tip | Kısıt |
|------|-----|-------|
| key | String(100) | PK |
| value | Text | NOT NULL |

Örnekler: `institution_name`, `default_page_size`.

> `users` ve `sessions` tabloları bu projede **yoktur**.

## 6. İş Kuralları

1. Silme **soft delete**'tir: `patents.deleted_at` o anki UTC zamanla doldurulur. Listeler ve aramalar varsayılan olarak `deleted_at IS NULL` kayıtları gösterir. Silinenleri listeleme/geri alma **arayüzü yoktur** (ileride gerekirse eklenir); veri veritabanında korunur.
2. Başvuru sahibi / bölüm / FSMH türü / vekil firma silinmek istendiğinde bağlı aktif patent (`deleted_at IS NULL`) varsa silme **engellenir**; başvuru sahibi ve vekil firma için bunun yerine `is_active = false` ile pasife alma önerilir (bölüm ve FSMH türünde `is_active` alanı yoktur). Bağlı patent yoksa referans kaydı kalıcı silinir (soft delete yalnızca `patents` içindir).
3. `application_date` boş olabilir ve gelecekte bir tarih olabilir; uyarı verilmeden kabul edilir.
4. Aynı `title` + `applicant_id` + `application_date` kombinasyonu için **mükerrer kayıt uyarısı** verilir (engellemez, kullanıcı onaylayarak kaydeder); boş (`NULL`) tarihler birbirine eşit sayılır.
5. Metin alanlarında baştaki/sondaki boşluklar kırpılır; Türkçe karakter bütünlüğü (UTF-8) korunur; arama **Türkçe harf duyarsız** (ı/İ, ş/Ş vb.) yapılır; normalize işlemi uygulama katmanında tek bir yardımcı fonksiyonla yapılır (SQLite `lower()` Türkçe karakterleri doğru işlemez), bu nedenle ek sütun gerekmez.
6. Tarihler veritabanında ISO (`YYYY-MM-DD`), arayüzde `GG.AA.YYYY`.

## 7. API Tasarımı (REST, `/api` öneki)

| Router | Endpoint'ler |
|--------|--------------|
| `patents` | `GET /api/patents` (arama, filtre, sıralama, sayfalama), `POST`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` (soft delete) |
| `applicants` | CRUD |
| `departments` | CRUD |
| `fsmh_types` | CRUD |
| `attorney_firms` | CRUD |
| `settings` | `GET`, `PUT` |
| `health` | `GET /api/health` |

Liste filtreleri: `q` (başlık/başvuru sahibi/ortak/not içinde arama), `applicant_id`, `department_id`, `fsmh_type_id`, `attorney_firm_id`, `date_from`, `date_to`, `has_attorney` (bool), `sort_by`, `sort_dir`, `page`, `page_size`.

İskelet aşamasında endpoint'ler boş/501 iskelet olarak oluşturulur.

## 8. Klasör Yapısı

```
patent-takip/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── applicant.py
│   │   │   ├── department.py
│   │   │   ├── fsmh_type.py
│   │   │   ├── attorney_firm.py
│   │   │   ├── patent.py
│   │   │   ├── patent_partner.py
│   │   │   └── setting.py
│   │   ├── schemas/
│   │   ├── routers/
│   │   │   ├── patents.py
│   │   │   ├── applicants.py
│   │   │   ├── departments.py
│   │   │   ├── fsmh_types.py
│   │   │   ├── attorney_firms.py
│   │   │   └── settings.py
│   │   ├── services/
│   │   └── core/            # ortak bağımlılıklar, yardımcılar, güvenlik başlığı middleware'i
│   ├── alembic/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   └── main.tsx
│   ├── vite.config.ts       # dev proxy → backend
│   ├── tailwind.config.js   # tema renkleri/font tek noktada
│   └── package.json
├── scripts/                 # (excel_import.py ileride, şimdilik boş)
├── docs/
│   └── patent-takip-otomasyon-plan.md # bu şartname
├── data/                    # patent.db burada (git'e girmez)
├── .env.example             # ayarlanabilir değerler: host/port, CORS_ORIGINS, FRAME_ANCESTORS, ROOT_PATH, VITE_BASE_PATH
├── .gitignore
└── README.md
```

## 9. Veritabanı Yapılandırması

- Dosya: `data/patent.db`.
- Engine bağlantısında `connect_args={"check_same_thread": False}` ve bağlantı açılışında event listener ile:
  - `PRAGMA journal_mode=WAL;`
  - `PRAGMA foreign_keys=ON;`
  - `PRAGMA synchronous=NORMAL;`
  - `PRAGMA busy_timeout=5000;`
- Şema değişiklikleri yalnızca Alembic migration ile yapılır; `create_all` kullanılmaz.

## 10. Frontend

- React + Vite + Tailwind CSS.
- Geliştirme: Vite dev server (5173) → `/api` isteklerini backend'e (8001) proxy eder.
- Production: `npm run build` çıktısı (`frontend/dist`) FastAPI `StaticFiles` ile **aynı porttan** servis edilir; SPA için bilinmeyen yollar `index.html`'e düşer (`/api` hariç).
- İlk aşamada sayfalar yalnızca placeholder route'lardır: Patent Listesi, Patent Formu, Başvuru Sahipleri, Bölümler, Vekil Firmalar, Ayarlar.
- Liste sayfası hedefi (sonraki aşama): Excel'deki 8 sütun, bu şartnamedeki sırayla, başında otomatik sıra numarası (No) sütunuyla; satır içi hızlı arama; filtre çubuğu; Türkçe arayüz.

**Arayüz düzeni (bağımsız çalışma, entegrasyona uyumlu):**
- Uygulama şimdilik kendi basit üst başlığı ("Patent Takip") ve sekmeli gezinmesiyle (Patent Listesi, Başvuru Sahipleri, Bölümler, Vekil Firmalar, Ayarlar) çalışır.
- Başlık ve gezinme tek bir `AppShell` bileşeninde toplanır; entegrasyon biçimi netleşince bu kabuk kolayca kaldırılabilir veya sadeleştirilebilir (örn. iframe'de başlıksız kullanım).
- Düzen duyarlıdır (dar genişlikte yatay taşma yok); tüm bağlantılar göreli yoldur, `window.top` yönlendirmesi kullanılmaz.
- Tema (font, renk, köşe yuvarlaklığı) `tailwind.config.js` içinde tek noktada tanımlanır; ana sistemin görünümüne ileride uyarlanabilir.

## 11. Çalışma Modeli ve Modül Entegrasyonu

- Uygulama yerelde çalışır; Uvicorn host ve port değerleri `.env`/`config.py` üzerinden ayarlanır (varsayılan `127.0.0.1:8001`).
- **Kimlik doğrulama yoktur.** Login ekranı, kullanıcı adı/şifre, session cookie ve `users`/`sessions` tabloları bulunmaz. Tüm `/api` uçları doğrudan erişilebilir; erişim kontrolü şimdilik yoktur, entegrasyon sonrası ana sistemin sorumluluğundadır. Çerez kullanılmadığı için ileride gömme senaryolarında çerez sorunu oluşmaz.

**Entegrasyon biçimi (B9): ileride karar verilecek.** Şimdilik uygulama yerelde bağımsız çalışır. Karar netleşmeden aşağıdaki hazırlıklar üç senaryoya da (iframe, reverse proxy, yalnızca API tüketimi) uyum sağlar:

| Senaryo | Hazırlık |
|---------|----------|
| API tüketimi | Tüm API yolları sabit `/api` önekinde kalır; yanıtlar JSON; CORS izinli origin listesi `.env` (`CORS_ORIGINS`) ile ayarlanır (varsayılan: production'da kapalı/aynı origin, dev'de Vite origin'i). |
| Reverse proxy | Uygulama bir alt yol altında servis edilebilir: backend `ROOT_PATH`, frontend `VITE_BASE_PATH` ayarlarıyla (varsayılan boş = kök). Frontend API taban adresi tek yapılandırma noktasından (`frontend/src/api/`) okunur. |
| iframe | `Content-Security-Policy: frame-ancestors` başlığı `.env` içindeki `FRAME_ANCESTORS` ile ayarlanır (varsayılan: `'self'`); `X-Frame-Options` gönderilmez (CSP ile çakışmasın diye). Arayüz kabuğu `AppShell` olarak ayrıdır (Madde 10). |

Bu ayarların hiçbiri varsayılanda dış erişim açmaz; entegrasyon aşamasında yalnızca `.env` değerleri doldurulur.

- SQL enjeksiyonuna karşı yalnızca ORM/parametreli sorgu kullanılır.
- Gizli/yerel ayarlar `.env` içinde; `.env` ve `data/patent.db` git'e girmez.

## 12. Geliştirme Aşamaları

1. Şartname analizi, belirsizlik raporu, **onay**.
2. Klasör yapısının (Madde 8) birebir oluşturulması.
3. Backend kurulumu: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, Alembic.
4. SQLite + WAL yapılandırması (Madde 9).
5. SQLAlchemy modelleri: applicants, departments, fsmh_types, attorney_firms, patents, patent_partners, settings — Madde 5, alan alan.
6. Alembic altyapısı, ilk migration, çalıştırma.
7. Pydantic request/response şemaları.
8. FastAPI app + router iskeleti (Madde 7) + ayarlanabilir `frame-ancestors` başlığı (Madde 11).
9. Frontend: React + Vite + Tailwind altyapısı (`AppShell` + sekmeli iskelet).
10. Production'da tek port: StaticFiles mount.
11. Dev proxy (Vite → backend) doğrulaması.
12. `.gitignore` (`data/*.db*`, `node_modules`, `.venv`, `__pycache__`, `.env`, `frontend/dist`).
13. **Excel aktarım scripti (`excel_import.py`) — bu aşamada YAZILMAZ.**
14. Detaylı UI sayfaları — bu aşamada YAZILMAZ (yalnızca placeholder).

Her aşama sonunda rapor: oluşturulan/değiştirilen dosyalar, dayanılan şartname maddesi, test komutu ve çıktısı, kalan TODO. Hata olursa kök neden bulunup düzeltilir, sessiz workaround yapılmaz.

Sonraki aşamalar (ayrı onayla): CRUD uçlarının gerçek mantığı → liste/form UI → Excel import → Excel export → ana sisteme entegrasyon (biçim o zaman belirlenir).

## 13. Test Gereksinimleri

- Backend: pytest + FastAPI TestClient; her router için en az duman testi; ortak ad tekrarı ve soft delete (`deleted_at`) davranışı için birim testleri.
- DB: migration'ın boş veritabanında `alembic upgrade head` ile hatasız çalışması; `PRAGMA journal_mode` sorgusunun `wal` döndüğünün doğrulanması.
- Frontend: `npm run build` hatasız; production'da `/` ve `/api/health` aynı porttan yanıt verir.
- Entegrasyon hazırlığı: varsayılanda yanıt başlığında `frame-ancestors 'self'` bulunur ve `X-Frame-Options` bulunmaz; `FRAME_ANCESTORS` ayarlanınca başlık değişir; `ROOT_PATH`/`VITE_BASE_PATH` ile alt yol altında servis edildiğinde statik dosyalar ve `/api` çalışır.

## 14. Belirsizlikler ve Kararlar

### Çözülen kararlar
- **B1:** Bir buluşta tek başvuru sahibi olur (tek `applicant_id`). Aynı kişi birden çok kayıtta yer alabilir.
- **B2:** Bölüm/birim bilgisi patent kaydında ayrı alandır; başvuru sahibinde yalnızca varsayılan olarak tutulur.
- **B3:** FSMH türleri: Patent, Faydalı Model, Tasarım Tescili, Marka (Excel'deki "Tasarım Tescili" yazımıyla).
- **B4:** Ortaklar yalnızca kurum adıdır; sayısal oran/pay yoktur.
- **B5:** Başvuru tarihi boş olabilir (Excel'de çoğu satırda boş).
- **B6:** Varsayılan port 8001 (TTO Otomasyonu 8000); onaylandı.
- **B7:** Silinen kayıtlar için arayüz yok; veritabanında `deleted_at` tutulur.
- **B8:** Üstü çizili sütunlar (Kapsam, Komisyon Toplantı Tarihi, Komisyon Karar Durumu, Mevcut Durum, Masraf) şema dışı; gerektiğinde sonradan eklenebilir.
- **B11:** Ortak kurum adları serbest metin olarak, Excel'deki yazımla aynen saklanır; ayrı kurum tablosu yoktur.
- Kimlik doğrulama yok; Windows kurulum/servis ve yedekleme kapsam dışı.
- Excel'deki "No" yalnızca sıra numarasıdır, saklanmaz.
- Uygulama şimdilik yerelde bağımsız çalışır.

### İleride karar verilecek
- **B9 — Entegrasyon biçimi:** iframe, reverse proxy veya yalnızca API tüketimi; otomasyon tamamlandıktan sonra belirlenecek. Üçüne de uyumlu hazırlık Madde 11'de yapılır.
- **B10 — Ana sistem adresi ve "Aktif Bölüm" bağlamı:** Entegrasyon kararıyla birlikte ele alınır; şimdilik patent listesi tüm kayıtları gösterir, bölüm yalnızca filtredir.

### Açık madde
Uygulamayı bloklayan açık madde yoktur.

---
*Sürüm: 1.4 — Taslak, onay bekliyor.*
