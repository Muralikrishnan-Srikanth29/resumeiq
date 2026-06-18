import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed",
        variant === "primary" &&
          "bg-signal text-ink hover:bg-[#ff8064] active:bg-[#e85a3a]",
        variant === "secondary" &&
          "bg-paper-dim text-ink hover:bg-paper border border-line",
        variant === "ghost" &&
          "bg-transparent text-paper hover:bg-white/5 border border-line",
        size === "sm" && "px-3 py-1.5 text-sm",
        size === "md" && "px-5 py-2.5 text-sm",
        size === "lg" && "px-7 py-3.5 text-base",
        className
      )}
      {...props}
    />
  );
}
