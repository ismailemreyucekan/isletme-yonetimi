# Kasa — Restoran/Kafe Kasa & QR Ödeme Sistemi

Çok kiracılı (multi-tenant) POS + QR ödeme SaaS. Detaylı ürün/teknik plan: [PLAN.md](PLAN.md).

> **Geliştirme tamamen Docker üzerinden yürür.** Bilgisayarına Python, Node veya
> PostgreSQL kurmana gerek yok — sadece **Docker Desktop** ve **Git** yeterli.

## Monorepo Yapısı

```
kasa/
├─ backend/    # FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Redis
├─ frontend/   # React + TypeScript + Vite + Tailwind
├─ docker-compose.yml
└─ PLAN.md
```

## Başlangıç (yeni geliştirici için 3 adım)

**Ön koşul:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) + [Git](https://git-scm.com/) kurulu ve Docker Desktop açık olmalı.

```bash
git clone https://github.com/ismailemreyucekan/isletme-yonetimi.git
cd isletme-yonetimi
docker compose up --build
```

Açılınca:

| Servis | Adres |
|---|---|
| Uygulama (frontend) | http://localhost:5173 |
| API + Swagger | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (kullanıcı/parola/db: `kasa`/`kasa`/`kasa`) |
| Redis | localhost:6379 |

Uygulamada **"İşletme Kaydı"** ile hesap oluşturup giriş yaparsın. Ekstra `.env`
ayarı gerekmez; geliştirme varsayılanları `docker-compose.yml` içinde gömülü.

> **Port çakışması (5432):** Makinende zaten yerel bir PostgreSQL kuruluysa
> Docker'ın Postgres'i 5432'yi alamaz. Bu durumda kök dizinde bir `.env` oluştur
> (`DB_PORT=5433`) ve dış araçlarda (ör. masaüstü pgAdmin) **localhost:5433**
> kullan. API/frontend bundan etkilenmez (içeride `db:5432` kullanır).

## Canlı Geliştirme (hot-reload)

Kaynak kodlar konteynere bağlı (bind-mount) — **kod değişince otomatik yenilenir,
rebuild gerekmez:**

- **Backend:** `uvicorn --reload` (Python dosyasını kaydet → API kendini yeniler).
- **Frontend:** Vite HMR (bileşeni kaydet → tarayıcı anında güncellenir).

> Yalnızca **bağımlılık** eklediğinde (yeni pip/npm paketi) imajı yeniden
> kurman gerekir: `docker compose up -d --build`.

## Sık Kullanılan Komutlar

```bash
docker compose up                 # başlat (logları ekranda)
docker compose up -d              # arka planda başlat
docker compose up -d --build      # bağımlılık değişince yeniden kur
docker compose ps                 # servis durumu
docker compose logs -f api        # api loglarını izle
docker compose down               # durdur (DB verisi kalır)
docker compose down -v            # durdur + DB verisini sil

# Testler / lint (konteyner içinde, yerel kurulum gerekmeden):
docker compose exec api pytest -q
docker compose exec api ruff check app tests

# Veritabanı (psql):
docker compose exec db psql -U kasa -d kasa

# Yeni migrasyon üretme (model değiştirdiğinde):
docker compose exec api alembic revision --autogenerate -m "aciklama"
docker compose exec api alembic upgrade head
```

> Not: Migrasyonlar `api` konteyneri her başladığında otomatik uygulanır
> (`alembic upgrade head`).

## Katkı Akışı

Depo public; herkes klonlayabilir. Push için ya repo'ya **collaborator** eklenmeli
ya da **fork + Pull Request** yapılmalı. Önerilen akış:

```bash
git checkout -b ozellik/menu-yonetimi
# ... değişiklikler ...
git commit -m "Menü yönetimi eklendi"
git push -u origin ozellik/menu-yonetimi   # sonra GitHub'da PR aç
```

Her PR'da CI (`.github/workflows/ci.yml`) backend lint+test ve frontend lint+build
çalıştırır.

## Docker'sız Yerel Geliştirme (opsiyonel)

Docker tercih etmeyenler için alternatif `backend/.env.example` ve aşağıdaki adımlar
kullanılabilir; ancak **önerilen yol Docker'dır**.

```bash
# Veritabanı + Redis'i yine Docker'dan al:
docker compose up -d db redis

# Backend:
cd backend && python -m venv .venv && . .venv/Scripts/activate
pip install -e ".[dev]" && cp .env.example .env
alembic upgrade head && uvicorn app.main:app --reload

# Frontend:
cd frontend && npm install && npm run dev
```
