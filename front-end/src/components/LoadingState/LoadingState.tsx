'use client';
import styles from './LoadingState.module.css';

function SkeletonCard() {
  return (
    <div className={styles.skeletonCard}>
      <div className={styles.skeletonRow}>
        <div className={`${styles.block} ${styles.titleBlock}`} />
        <div className={`${styles.block} ${styles.badgeBlock}`} />
      </div>
      <div className={`${styles.block} ${styles.textBlock}`} style={{ width: '40%', marginBottom: 12 }} />
      <div className={`${styles.block} ${styles.barBlock}`} />
      <div className={`${styles.block} ${styles.textBlock}`} style={{ width: '80%', marginTop: 12, marginBottom: 8 }} />
      <div className={`${styles.block} ${styles.btnBlock}`} />
    </div>
  );
}

interface LoadingStateProps {
  count?: number;
  message?: string;
}

export default function LoadingState({ count = 3, message = 'Đang tra cứu FDA và tồn kho…' }: LoadingStateProps) {
  return (
    <div className={styles.container}>
      <div className={styles.spinnerWrap}>
        <div className={styles.spinner} aria-hidden="true" />
        <p className={styles.spinnerText}>{message}</p>
      </div>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
