import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { menuApi } from "@shared/api/menu";
import { uploadImage } from "@shared/api/uploads";
import { ApiError } from "@shared/api/client";
import type { MenuCategory, MenuItem } from "@shared/types";
import { Button } from "@shared/ui/Button";
import { Card } from "@shared/ui/Card";
import { Input } from "@shared/ui/Input";

import { ItemOptionsEditor } from "./ItemOptionsEditor";

// ── Kategori Formu ────────────────────────────────────────────────────────────

function CategoryForm({
  initial,
  onSubmit,
  onCancel,
  loading,
}: {
  initial?: Partial<MenuCategory>;
  onSubmit: (name: string) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(name);
      }}
    >
      <Input
        label=""
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Kategori adı"
        required
        minLength={1}
        className="flex-1"
      />
      <Button type="submit" loading={loading} className="self-end">
        {initial?.id ? "Kaydet" : "Ekle"}
      </Button>
      <Button type="button" onClick={onCancel} className="self-end bg-slate-200 text-slate-700 hover:bg-slate-300">
        İptal
      </Button>
    </form>
  );
}

// ── Ürün Formu ────────────────────────────────────────────────────────────────

function ItemForm({
  categories,
  initial,
  onSubmit,
  onCancel,
  loading,
}: {
  categories: MenuCategory[];
  initial?: Partial<MenuItem>;
  onSubmit: (data: {
    category_id: string;
    name: string;
    description: string;
    price: number;
    image_url: string;
  }) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [categoryId, setCategoryId] = useState(initial?.category_id ?? categories[0]?.id ?? "");
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [price, setPrice] = useState(initial?.price ?? "");
  const [imageUrl, setImageUrl] = useState(initial?.image_url ?? "");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      const url = await uploadImage(file);
      setImageUrl(url);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Görsel yüklenemedi");
    } finally {
      setUploading(false);
    }
  };

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          category_id: categoryId,
          name,
          description,
          price: parseFloat(price as string),
          image_url: imageUrl,
        });
      }}
    >
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-700">Kategori</label>
        <select
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          required
          className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <Input
        label="Ürün adı"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Ürün adı"
        required
      />
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-700">Açıklama</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="İsteğe bağlı açıklama"
          rows={2}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        />
      </div>
      <Input
        label="Fiyat (₺)"
        type="number"
        min="0.01"
        step="0.01"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
        placeholder="0.00"
        required
      />
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-700">Görsel</label>
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        {imageUrl ? (
          <div className="relative">
            <img
              src={imageUrl}
              alt="Önizleme"
              className="h-32 w-full rounded-lg object-cover"
            />
            <div className="mt-2 flex gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => fileRef.current?.click()}
                loading={uploading}
              >
                Değiştir
              </Button>
              <Button
                type="button"
                onClick={() => setImageUrl("")}
                className="bg-red-50 text-red-600 hover:bg-red-100"
              >
                Kaldır
              </Button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="flex h-32 w-full flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-slate-300 text-slate-400 transition-colors hover:border-brand-400 hover:text-brand-600 disabled:opacity-60"
          >
            {uploading ? (
              <span className="text-sm">Yükleniyor…</span>
            ) : (
              <>
                <span className="text-2xl">📷</span>
                <span className="text-sm">Bilgisayardan görsel seç</span>
                <span className="text-xs text-slate-400">JPEG/PNG/WEBP/GIF · max 5 MB</span>
              </>
            )}
          </button>
        )}
        {uploadError && <span className="text-xs text-red-600">{uploadError}</span>}
      </div>
      <div className="flex gap-2">
        <Button type="submit" loading={loading}>
          {initial?.id ? "Kaydet" : "Ekle"}
        </Button>
        <Button type="button" onClick={onCancel} className="bg-slate-200 text-slate-700 hover:bg-slate-300">
          İptal
        </Button>
      </div>
    </form>
  );
}

// ── Ana Sayfa ─────────────────────────────────────────────────────────────────

export function MenuPage() {
  const qc = useQueryClient();

  const { data: categories = [], isLoading: catLoading } = useQuery({
    queryKey: ["menu-categories"],
    queryFn: menuApi.listCategories,
  });

  const { data: items = [], isLoading: itemLoading } = useQuery({
    queryKey: ["menu-items"],
    queryFn: menuApi.listItems,
  });

  const [selectedCatId, setSelectedCatId] = useState<string | null>(null);
  const [showCatForm, setShowCatForm] = useState(false);
  const [editCat, setEditCat] = useState<MenuCategory | null>(null);
  const [showItemForm, setShowItemForm] = useState(false);
  const [editItem, setEditItem] = useState<MenuItem | null>(null);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["menu-categories"] });
    qc.invalidateQueries({ queryKey: ["menu-items"] });
  };

  const createCat = useMutation({
    mutationFn: (name: string) => menuApi.createCategory({ name }),
    onSuccess: () => { invalidate(); setShowCatForm(false); },
  });

  const updateCat = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      menuApi.updateCategory(id, { name }),
    onSuccess: () => { invalidate(); setEditCat(null); },
  });

  const deleteCat = useMutation({
    mutationFn: menuApi.deleteCategory,
    onSuccess: () => { invalidate(); setSelectedCatId(null); },
  });

  const toggleCat = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      menuApi.updateCategory(id, { is_active }),
    onSuccess: invalidate,
  });

  const createItem = useMutation({
    mutationFn: menuApi.createItem,
    onSuccess: (newItem) => {
      invalidate();
      setShowItemForm(false);
      // Ürün oluşturulunca düzenleme moduna geç → opsiyonlar aynı yerde eklenir.
      setEditItem(newItem);
    },
  });

  const updateItem = useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Parameters<typeof menuApi.updateItem>[1]) =>
      menuApi.updateItem(id, data),
    onSuccess: () => { invalidate(); setEditItem(null); },
  });

  const deleteItem = useMutation({
    mutationFn: menuApi.deleteItem,
    onSuccess: invalidate,
  });

  const toggleItem = useMutation({
    mutationFn: ({ id, is_available }: { id: string; is_available: boolean }) =>
      menuApi.updateItem(id, { is_available }),
    onSuccess: invalidate,
  });

  const visibleItems = selectedCatId
    ? items.filter((i) => i.category_id === selectedCatId)
    : items;

  if (catLoading || itemLoading) {
    return <div className="p-8 text-slate-500">Yükleniyor…</div>;
  }

  return (
    <div className="flex h-full gap-4 p-4">
      {/* Sol: Kategoriler */}
      <div className="flex w-64 shrink-0 flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-slate-800">Kategoriler</h2>
          {!showCatForm && (
            <button
              onClick={() => setShowCatForm(true)}
              className="text-sm text-brand-600 hover:underline"
            >
              + Ekle
            </button>
          )}
        </div>

        {showCatForm && (
          <Card className="p-3">
            <CategoryForm
              onSubmit={(name) => createCat.mutate(name)}
              onCancel={() => setShowCatForm(false)}
              loading={createCat.isPending}
            />
          </Card>
        )}

        <div className="flex flex-col gap-1">
          <button
            onClick={() => setSelectedCatId(null)}
            className={[
              "rounded-lg px-3 py-2 text-left text-sm transition-colors",
              selectedCatId === null
                ? "bg-brand-600 text-white"
                : "text-slate-700 hover:bg-slate-100",
            ].join(" ")}
          >
            Tümü ({items.length})
          </button>

          {categories.map((cat) =>
            editCat?.id === cat.id ? (
              <Card key={cat.id} className="p-2">
                <CategoryForm
                  initial={cat}
                  onSubmit={(name) => updateCat.mutate({ id: cat.id, name })}
                  onCancel={() => setEditCat(null)}
                  loading={updateCat.isPending}
                />
              </Card>
            ) : (
              <div
                key={cat.id}
                className={[
                  "group flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer transition-colors",
                  selectedCatId === cat.id
                    ? "bg-brand-600 text-white"
                    : "text-slate-700 hover:bg-slate-100",
                  !cat.is_active ? "opacity-50" : "",
                ].join(" ")}
                onClick={() => setSelectedCatId(cat.id)}
              >
                <span className="text-sm truncate">{cat.name}</span>
                <div className="hidden gap-1 group-hover:flex" onClick={(e) => e.stopPropagation()}>
                  <button
                    title="Düzenle"
                    onClick={() => setEditCat(cat)}
                    className="rounded p-0.5 hover:bg-black/10"
                  >
                    ✏️
                  </button>
                  <button
                    title={cat.is_active ? "Gizle" : "Göster"}
                    onClick={() => toggleCat.mutate({ id: cat.id, is_active: !cat.is_active })}
                    className="rounded p-0.5 hover:bg-black/10"
                  >
                    {cat.is_active ? "👁" : "🚫"}
                  </button>
                  <button
                    title="Sil"
                    onClick={() => {
                      if (confirm(`"${cat.name}" kategorisini ve tüm ürünlerini sil?`)) {
                        deleteCat.mutate(cat.id);
                      }
                    }}
                    className="rounded p-0.5 hover:bg-black/10"
                  >
                    🗑
                  </button>
                </div>
              </div>
            )
          )}
        </div>
      </div>

      {/* Sağ: Ürünler */}
      <div className="flex flex-1 flex-col gap-3 overflow-auto">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-slate-800">
            Ürünler{selectedCatId ? ` — ${categories.find((c) => c.id === selectedCatId)?.name}` : ""}
            <span className="ml-2 text-sm font-normal text-slate-400">({visibleItems.length})</span>
          </h2>
          {!showItemForm && categories.length > 0 && (
            <Button onClick={() => setShowItemForm(true)}>+ Ürün Ekle</Button>
          )}
        </div>

        {showItemForm && (
          <Card className="p-4">
            <h3 className="mb-3 font-medium text-slate-700">Yeni Ürün</h3>
            <ItemForm
              categories={categories}
              initial={selectedCatId ? { category_id: selectedCatId } : undefined}
              onSubmit={(data) => createItem.mutate(data)}
              onCancel={() => setShowItemForm(false)}
              loading={createItem.isPending}
            />
          </Card>
        )}

        {editItem && (
          <Card className="p-4">
            <h3 className="mb-3 font-medium text-slate-700">Ürünü Düzenle</h3>
            <ItemForm
              categories={categories}
              initial={editItem}
              onSubmit={(data) => updateItem.mutate({ id: editItem.id, ...data })}
              onCancel={() => setEditItem(null)}
              loading={updateItem.isPending}
            />
            <div className="mt-4 border-t border-slate-100 pt-4">
              <ItemOptionsEditor itemId={editItem.id} />
            </div>
          </Card>
        )}

        {visibleItems.length === 0 && !showItemForm && (
          <div className="flex flex-1 items-center justify-center text-slate-400">
            {categories.length === 0
              ? "Önce bir kategori ekleyin."
              : "Bu kategoride ürün yok."}
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {visibleItems.map((item) => (
            <Card key={item.id} className={["overflow-hidden flex flex-col", !item.is_available ? "opacity-50" : ""].join(" ")}>
              {item.image_url ? (
                <img
                  src={item.image_url}
                  alt={item.name}
                  className="h-32 w-full object-cover"
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src =
                      "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect fill='%23f1f5f9' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' fill='%2394a3b8' font-size='20' text-anchor='middle' dy='.3em'%3EGörsel yok%3C/text%3E%3C/svg%3E";
                  }}
                />
              ) : (
                <div className="flex h-32 w-full items-center justify-center bg-slate-100 text-xs text-slate-400">
                  Görsel yok
                </div>
              )}
              <div className="flex flex-col gap-2 p-4 flex-1">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800 truncate">{item.name}</p>
                  {item.description && (
                    <p className="text-xs text-slate-500 line-clamp-2">{item.description}</p>
                  )}
                  <p className="mt-1 text-sm font-semibold text-brand-700">
                    ₺{parseFloat(item.price).toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-400">
                    {categories.find((c) => c.id === item.category_id)?.name}
                  </p>
                </div>
              </div>
              <div className="flex gap-1 mt-auto">
                <button
                  onClick={() => toggleItem.mutate({ id: item.id, is_available: !item.is_available })}
                  className="flex-1 rounded-lg border border-slate-200 py-1 text-xs hover:bg-slate-50 transition-colors"
                >
                  {item.is_available ? "Aktif" : "Pasif"}
                </button>
                <button
                  onClick={() => { setEditItem(item); setShowItemForm(false); }}
                  className="rounded-lg border border-slate-200 px-2 py-1 text-xs hover:bg-slate-50 transition-colors"
                >
                  Düzenle
                </button>
                <button
                  onClick={() => {
                    if (confirm(`"${item.name}" ürününü sil?`)) deleteItem.mutate(item.id);
                  }}
                  className="rounded-lg border border-red-200 px-2 py-1 text-xs text-red-600 hover:bg-red-50 transition-colors"
                >
                  Sil
                </button>
              </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
