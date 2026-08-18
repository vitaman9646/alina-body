import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

export function FadeIn({
  children,
  className = '',
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function Section({
  id,
  children,
  className = '',
}: {
  id?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`px-5 py-20 sm:px-8 md:py-28 ${className}`}>
      <div className="mx-auto w-full max-w-6xl">{children}</div>
    </section>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.28em] text-rose">
      {children}
    </p>
  );
}

const btn =
  'inline-flex items-center justify-center rounded-full px-7 py-3.5 text-[13px] font-medium tracking-[0.02em] transition-all duration-300';

const variants = {
  primary: 'bg-ink text-cream hover:bg-[#2b241f] shadow-[0_10px_30px_-12px_rgba(58,49,44,0.45)]',
  ghost: 'border border-ink/15 bg-transparent text-ink hover:border-ink/35 hover:bg-white/40',
  soft: 'bg-blush text-ink hover:bg-[#ddc4bd]',
};

export function ButtonLink({
  to,
  children,
  variant = 'primary',
  className = '',
}: {
  to: string;
  children: ReactNode;
  variant?: keyof typeof variants;
  className?: string;
}) {
  return (
    <Link to={to} className={`${btn} ${variants[variant]} ${className}`}>
      {children}
    </Link>
  );
}

export function Button({
  children,
  variant = 'primary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: keyof typeof variants }) {
  return (
    <button className={`${btn} ${variants[variant]} disabled:opacity-50 ${className}`} {...props}>
      {children}
    </button>
  );
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-3xl bg-blush/60 ${className}`} />;
}

export function ErrorNote({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-[24px] border border-rose/30 bg-white/70 px-6 py-5 text-sm text-stone">
      <p>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 text-[13px] text-ink underline underline-offset-4">
          Попробовать снова
        </button>
      )}
    </div>
  );
}
