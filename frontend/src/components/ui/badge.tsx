import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[var(--orange-dim)] text-[var(--orange)] border border-[var(--orange)]/20",
        cyan: "bg-[var(--cyan-dim,rgba(0,229,255,0.1))] text-[var(--cyan)] border border-[var(--cyan)]/20",
        green: "bg-[rgba(0,255,135,0.1)] text-[var(--green)] border border-[var(--green)]/20",
        amber: "bg-[rgba(255,171,0,0.1)] text-[var(--amber)] border border-[var(--amber)]/20",
        muted: "bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
