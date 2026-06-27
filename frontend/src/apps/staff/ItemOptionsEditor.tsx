import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";

import { type Modifier, type ModifierGroup, modifiersApi } from "@shared/api/modifiers";
import { Button } from "@shared/ui/Button";

/** Ürünün opsiyon gruplarını ürün düzenleme formunun içinde yönetir. */
export function ItemOptionsEditor({ itemId }: { itemId: string }) {
  const qc = useQueryClient();
  const key = ["item-groups", itemId];
  const { data: groups = [], isLoading } = useQuery({
    queryKey: key,
    queryFn: () => modifiersApi.itemGroups(itemId),
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: key });

  const [name, setName] = useState("");
  const [type, setType] = useState<"single" | "multiple">("single");
  const [required, setRequired] = useState(false);

  const addGroup = useMutation({
    mutationFn: async () => {
      const g = await modifiersApi.createGroup({
        name: name.trim(),
        selection_type: type,
        is_required: required,
        min_select: required ? 1 : 0,
        max_select: type === "single" ? 1 : 99,
        modifiers: [],
      });
      await modifiersApi.assignGroups(itemId, [...groups.map((x) => x.id), g.id]);
    },
    onSuccess: () => {
      invalidate();
      setName("");
      setRequired(false);
    },
  });

  const onAddGroup = (e: FormEvent) => {
    e.preventDefault();
    addGroup.mutate();
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <h4 className="mb-2 text-sm font-semibold text-slate-700">
        Seçenekler (Boy, Süt tipi, Ekstralar…)
      </h4>

      {isLoading ? (
        <p className="text-sm text-slate-400">Yükleniyor…</p>
      ) : (
        groups.map((g) => <GroupEditor key={g.id} group={g} onChange={invalidate} />)
      )}

      <form
        onSubmit={onAddGroup}
        className="mt-2 flex flex-wrap items-center gap-2 rounded-lg border border-dashed border-slate-300 bg-white p-2"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Yeni grup adı (örn. Boy)"
          className="min-w-36 flex-1 rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <div className="grid grid-cols-2 gap-1 rounded-lg bg-slate-100 p-0.5">
          {(
            [
              ["single", "Tek"],
              ["multiple", "Çoklu"],
            ] as const
          ).map(([t, label]) => (
            <button
              key={t}
              type="button"
              onClick={() => setType(t)}
              className={[
                "rounded-md px-2 py-1 text-xs font-medium",
                type === t ? "bg-white text-brand-700 shadow-sm" : "text-slate-500",
              ].join(" ")}
            >
              {label}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-1 text-xs text-slate-600">
          <input
            type="checkbox"
            checked={required}
            onChange={(e) => setRequired(e.target.checked)}
            className="h-3.5 w-3.5"
          />
          Zorunlu
        </label>
        <Button
          type="submit"
          variant="secondary"
          loading={addGroup.isPending}
          disabled={!name.trim()}
        >
          Grup Ekle
        </Button>
      </form>
    </div>
  );
}

function GroupEditor({ group, onChange }: { group: ModifierGroup; onChange: () => void }) {
  const [mName, setMName] = useState("");
  const [mPrice, setMPrice] = useState("");

  // Grup düzenleme
  const [editingGroup, setEditingGroup] = useState(false);
  const [gName, setGName] = useState(group.name);
  const [gType, setGType] = useState<"single" | "multiple">(group.selection_type);
  const [gReq, setGReq] = useState(group.is_required);

  const addMod = useMutation({
    mutationFn: () =>
      modifiersApi.addModifier(group.id, {
        name: mName.trim(),
        price_delta: Number(mPrice) || 0,
      }),
    onSuccess: () => {
      onChange();
      setMName("");
      setMPrice("");
    },
  });
  const delGroup = useMutation({
    mutationFn: () => modifiersApi.deleteGroup(group.id),
    onSuccess: onChange,
  });
  const updGroup = useMutation({
    mutationFn: () =>
      modifiersApi.updateGroup(group.id, {
        name: gName.trim(),
        selection_type: gType,
        is_required: gReq,
        min_select: gReq ? 1 : 0,
        max_select: gType === "single" ? 1 : 99,
      }),
    onSuccess: () => {
      onChange();
      setEditingGroup(false);
    },
  });

  return (
    <div className="mb-2 rounded-lg border border-slate-200 bg-white p-2.5">
      {editingGroup ? (
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <input
            value={gName}
            onChange={(e) => setGName(e.target.value)}
            className="min-w-32 flex-1 rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <div className="grid grid-cols-2 gap-1 rounded-lg bg-slate-100 p-0.5">
            {(
              [
                ["single", "Tek"],
                ["multiple", "Çoklu"],
              ] as const
            ).map(([t, label]) => (
              <button
                key={t}
                type="button"
                onClick={() => setGType(t)}
                className={[
                  "rounded-md px-2 py-1 text-xs font-medium",
                  gType === t ? "bg-white text-brand-700 shadow-sm" : "text-slate-500",
                ].join(" ")}
              >
                {label}
              </button>
            ))}
          </div>
          <label className="flex items-center gap-1 text-xs text-slate-600">
            <input
              type="checkbox"
              checked={gReq}
              onChange={(e) => setGReq(e.target.checked)}
              className="h-3.5 w-3.5"
            />
            Zorunlu
          </label>
          <button
            type="button"
            onClick={() => updGroup.mutate()}
            disabled={!gName.trim() || updGroup.isPending}
            className="text-xs font-medium text-brand-600 hover:underline disabled:opacity-50"
          >
            kaydet
          </button>
          <button
            type="button"
            onClick={() => setEditingGroup(false)}
            className="text-xs text-slate-400 hover:underline"
          >
            iptal
          </button>
        </div>
      ) : (
        <div className="mb-1.5 flex items-center justify-between">
          <div>
            <span className="text-sm font-medium text-slate-800">{group.name}</span>
            <span className="ml-2 text-xs text-slate-400">
              {group.selection_type === "single" ? "tek" : "çoklu"}
              {group.is_required && " · zorunlu"}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setGName(group.name);
                setGType(group.selection_type);
                setGReq(group.is_required);
                setEditingGroup(true);
              }}
              className="text-xs text-slate-500 hover:underline"
            >
              düzenle
            </button>
            <button
              type="button"
              onClick={() => delGroup.mutate()}
              className="text-xs text-red-500 hover:underline"
            >
              sil
            </button>
          </div>
        </div>
      )}

      <ul className="mb-1.5 space-y-1">
        {group.modifiers.map((m) => (
          <ModifierRow key={m.id} modifier={m} onChange={onChange} />
        ))}
        {group.modifiers.length === 0 && (
          <li className="text-xs text-slate-400">Henüz seçenek yok.</li>
        )}
      </ul>

      <div className="flex items-center gap-1.5">
        <input
          value={mName}
          onChange={(e) => setMName(e.target.value)}
          placeholder="Seçenek (örn. Büyük)"
          className="flex-1 rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <input
          type="number"
          value={mPrice}
          onChange={(e) => setMPrice(e.target.value)}
          placeholder="₺"
          className="w-20 rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <Button
          type="button"
          variant="secondary"
          loading={addMod.isPending}
          disabled={!mName.trim()}
          onClick={() => addMod.mutate()}
        >
          Ekle
        </Button>
      </div>
    </div>
  );
}

function ModifierRow({ modifier, onChange }: { modifier: Modifier; onChange: () => void }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(modifier.name);
  const [price, setPrice] = useState(String(Number(modifier.price_delta)));

  const upd = useMutation({
    mutationFn: () =>
      modifiersApi.updateModifier(modifier.id, {
        name: name.trim(),
        price_delta: Number(price) || 0,
      }),
    onSuccess: () => {
      onChange();
      setEditing(false);
    },
  });
  const del = useMutation({
    mutationFn: () => modifiersApi.deleteModifier(modifier.id),
    onSuccess: onChange,
  });

  if (editing) {
    return (
      <li className="flex items-center gap-1.5 rounded bg-white px-1 py-1">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <input
          type="number"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          placeholder="₺"
          className="w-20 rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          type="button"
          onClick={() => upd.mutate()}
          disabled={!name.trim() || upd.isPending}
          className="text-xs font-medium text-brand-600 hover:underline disabled:opacity-50"
        >
          kaydet
        </button>
        <button
          type="button"
          onClick={() => setEditing(false)}
          className="text-xs text-slate-400 hover:underline"
        >
          iptal
        </button>
      </li>
    );
  }

  return (
    <li className="flex items-center justify-between rounded bg-slate-50 px-2 py-1 text-sm">
      <span className="text-slate-700">{modifier.name}</span>
      <span className="flex items-center gap-2">
        <span className="text-xs text-slate-500">
          {Number(modifier.price_delta) === 0
            ? "ücretsiz"
            : `${Number(modifier.price_delta) > 0 ? "+" : ""}₺${Number(modifier.price_delta)}`}
        </span>
        <button
          type="button"
          onClick={() => {
            setName(modifier.name);
            setPrice(String(Number(modifier.price_delta)));
            setEditing(true);
          }}
          className="text-xs text-slate-400 hover:underline"
        >
          düzenle
        </button>
        <button
          type="button"
          onClick={() => del.mutate()}
          className="text-xs text-red-400 hover:underline"
        >
          sil
        </button>
      </span>
    </li>
  );
}
