import type { InputHTMLAttributes } from "react";
import { useId } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, error, className = "", ...rest }: InputProps) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={id}
        {...rest}
        className={[
          "min-h-11 rounded-lg border bg-white px-3 py-2 text-sm",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500",
          error ? "border-red-400" : "border-slate-300",
          className,
        ].join(" ")}
      />
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
