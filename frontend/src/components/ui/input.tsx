import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "flex h-12 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-card)] px-4 py-3 text-base text-[var(--text)] placeholder:text-[var(--text-dim)] focus:border-[var(--orange)] focus:outline-none focus:ring-2 focus:ring-[var(--orange-dim)] disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";

export { Input };
