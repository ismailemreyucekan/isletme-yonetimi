# Restoran/Kafe Kasa & QR Ödeme Sistemi — Proje Planı

> Çok kiracılı (multi-tenant) SaaS. Backend: Python (FastAPI). Frontend: React + TypeScript.
> Ödeme: iyzico/PayTR (online) + nakit/kart manuel kayıt. Yasal entegrasyon (ÖKC/e-fatura) sonraki faza bırakıldı, mimaride yer tutucu var.

---

## 1. Ürün Vizyonu

Restoran ve kafelerin tek bir panelden yönetebileceği bir kasa (POS) sistemi:

- **Garson/Kasa POS:** masa açma, sipariş alma, hesap kapatma.
- **Menü yönetimi:** kategori/ürün/fiyat/stok yönetimi.
- **Mutfak ekranı (KDS):** siparişlerin mutfağa canlı düşmesi.
- **QR ile müşteri ödeme:** müşteri masadaki QR'ı okutur, yediği/içtiğini seçer, hesabı böler ve kartla öder (ya da kasada nakit öder).

İş modeli: birden fazla işletme aynı sisteme abone olur; her işletmenin kendi menüsü, masaları, kullanıcıları ve raporları izole olur.

---

## 2. Teknoloji Yığını (Tech Stack)

### Backend
| Katman | Seçim | Neden |
|---|---|---|
| Dil/Framework | **Python + FastAPI** | Async, native WebSocket, otomatik OpenAPI/Swagger dokümantasyon |
| ORM | **SQLAlchemy 2.0** + **Alembic** | Olgun ORM + güvenli şema migrasyonları |
| Veritabanı | **PostgreSQL** | İlişkisel, çok kiracılı için güçlü, JSONB esnekliği |
| Cache / Pub-Sub | **Redis** | WebSocket ölçekleme (pub/sub), oturum, cache, kilitleme |
| Doğrulama | **Pydantic v2** | İstek/yanıt şemaları, ayar yönetimi |
| Auth | **JWT** (access + refresh) | Personel için rol bazlı; müşteri için anonim masa oturumu |
| Arka plan işleri | **FastAPI BackgroundTasks** (sonra Celery) | E-posta, webhook işleme |
| Test | **pytest** + httpx | Birim + entegrasyon testleri |

### Frontend
| Katman | Seçim | Neden |
|---|---|---|
| Framework | **React + TypeScript + Vite** | Hızlı geliştirme, tip güvenliği |
| Sunucu durumu | **TanStack Query** | Cache, otomatik yenileme, optimistic update |
| Yerel durum | **Zustand** | Hafif global state (aktif masa, sepet) |
| Routing | **React Router** | SPA yönlendirme |
| UI | **Tailwind CSS** + **shadcn/ui** | Hızlı, tutarlı, erişilebilir bileşenler |
| Gerçek zamanlı | **WebSocket** (native) | KDS ve canlı sipariş/ödeme güncellemeleri |
| Müşteri tarafı | **PWA / mobil web** | QR ile açılan hafif, kurulumsuz arayüz |

### Altyapı
- **Docker + docker-compose** (geliştirme ortamı: api + postgres + redis).
- **Nginx** (reverse proxy, statik dosya servisi) — prod.
- **GitHub Actions** — CI (lint + test + build).
- Ödeme sağlayıcı: **iyzico** veya **PayTR** (Türkiye). Soyutlanmış `PaymentProvider` arayüzü ile değiştirilebilir.

---

## 3. Uygulama Bileşenleri (3 ayrı arayüz, tek backend)

```
                       ┌───────────────────────────┐
                       │       FastAPI Backend       │
                       │  REST API + WebSocket + Auth│
                       └──────────────┬──────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
   ┌──────────────────┐   ┌────────────────────┐   ┌────────────────────┐
   │  Personel Paneli  │   │   Mutfak Ekranı     │   │  Müşteri QR Web     │
   │ (POS + Menü Admin)│   │       (KDS)         │   │ (mobil, anonim)     │
   │   React SPA/PWA   │   │     React SPA       │   │   React PWA         │
   └──────────────────┘   └────────────────────┘   └────────────────────┘

        ┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐
        │  PostgreSQL  │     │    Redis     │     │  Ödeme (iyzico/PayTR)│
        └──────────────┘     └──────────────┘     └─────────────────────┘
```

İlk etapta üçü tek bir React monorepo'sunda farklı route/uygulama olarak yaşar; ileride ayrı build alınabilir.

---

## 4. Çok Kiracılılık (Multi-Tenancy) Stratejisi

**Yaklaşım: Tek veritabanı, tek şema, `tenant_id` (restaurant_id) kolonu** ile satır bazlı izolasyon.

- Her tabloda `restaurant_id` foreign key bulunur.
- Tüm sorgular middleware/dependency üzerinden otomatik olarak aktif kiracıya filtrelenir.
- JWT içine `restaurant_id` gömülür; her istekte doğrulanır.
- Ek güvenlik için PostgreSQL **Row-Level Security (RLS)** sonradan eklenebilir.
- Neden bu? KOBİ ölçeğinde en basit ve en uygun maliyetli; şema-per-tenant veya db-per-tenant karmaşıklığına MVP'de gerek yok.

---

## 5. Veri Modeli (Özet)

```
Restaurant (kiracı / hesap)
  ├─ id, name, slug, plan, created_at, settings(JSONB)
  │
  ├─ User (personel)
  │     id, restaurant_id, name, email, password_hash, role[owner|manager|cashier|waiter]
  │
  ├─ Table (masa)
  │     id, restaurant_id, name/no, qr_token (benzersiz), status[empty|occupied]
  │
  ├─ MenuCategory
  │     id, restaurant_id, name, sort_order, is_active
  │
  ├─ MenuItem (ürün)
  │     id, restaurant_id, category_id, name, description, price, image_url,
  │     is_available, stock(opsiyonel)
  │
  ├─ ModifierGroup (opsiyon grubu: "Boy", "Süt tipi", "Ekstralar", "Pişirme")
  │     id, restaurant_id, name, selection_type[single|multiple],
  │     min_select, max_select, is_required, sort_order
  │
  ├─ Modifier (opsiyon: "Büyük +15₺", "Yulaf sütü +10₺")
  │     id, modifier_group_id, name, price_delta, is_available, sort_order
  │
  ├─ MenuItemModifierGroup  (ürün ↔ opsiyon grubu, çoka-çok)
  │     menu_item_id, modifier_group_id     ← bir grup birden çok üründe kullanılır
  │
  ├─ Order (masa hesabı / oturum)
  │     id, restaurant_id, table_id (online siparişte boş olabilir),
  │     source[dine_in|takeaway|qr_self_order|yemeksepeti|getir|trendyol|...],
  │     external_order_id, external_status, customer_info(JSONB: ad/tel/adres),
  │     status[open|partially_paid|paid|closed],
  │     opened_by(user), opened_at, closed_at,
  │     subtotal, service_charge_rate, service_charge_amount, discount_amount,
  │     total, paid_total
  │
  ├─ OrderItem (sipariş satırı)
  │     id, order_id, menu_item_id, name_snapshot, unit_price, quantity, note,
  │     line_total (unit_price + opsiyonlar) * quantity,
  │     kitchen_status[new|preparing|ready|served], paid_status[unpaid|locked|paid]
  │
  ├─ OrderItemModifier (seçilen opsiyon snapshot'ı)
  │     id, order_item_id, modifier_id, name_snapshot, price_delta_snapshot
  │
  ├─ Payment (ödeme kaydı)
  │     id, restaurant_id, order_id, amount, tip_amount, method[online|cash|card],
  │     provider_ref, status[pending|success|failed], split_type, created_at,
  │     tip_for_user_id (opsiyonel — bahşiş garsona atfedilirse)
  │
  ├─ MarketplaceIntegration (online platform bağlantısı — kiracı başına, opsiyon)
  │     id, restaurant_id, platform[yemeksepeti|getir|trendyol|...], store_id,
  │     credentials(şifreli), is_enabled
  │
  └─ MenuItemChannelMapping (kanal bazlı eşleme/fiyat)
        menu_item_id, channel, external_item_id, price_override, is_available
```

> **Önemli tasarım kararı:** `OrderItem.name_snapshot` ve `unit_price` sipariş anındaki değeri saklar — menü fiyatı sonradan değişse bile geçmiş hesap bozulmaz.

> **Yasal yer tutucu:** `Payment` ve `Order` tablolarına ileride `fiscal_receipt_id` / `einvoice_id` alanları eklenecek; servis katmanında `FiscalService` arayüzü boş implementasyonla şimdiden tanımlanır.

---

## 6. QR ile Ödeme Akışı (Çekirdek Özellik)

```
1. Her masada statik QR:  https://app.com/r/{slug}/t/{qr_token}
        │
2. Müşteri okutur ──► Backend masayı + AKTİF order'ı bulur
        │
3. Mobil web hesabı kalem kalem gösterir (ödenmemiş ürünler)
        │
4. Müşteri ödeme yöntemini seçer:
     a) Tüm hesabı öde
     b) Kendi yediklerini seç (item-level)   ← "ne içip yediysen onu seç"
     c) Eşit böl (X kişiye)
        │
5. Seçilen kalemler KİLİTLENİR (paid_status=locked, kısa süreli)
   → aynı ürünü iki kişinin ödemesini engeller (Redis kilidi)
        │
6. Ödeme:
     • Online  → iyzico/PayTR ödeme sayfası → webhook ile doğrulama
     • Nakit   → garson kasadan "ödendi" işaretler
        │
7. Başarılı ödeme → kalemler paid, Payment kaydı oluşur
   → POS ve KDS'ye WebSocket ile anlık bildirim
        │
8. Tüm kalemler ödendiyse → Order kapanır, masa boşalır
```

**Hesap bölme mantığı — dikkat edilecekler:**
- **Item-level kilitleme:** iki müşterinin aynı ürünü ödemesini önlemek için Redis tabanlı kısa ömürlü kilit + DB'de `paid_status=locked`.
- **Kalan tutar takibi:** `order.total - order.paid_total` her zaman tutarlı olmalı; ödemeler atomik (transaction) işlenmeli.
- **Zaman aşımı:** kilitlenmiş ama ödenmemiş kalemler X dakika sonra serbest bırakılır.
- **Eşit bölme:** toplam / kişi sayısı; küsurat yuvarlama kuralı netleştirilir.

---

## 6.1 Ürün Opsiyonları (Modifiers)

Ürünlere bağlı seçenekler — örn. kahvede *boy*, *süt tipi*, *ekstra shot*; yemekte *pişirme derecesi*, *ekstra malzeme*; soslar.

- **ModifierGroup** (opsiyon grubu): "Boy", "Süt tipi", "Ekstralar".
  - `selection_type`: **single** (radio — biri seçilir) / **multiple** (checkbox — birden çok).
  - `min_select` / `max_select`: kaç seçim zorunlu/serbest (örn. en az 1, en fazla 3 ekstra).
  - `is_required`: zorunlu mu (örn. "Boy" seçilmeden sepete eklenemez).
- **Modifier** (opsiyon): "Büyük (+15₺)", "Yulaf sütü (+10₺)" — her birinin `price_delta`'sı var (artı/eksi/sıfır olabilir).
- Bir grup **çoka-çok** ile birden çok ürüne bağlanır → "Boy" grubunu tüm sıcak içeceklerde tek seferde tanımlarsın.
- **Snapshot mantığı:** sipariş anında seçilen opsiyonlar `OrderItemModifier` olarak ad + fiyatla birlikte donar; menü sonradan değişse de geçmiş hesap bozulmaz.
- **Fiyat:** `line_total = (unit_price + Σ seçili opsiyon price_delta) × quantity`.
- **Görünürlük:** seçilen opsiyonlar hem **KDS**'de (mutfak "yulaf sütü, büyük" görür), hem POS adisyonunda, hem QR hesabında satır altında gösterilir.

> Müşteri QR'dan sipariş de verecekse (bkz. öneriler) opsiyon seçimi mobil arayüzde de gerekir — bu yüzden modeli baştan doğru kurmak önemli.

## 6.2 Bahşiş (Tip) & Servis Ücreti

İki ayrı kavram, ayrı yönetilmeli:

**Servis ücreti / kuver (otomatik):**
- Restoran ayarından açılır/kapanır; oran (`service_charge_rate`, örn. %10) veya kişi başı sabit kuver olarak tanımlanır.
- Hesaba **otomatik** eklenir (`service_charge_amount`), ara toplam üzerinden hesaplanır.
- Genelde ciroya/vergiye dahildir — muhasebe açısından bahşişten ayrı tutulur.
- Hesap bölünürken oransal dağıtılır.

**Bahşiş (gönüllü):**
- Online ödemede müşteri seçer: hazır oranlar (**%5 / %10 / %15**), **özel tutar**, veya **yukarı yuvarlama**.
- Nakit ödemede garson kasadan tutar girebilir.
- `Payment.tip_amount` olarak saklanır; isteğe bağlı garsona atfedilir (`tip_for_user_id`) → garson bazlı bahşiş raporu.
- Genelde ciro dışıdır — toplam ödeme = `amount + tip_amount`, ama satış raporunda bahşiş ayrı gösterilir.

> **Net kural:** Müşterinin ödediği = ürünler + servis ücreti − indirim + bahşiş. Raporlamada bu dört kalem **ayrı** tutulur ki ciro, servis ve bahşiş karışmasın.

## 6.3 Önerilerim — Eklemeye Değer Özellikler

Mevcut planı bozmadan, değer/efor dengesine göre sıraladım:

**MVP'ye dahil edildi:**
1. **Garson çağır / hesap iste butonu:** QR ekranından tek dokunuş; POS'a anlık bildirim.
2. **İndirim & kampanya:** Satır veya hesap bazlı indirim (% veya tutar), kupon kodu. (`discount_amount` zaten modelde.)
3. **Gün sonu / Z-raporu benzeri özet & kasa devri:** Vardiya açılış-kapanış, nakit sayım mutabakatı. İşletme için olmazsa olmaz.

**İşletme bazlı opsiyon (feature flag):**
4. **QR'dan sipariş verme (self-order):** Müşteri sadece ödemekle kalmaz, masadan menüyü görüp **sipariş de verir**; sipariş doğrudan KDS'ye düşer. Her işletme kendi panelinden **açıp kapatabilir** (`settings.self_order_enabled`). Opsiyon modeli ve KDS buna zaten hazır olduğundan, MVP'de altyapısı kurulur, varsayılan **kapalı** gelir.

**Orta değer:**
5. **Sipariş tipi:** masada / gel-al / paket — tek modelle (`order_type`).
6. **Mutfak/bar yazıcısı entegrasyonu:** KDS ekranı olmayan yerler termal yazıcı ister (fiş yazdırma).
7. **Masa birleştirme / taşıma:** iki masayı birleştir, hesabı başka masaya taşı.
8. **Çoklu dil & para birimi menü:** turistik bölgeler için (TR/EN), QR menüde dil seçimi.
9. **Stok düşümü:** ürün satıldıkça basit stok azaltma + "tükendi" otomatik kapatma.

**İleride (faz 6+):**
10. **Sadakat / puan programı**, **ödeme sonrası değerlendirme/yorum**, **happy hour / zamana bağlı fiyat**, **rezervasyon**.

> **Karar:** Garson çağır, indirim/kampanya ve gün sonu/kasa devri MVP'ye alındı. QR'dan sipariş, işletme bazlı açılıp kapanan opsiyon olarak kurgulandı (varsayılan kapalı). Yol haritası (§9) buna göre güncellendi.

### İşletme Ayarları & Özellik Bayrakları (Feature Flags)

`Restaurant.settings` (JSONB) üzerinden işletmeye özel davranışlar yönetilir; örnek:

```jsonc
{
  "self_order_enabled": false,      // QR'dan sipariş (opsiyon)
  "service_charge_enabled": true,   // servis ücreti uygula
  "service_charge_rate": 10,        // %
  "tip_enabled": true,              // QR ödemede bahşiş sor
  "currency": "TRY",
  "languages": ["tr"],
  "marketplace_integrations": {     // online sipariş platformları (opsiyon)
    "yemeksepeti": false,
    "getir": false,
    "trendyol_yemek": false
  }
}
```

Backend her isteğte aktif bayrakları uygular; frontend bu ayarlara göre ilgili UI'ı gösterir/gizler. Sonradan eklenecek opsiyonlar (çoklu dil, stok vb.) de aynı yapıya yazılır.

## 6.4 Online Sipariş Platformu Entegrasyonu (opsiyon)

Yemeksepeti, Getir Yemek, Trendyol Yemek gibi platformlardan gelen siparişlerin doğrudan sisteme düşmesi. İşletme bazlı açılır (`settings.marketplace_integrations`).

**Neden değerli:** Restoranlar bu siparişleri ayrı ayrı tabletlerden takip etmek zorunda kalmaz ("tablet kalabalığı" sorunu); hepsini tek POS + KDS ekranından yönetir.

**Kapsam:**
- **Sipariş alma (injection):** platform siparişi webhook/API ile gelir → otomatik adisyon + KDS'ye düşer.
- **Sipariş onay/red** ve **durum güncelleme** (hazırlanıyor / hazır / kuryeye verildi).
- **Menü senkronu:** ürün / fiyat / müsaitlik bilgisini platformlara push (tek menü, çok kanal).
- **Mağaza durumu:** aç / kapa / yoğun modu.
- **Kanal bazlı fiyat:** platform fiyatı dükkân fiyatından farklı olabilir (komisyon farkı).

**Mimari:**
- `MarketplaceProvider` soyut arayüzü (PaymentProvider ile aynı desen) — her platform/aggregator bir implementasyon.
- İki yol:
  1. **Doğrudan API:** her platformun partner API'si — iş ortaklığı/onay gerekir, her platform ayrı entegrasyon.
  2. **Aggregator/middleware:** tek API ile birden çok platform — daha hızlı, bakımı kolay. **Önerilen başlangıç yolu.**
- Gelen sipariş `Order.source` ile işaretlenir; **KDS ve POS'ta kanal rozeti** (renk + logo) gösterilir.
- **Güvenlik:** kimlik bilgileri şifreli saklanır; webhook imza doğrulaması; **idempotent** işleme (çift sipariş engellenir).

> Bu entegrasyonlar platformlarla **iş ortaklığı/onay** gerektirir; teknik altyapı hazır olur, her işletme kendi hesabını panelden bağlar. Veri modeli etkisi §5'te.

## 7. Gerçek Zamanlı Mimari (WebSocket)

- FastAPI WebSocket endpoint'i: `/ws?token=...` (personel) ve masa kanalı (müşteri).
- **Kanal yapısı:** her restoran için `restaurant:{id}` namespace; alt konular: `kds`, `pos`, `table:{id}`.
- Çok instance ölçekleme için **Redis Pub/Sub** ile mesaj dağıtımı.
- Yayınlanan olaylar: `order.created`, `order.item.added`, `item.status.changed`, `payment.succeeded`, `order.closed`.

---

## 8. Önerilen Proje Yapısı

```
kasa/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/            # config, security, db session, deps
│  │  ├─ models/          # SQLAlchemy modelleri
│  │  ├─ schemas/         # Pydantic şemaları
│  │  ├─ api/
│  │  │  ├─ deps.py       # auth + tenant dependency'leri
│  │  │  └─ routes/       # auth, menu, tables, orders, payments, ws
│  │  ├─ services/        # iş mantığı (order, payment, fiscal[placeholder])
│  │  ├─ realtime/        # websocket + redis pubsub
│  │  └─ integrations/    # payment_providers (iyzico, paytr)
│  ├─ alembic/            # migrasyonlar
│  ├─ tests/
│  ├─ pyproject.toml
│  └─ Dockerfile
│
├─ frontend/
│  ├─ src/
│  │  ├─ apps/
│  │  │  ├─ staff/        # POS + menü admin
│  │  │  ├─ kds/          # mutfak ekranı
│  │  │  └─ customer/     # QR mobil ödeme
│  │  ├─ shared/          # api client, ws client, ui bileşenleri, types
│  │  └─ main.tsx
│  ├─ package.json
│  └─ Dockerfile
│
├─ docker-compose.yml
├─ .github/workflows/ci.yml
└─ PLAN.md
```

---

## 8.1 Tasarım Sistemi & Kullanılabilirlik (UX/UI)

Hedef: **personel hızlı kullansın, müşteri düşünmeden ödesin, ekranlar profesyonel görünsün.** Üç yüzeyin (POS / KDS / müşteri) kullanıcısı, cihazı ve ortamı farklı olduğundan her biri ayrı tasarlanır ama ortak bir dile bağlanır.

### Tasarım İlkeleri
1. **Hız öncelikli (personel):** en sık yapılan iş (ürün ekleme, hesap kapatma) **1–2 dokunuşta** bitsin.
2. **Bağlama göre tasarım:** yoğun serviste garson, sıcak/gürültülü mutfak, telefonuyla müşteri — her biri için farklı düzen.
3. **Hata affediciliği:** her kritik aksiyonda geri al / onay; yanlış ürünü silmek kolay olsun.
4. **Net hiyerarşi:** tutar, masa no, sipariş durumu gibi kritik bilgiler büyük ve önde.
5. **Tutarlılık:** tek tasarım dili, tek bileşen seti — öğrenmesi kolay.
6. **Erişilebilirlik:** WCAG 2.1 **AA** hedefi.

### Tasarım Dili (Design Tokens)
- **Renk:** marka `primary` + nötr gri skalası + anlamsal renkler (success/warning/danger/info). Tek kaynak: Tailwind token'ları.
- **Tipografi:** okunabilir sans-serif (örn. **Inter**); net tip ölçeği; rakamlar için tabular figürler (fiyat hizalaması).
- **Aralık & ölçü:** 4/8px grid; tutarlı radius, gölge, elevation.
- **Açık + Koyu tema:** POS açık, **KDS koyu** (mutfakta göz yormaz, yüksek kontrast).
- **İşletme bazlı tema (white-label):** her işletme kendi **logosunu** ve **primary rengini** ayarlardan belirler; müşteri QR ekranı o işletmenin markasıyla görünür. (`settings` ile bağlı.)

### Yüzey Bazlı Tasarım

**POS — Personel (tablet öncelikli, yatay):**
- Büyük dokunma hedefleri (**min 44–48px**), tek elle erişilebilir yerleşim.
- 3 sütun: **sol** kategoriler · **orta** ürün grid'i (renk kodlu, görselli) · **sağ** canlı adisyon + toplam.
- Hızlı miktar +/−, opsiyon seçimi modalda; sık ürünler için "favoriler".
- **Masa planı:** renk durumlu (boş / dolu / ödeme bekliyor / hazır) — bir bakışta salonu oku.
- Büyük "Öde" ve "Hesabı Böl" butonları; servis ücreti/indirim görünür satırlar.

**KDS — Mutfak (duvar ekranı / tablet):**
- **Koyu tema**, yüksek kontrast, uzaktan okunur **büyük font**.
- Sipariş kartları kanban düzeninde: **Yeni → Hazırlanıyor → Hazır**.
- Renk + **süre sayacı** (geciken sipariş kırmızıya döner) — opsiyonlar/notlar belirgin.
- Tek dokunuşla durum ilerletme; dokunma alanları kocaman.

**Müşteri QR — Mobil (kurulumsuz PWA):**
- **3 adımda ödeme:** hesabı gör → ne ödeyeceğini seç (kendi yediğin / eşit böl) → öde.
- Hızlı yüklenir; ilk ekranda büyük net **tutar** ve işletme markası.
- Güven veren ödeme ekranı (kilit ikonu, sağlayıcı logosu); mümkünse Apple/Google Pay.
- **Bahşiş** seçimi tek dokunuş (%5/10/15 / özel / yuvarla); servis ücreti şeffaf gösterilir.
- Minimum form, gereksiz adım yok; dil seçimi (TR/EN) ayara bağlı.

**Menü Admin — Yönetim (masaüstü):**
- Veri yoğun ama temiz tablo/form; sürükle-bırak sıralama, anlık önizleme.
- Ürün + opsiyon grupları yönetimi sade akışta; toplu işlemler.

### Bileşen Kütüphanesi & Geri Bildirim
- **shadcn/ui + Tailwind token**'larıyla ortak set: Button, Modal, Toast, Table, Tabs, Form alanları, Empty/Loading/Error durumları.
- **Durum tasarımı:** skeleton yükleme, optimistic update, yönlendirici boş durumlar, çözüm öneren hata mesajları, **toast** bildirimleri (ör. "Ödeme alındı"), ince mikro-animasyonlar.

### Erişilebilirlik (WCAG AA)
- Kontrast ≥ 4.5:1, dokunma hedefi ≥ 44px, tam klavye erişimi, ARIA etiketleri, görünür odak.
- **Renk tek başına anlam taşımaz** — durum bilgisi ikon + etiketle de verilir.

### Performans Hissi & Dayanıklılık
- Hızlı ilk yükleme (Vite, kod bölme), QR ekranı düşük bağlantıda da açılır.
- POS, kısa internet kopmalarına dayanıklı (kuyruğa al, bağlanınca senkronla) — hedef olarak planlanır.

> **Tasarım süreci:** Önce token'lar + anahtar ekranlar (QR ödeme, POS, KDS, masa planı, menü yönetimi) mockup'lanır; onaylandıktan sonra bileşenler kodlanır.

## 8.2 Responsive & Çoklu Cihaz Stratejisi

Hedef: **tek React kod tabanı, her cihazda düzgün** — masaüstü tarayıcı ve mobil (telefon/tablet) sorunsuz çalışır.

**Cihaz hedefleri (yüzey bazlı):**
| Yüzey | Birincil cihaz | Ayrıca |
|---|---|---|
| POS / Adisyon | Tablet 10" (yatay) | Telefon (garson cebinden), masaüstü |
| KDS (mutfak) | Büyük ekran/TV, tablet (yatay) | — |
| Müşteri QR | Telefon (her tarayıcı) | Tablet, masaüstü |
| Menü yönetimi | Masaüstü | Tablet |

**Yaklaşım:**
- **Mobile-first** CSS + Tailwind breakpoint'leri (`sm/md/lg/xl`); küçükten büyüğe ölçeklenir.
- **Uyarlanır düzen:** POS masaüstü/tablette 3 sütun (kategori · ürün · adisyon) → telefonda tek sütun + sekmeli geçiş. KDS sütun sayısı ekran genişliğine göre 1→4.
- **Dokunma + fare birlikte:** hover'a bağlı olmayan etkileşim, min **44px** dokunma hedefi, swipe/uzun-bas jestleri destekli.
- **PWA:** kurulabilir (ana ekrana ekle), **çevrimdışı dayanıklı** (özellikle POS ve QR); service worker ile statik cache, kuyruğa-al/senkronla.
- **Test matrisi:** iOS Safari, Android Chrome, masaüstü Chrome/Edge/Firefox; küçük telefondan TV'ye farklı çözünürlükler.
- **Oryantasyon:** POS/KDS yatay önerilir ama dikeyde de bozulmaz; QR her oryantasyonda çalışır.
- **Performans:** route bazlı code-splitting, lazy load, görsel optimizasyonu — düşük bağlantıda da hızlı açılış.

## 8.3 Tasarlanan Anahtar Ekranlar

Aşağıdaki ekranlar tasarım dilini somutlaştırmak için taslaklandı (mockup):

1. **Müşteri QR ödeme** (mobil) — kendi yediğini seç / eşit böl, bahşiş, şeffaf hesap, güvenli ödeme.
2. **POS / Adisyon** (tablet) — sol kategoriler · orta ürün grid'i · sağ canlı adisyon; telefonda tek sütun + sekme.
3. **KDS / Mutfak ekranı** (koyu tema) — Yeni → Hazırlanıyor → Hazır kanban'ı, süre sayaçlı kartlar.
4. **Salon / Masa planı** — renk durumlu masalar (boş / dolu / ödeme bekliyor), tutar ve süre rozeti.
5. **Menü yönetimi** (masaüstü) — kategori listesi + ürün tablosu, müsaitlik toggle, opsiyon grupları.

## 9. Geliştirme Yol Haritası (Fazlar)

### Faz 0 — Temel Kurulum
- Monorepo, docker-compose (api + postgres + redis), Alembic, CI iskeleti.
- Auth: kayıt/giriş, JWT, rol bazlı yetki, `Restaurant` + `User` modelleri.
- Tenant dependency: her istekte aktif kiracı çözümleme.

### Faz 1 — Menü Yönetimi
- Kategori & ürün CRUD (admin panel).
- Görsel yükleme, fiyat, müsaitlik (açık/kapalı) yönetimi.
- **Ürün opsiyonları:** ModifierGroup/Modifier CRUD, ürünlere atama (bkz. §6.1).

### Faz 2 — POS (Garson/Kasa)
- Masa listesi & durumları, QR token üretimi.
- Masa açma → sipariş alma (opsiyon seçerek) → ürün ekle/çıkar → hesap görüntüleme.
- **Servis ücreti/kuver** ayarı ve otomatik uygulanması (bkz. §6.2).
- **İndirim & kampanya:** satır/hesap bazlı indirim (% veya tutar), kupon kodu.
- Nakit/kart ile hesap kapatma (manuel ödeme kaydı), nakit bahşiş girişi.

### Faz 3 — Mutfak Ekranı (KDS) + Gerçek Zamanlı
- WebSocket altyapısı + Redis pub/sub.
- Siparişlerin mutfağa canlı düşmesi; `new → preparing → ready → served`.

### Faz 4 — QR Müşteri Ödeme + Online Ödeme
- QR ile masa hesabı görüntüleme (mobil web).
- Kalem seçerek / eşit bölerek ödeme; kilitleme mantığı.
- **Bahşiş seçimi** (oran / özel tutar / yuvarlama) ödeme ekranında (bkz. §6.2).
- **Garson çağır / hesap iste** butonu — QR'dan POS'a anlık bildirim.
- iyzico/PayTR entegrasyonu + webhook doğrulama.

### Faz 4.5 — QR'dan Sipariş (opsiyon, varsayılan kapalı)
- `settings.self_order_enabled` açıkken QR ekranında menüden sipariş verme.
- Opsiyon seçimi, sepet, siparişin doğrudan KDS'ye düşmesi.
- Altyapı MVP'de kurulur; işletme panelinden aç/kapat.

### Faz 5 — Raporlama, Panel & Gün Sonu
- Günlük/haftalık satış özeti, ürün bazlı satış, ödeme yöntemi dağılımı.
- Basit dashboard (ciro, masa devir hızı, bahşiş/servis ayrımı).
- **Gün sonu / Z-raporu benzeri özet + kasa devri:** vardiya açılış-kapanış, nakit sayım mutabakatı.

### Faz 5.5 — Online Sipariş Platformu Entegrasyonu (opsiyon)
- `MarketplaceProvider` soyutlaması; aggregator veya doğrudan API.
- Sipariş injection → otomatik adisyon + KDS; onay/red + durum güncelleme.
- Menü senkronu (ürün/fiyat/müsaitlik) ve kanal bazlı fiyat.
- POS/KDS'te kanal rozeti; işletme panelinden platform bağlama.

### Faz 6 — Yasal & İleri Özellikler (sonra)
- ÖKC/yazarkasa entegrasyonu, e-fatura/e-arşiv.
- Çoklu şube, personel vardiya/yetki detayları, sadakat/kupon, garson çağırma.

---

## 10. Güvenlik & Önemli Hususlar

- **Kiracı izolasyonu:** her sorguda `restaurant_id` zorunlu; testlerle çapraz-kiracı sızıntısı kontrol edilir.
- **QR token güvenliği:** masa token'ı tahmin edilemez (uzun random); ödeme oturumu kısa ömürlü token ile yetkilendirilir (müşteri tüm sisteme erişemez, sadece o masanın hesabına).
- **Ödeme güvenliği:** kart bilgisi backend'de saklanmaz; ödeme sağlayıcının hosted page/iframe'i kullanılır (PCI yükü sağlayıcıda). Tutar doğrulama yalnızca **webhook** ile yapılır, frontend'e güvenilmez.
- **Atomiklik:** ödeme ve kalem durum güncellemeleri tek transaction; race condition'a karşı kilit.
- **Idempotency:** ödeme webhook'ları idempotent işlenir (çift bildirim sorun yaratmaz).
- **Rate limiting & loglama:** QR uçları için oran sınırı; denetim logu (kim neyi kapattı).

---

## 11. Açık Sorular / Sonraki Adımda Netleşecekler

1. **Ödeme sağlayıcı:** iyzico mı PayTR mı? (komisyon, entegrasyon kolaylığı, başvuru süreci farklı)
2. **Çoklu şube** ihtiyacı var mı (bir restoran zinciri)? — şimdilik tek şube varsayıldı.
3. **Müşteri hesabı** gerekli mi, yoksa QR ödeme tamamen anonim mi? (anonim öneriliyor)
4. **Online sipariş entegrasyonu** doğrudan platform API'leri ile mi, yoksa **aggregator/middleware** ile mi yapılsın? (aggregator daha hızlı; partner onay süreçleri farklı)

> Karara bağlananlar: ✅ Ürün opsiyonları (§6.1), ✅ bahşiş/servis ücreti (§6.2),
> ✅ garson çağır + indirim/kampanya + gün sonu/kasa devri MVP'de,
> ✅ QR'dan sipariş işletme bazlı opsiyon (varsayılan kapalı),
> ✅ online sipariş platformu (Yemeksepeti/Getir/Trendyol) entegrasyonu işletme bazlı opsiyon (§6.4) olarak plana eklendi.

---

## 12. Önerilen İlk Adım

Faz 0'ı başlatmak: monorepo iskeleti + docker-compose + auth + `Restaurant`/`User` modelleri + tenant dependency. Onay verirsen bu iskeleti kurmaya başlayabilirim.
