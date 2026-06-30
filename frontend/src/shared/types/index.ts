export type UserRole = "owner" | "manager" | "cashier" | "waiter";

export interface User {
  id: string;
  restaurant_id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Restaurant {
  id: string;
  name: string;
  slug: string;
  plan: string;
  settings: Record<string, unknown>;
  features: Record<string, boolean>;
  created_at: string;
}

// ── Platform admin paneli ────────────────────────────────────────────────────

export interface PlatformAdmin {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminTokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AdminAuthResponse extends AdminTokenPair {
  admin: PlatformAdmin;
}

export interface FeatureCatalogItem {
  key: string;
  label: string;
  description: string;
}

export interface AdminRestaurant {
  id: string;
  name: string;
  slug: string;
  plan: string;
  settings: Record<string, unknown>;
  features: Record<string, boolean>;
  user_count: number;
  owner_email: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse extends TokenPair {
  user: User;
}

export interface RegisterPayload {
  restaurant_name: string;
  owner_name: string;
  email: string;
  password: string;
  slug?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface MenuCategory {
  id: string;
  restaurant_id: string;
  name: string;
  sort_order: number;
  is_active: boolean;
}

export interface MenuItem {
  id: string;
  restaurant_id: string;
  category_id: string;
  name: string;
  description: string | null;
  price: string;
  image_url: string | null;
  is_available: boolean;
  sort_order: number;
}

export interface MenuCategoryCreate {
  name: string;
  sort_order?: number;
  is_active?: boolean;
}

export interface MenuItemCreate {
  category_id: string;
  name: string;
  description?: string;
  price: number;
  image_url?: string;
  is_available?: boolean;
  sort_order?: number;
}

// ── Masa & Sipariş ─────────────────────────────────────────────────────────

export interface TableWithStatus {
  id: string;
  restaurant_id: string;
  name: string;
  sort_order: number;
  qr_token: string;
  status: "empty" | "occupied";
  active_order_id: string | null;
  active_total: number;
  active_paid_total: number;
}

export type PaidStatus = "unpaid" | "locked" | "paid";

export interface OrderItemModifier {
  id: string;
  name_snapshot: string;
  price_delta_snapshot: string;
}

export interface OrderItem {
  id: string;
  menu_item_id: string | null;
  name_snapshot: string;
  unit_price: string;
  quantity: number;
  line_total: string;
  note: string | null;
  paid_status: PaidStatus;
  modifiers: OrderItemModifier[];
}

export type KitchenStatus = "new" | "preparing" | "ready" | "served";

export interface KdsItem {
  id: string;
  name_snapshot: string;
  quantity: number;
  note: string | null;
  kitchen_status: KitchenStatus;
}

export interface KdsTicket {
  order_id: string;
  table_name: string | null;
  source: string;
  opened_at: string;
  items: KdsItem[];
}

export type OrderStatus = "open" | "paid" | "closed";

export interface WaiterCall {
  id: string;
  table_id: string;
  table_name: string | null;
  status: "pending" | "resolved";
  note: string | null;
  created_at: string;
  resolved_at: string | null;
}

// ── İşletme ana sayfası özeti ────────────────────────────────────────────────

export interface ActiveOrderSummary {
  order_id: string;
  table_id: string | null;
  table_name: string | null;
  source: string;
  total: number;
  paid_total: number;
  remaining: number;
  opened_at: string;
}

export interface DashboardSummary {
  total_tables: number;
  occupied_tables: number;
  empty_tables: number;
  active_orders: number;
  open_total: number;
  open_paid: number;
  open_remaining: number;
  today_revenue: number;
  today_tips: number;
  today_payments: number;
  active_order_list: ActiveOrderSummary[];
}

export interface Order {
  id: string;
  restaurant_id: string;
  table_id: string | null;
  source: string;
  status: OrderStatus;
  subtotal: string;
  discount_amount: string;
  service_charge_rate: string;
  service_charge_amount: string;
  total: string;
  paid_total: string;
  opened_at: string;
  closed_at: string | null;
  items: OrderItem[];
}
