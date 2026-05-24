import Link from "next/link";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type ButtonVariant = "default" | "primary" | "ghost";

type BaseProps = {
  children: ReactNode;
  variant?: ButtonVariant;
  className?: string;
};

type ButtonProps = BaseProps & ButtonHTMLAttributes<HTMLButtonElement>;

type ButtonLinkProps = BaseProps &
  AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
  };

export function Button({ children, className, variant = "default", ...props }: ButtonProps) {
  return (
    <button className={cn("button", variant !== "default" && variant, className)} {...props}>
      {children}
    </button>
  );
}

export function ButtonLink({ children, className, variant = "default", href, ...props }: ButtonLinkProps) {
  return (
    <Link className={cn("button", variant !== "default" && variant, className)} href={href} {...props}>
      {children}
    </Link>
  );
}

