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
