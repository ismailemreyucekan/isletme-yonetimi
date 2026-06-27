import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand-700 text-white hover:bg-brand-800 focus-visible:ring-brand-500",
  secondary:
    "bg-white text-slate-800 border border-slate-300 hover:bg-slate-50 focus-visible:ring-slate-400",
  ghost: "bg-transparent text-slate-700 hover:bg-slate-100 focus-visible:ring-slate-300",
  danger: "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-400",
};

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  className = "",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={[
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2",
        "text-sm font-semibold transition-colors",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-60",
        VARIANTS[variant],
        className,
      ].join(" ")}
    >
      {loading && (
        <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  );
}
