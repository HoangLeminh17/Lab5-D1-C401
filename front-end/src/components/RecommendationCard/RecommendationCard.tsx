'use client';
import { DrugRecommendation, getStockLevel, getStockLabelVI, getVariantLabel } from '@/types';
import Badge from '@/components/Badge/Badge';
import styles from './RecommendationCard.module.css';

interface RecommendationCardProps {
  rec: DrugRecommendation;
}

const STOCK_BADGE_VARIANT: Record<string, 'success' | 'warning' | 'danger'> = {
  high: 'success', ok: 'success', low: 'warning', out: 'danger',
};

const VARIANT_BADGE: Record<string, 'equivalent' | 'alternative' | 'fallback'> = {
  equivalent: 'equivalent', alternative: 'alternative', fallback: 'fallback',
};

const VARIANT_CARD_CLASS: Record<string, string> = {
  equivalent: styles.equivalent,
  alternative: styles.alternative,
  fallback: styles.fallback,
};

export default function RecommendationCard({ rec }: RecommendationCardProps) {
  const { drug, variant, reason } = rec;
  const stockLevel = getStockLevel(drug.Ton_Kho);

  return (
    <article
      className={`${styles.card} ${VARIANT_CARD_CLASS[variant] ?? ''}`}
      aria-label={`Gợi ý: ${drug.Ten_Thuoc}`}
    >
      {/* Row 1: Drug name (left) — Stock badge (right) */}
      <div className={styles.row1}>
        <h3 className={styles.drugName}>{drug.Ten_Thuoc}</h3>
        <Badge
          variant={STOCK_BADGE_VARIANT[stockLevel]}
          label={getStockLabelVI(stockLevel)}
          size="sm"
        />
      </div>

      {/* Row 2: Variant badge (left) — Ingredient (right) */}
      <div className={styles.row2}>
        <Badge
          variant={VARIANT_BADGE[variant]}
          label={getVariantLabel(variant, 'vi')}
          size="sm"
        />
        <span className={styles.ingredient}>{drug.Hoat_Chat}</span>
      </div>

      {/* Row 3: Stock count */}
      <div className={styles.stockRow}>
        <span className={styles.stockIcon}>📦</span>
        <span>Tồn kho: <strong>{drug.Ton_Kho}</strong> hộp</span>
      </div>

      {/* Reason */}
      <p className={styles.reason}>{reason}</p>
    </article>
  );
}
