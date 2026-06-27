import type { HTMLAttributes } from "react";

export function Card({ className = "", ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...rest}
      className={[
        "rounded-2xl border border-slate-200 bg-white shadow-sm",
        className,
      ].join(" ")}
    />
  );
}
