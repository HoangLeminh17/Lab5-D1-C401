'use client';
import styles from './Badge.module.css';

type BadgeVariant =
  | 'equivalent' | 'alternative' | 'fallback'
  | 'success' | 'warning' | 'danger' | 'info' | 'neutral';

type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  label: string;
  showDot?: boolean;
}

export default function Badge({ variant = 'neutral', size = 'md', label, showDot = true }: BadgeProps) {
  const cls = [
    styles.badge,
    styles[variant],
    size !== 'md' ? styles[size] : '',
  ].filter(Boolean).join(' ');

  return (
    <span className={cls}>
      {showDot && <span className={styles.dot} aria-hidden="true" />}
      {label}
    </span>
  );
}
