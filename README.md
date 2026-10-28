# Patent Takip Otomasyonu

Bağlayıcı teknik şartname: [docs/patent-takip-otomasyon-plan.md](docs/patent-takip-otomasyon-plan.md) (v1.4).
Şartname bu dosyada değiştirilmez; aşağıdaki kararlar onaylanmış uygulama detaylarıdır.

## Onaylanan Kararlar

- Şartname `docs/` altına kopyalanır; proje içeriği doğrudan `PATENT/` köküne kurulur.
- Boş klasörlere `.gitkeep`; Python paketlerine (`app/`, `schemas/`, `routers/`, `services/`, `core/`) boş `__init__.py`.
- `routers/health.py` açılmaz; `GET /api/health` Aşama 8'de `main.py` içinde tanımlanır.
- Frontend ek dosyaları (`index.html`, `tsconfig*.json`, `postcss.config.js`, `App.tsx`, `index.css`, `components/AppShell.tsx`) Aşama 9'da eklenir.
- `created_at`/`updated_at` 5 tabloda bulunur (patents, applicants, departments, fsmh_types, attorney_firms).
- Referans (başvuru sahibi, bölüm, FSMH türü, vekil firma) silinirken silinmiş patent dahil herhangi bir bağlı patent varsa `409` döner ve pasife alma yönlendirmesi yapılır.
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
