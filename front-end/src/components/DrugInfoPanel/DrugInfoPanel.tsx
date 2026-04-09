'use client';
import { useState } from 'react';
import { FDAInfo } from '@/types';
import Badge from '@/components/Badge/Badge';
import styles from './DrugInfoPanel.module.css';

interface DrugInfoPanelProps {
  brandName?: string;
  fdaInfo?: FDAInfo | null;
}

const TRUNCATE = 300;

function ExpandableText({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  if (text.length <= TRUNCATE) return <p className={styles.sectionText}>{text}</p>;
  return (
    <div>
      <p className={styles.sectionText}>
        {expanded ? text : `${text.slice(0, TRUNCATE)}…`}
      </p>
      <button className={styles.expandBtn} onClick={() => setExpanded((v) => !v)}>
        {expanded ? '▲ Ẩn bớt' : '▼ Xem thêm'}
      </button>
    </div>
  );
}

export default function DrugInfoPanel({ brandName, fdaInfo }: DrugInfoPanelProps) {
  if (!brandName || !fdaInfo) {
    return (
      <aside className={styles.panel} aria-label="Drug information panel">
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🔍</div>
          <p className={styles.emptyTitle}>Thông tin thuốc</p>
          <p className={styles.emptySubtitle}>
            Nhập tên thuốc để xem thông tin chi tiết từ OpenFDA
          </p>
        </div>
      </aside>
    );
  }

  return (
    <aside className={styles.panel} aria-label={`Drug info: ${brandName}`}>
      {/* Header */}
      <div className={styles.header}>
        <p className={styles.panelTitle}>Thông tin thuốc gốc</p>
        <div className={styles.drugHeader}>
          <h2 className={styles.drugName}>{brandName}</h2>
          <Badge variant="danger" label="Hết hàng" size="sm" />
        </div>
        <div className={styles.metaChips}>
          <span className={styles.metaChip}>
            <span>💊</span> {fdaInfo.Hoat_Chat}
          </span>
          <span className={styles.metaChip}>
            <span>🚦</span> {fdaInfo.Duong_Dung}
          </span>
        </div>
      </div>

      {/* Scrollable sections */}
      <div className={styles.content}>
        {/* Contraindications — HIGH PRIORITY */}
        <section className={styles.section}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionIcon}>⛔</span>
            <span className={styles.sectionLabel}>Chống chỉ định</span>

          </div>
          <div className={`${styles.sectionText} ${styles.danger}`}>
            {fdaInfo.Chong_Chi_Dinh}
          </div>
        </section>

        {/* Side effects */}
        <section className={styles.section}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionIcon}>⚠️</span>
            <span className={styles.sectionLabel}>Tác dụng phụ</span>

          </div>
          <ExpandableText text={fdaInfo.Tac_Dung_Phu} />
        </section>

        {/* Indications */}
        <section className={styles.section}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionIcon}>📋</span>
            <span className={styles.sectionLabel}>Chỉ định</span>

          </div>
          <ExpandableText text={fdaInfo.Chi_Dinh} />
        </section>
      </div>
    </aside>
  );
}
