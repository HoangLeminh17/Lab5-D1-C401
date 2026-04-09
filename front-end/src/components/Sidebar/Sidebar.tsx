'use client';
import { ConsultationHistoryItem } from '@/types';
import styles from './Sidebar.module.css';

interface SidebarProps {
  history: ConsultationHistoryItem[];
  onNewConsultation: () => void;
  onSelectHistory?: (item: ConsultationHistoryItem) => void;
}

function formatTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'Vừa xong';
  if (diffMin < 60) return `${diffMin} phút trước`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH} giờ trước`;
  return date.toLocaleDateString('vi-VN');
}

const STATUS_ICON: Record<string, string> = {
  approved: '✅',
  rejected: '❌',
  pending: '⏳',
};

export default function Sidebar({ history, onNewConsultation, onSelectHistory }: SidebarProps) {
  return (
    <nav className={styles.sidebar} aria-label="Sidebar navigation">
      {/* Logo */}
      <div className={styles.logo}>
        <div className={styles.logoInner}>
          <div className={styles.logoIcon}>💊</div>
          <div className={styles.logoText}>
            <p className={styles.logoTitle}>Pharmacist Assistant</p>
            <p className={styles.logoSub}>Trợ lý Dược sĩ AI</p>
          </div>
        </div>
      </div>

      {/* New consultation */}
      <button
        id="new-consultation-btn"
        className={styles.newBtn}
        onClick={onNewConsultation}
        type="button"
      >
        <span>＋</span>
        <span>Tư vấn mới</span>
      </button>

      {/* History */}
      <div className={styles.section}>
        <p className={styles.sectionTitle}>Lịch sử</p>
      </div>

      <div className={styles.historyList}>
        {history.length === 0 ? (
          <p className={styles.emptyHistory}>Chưa có lịch sử tư vấn</p>
        ) : (
          history.slice().reverse().map((item) => (
            <div
              key={item.id}
              className={styles.historyItem}
              onClick={() => onSelectHistory?.(item)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onSelectHistory?.(item)}
              aria-label={`Lịch sử: ${item.brandName}`}
            >
              <span className={styles.historyIcon}>{STATUS_ICON[item.status]}</span>
              <div className={styles.historyInfo}>
                <p className={styles.historyName}>{item.brandName}</p>
                <p className={styles.historyMeta}>{formatTime(item.timestamp)}</p>
              </div>
              <span className={styles.historyCount}>{item.alternativesFound}</span>
            </div>
          ))
        )}
      </div>

      {/* Data sources */}
      <div className={styles.infoSection}>
        <p className={styles.infoTitle}>Nguồn dữ liệu</p>
        <div className={styles.infoRow}>🏥 <span>OpenFDA Drug Labels</span></div>
        <div className={styles.infoRow}>📋 <span>Kho nội bộ (inventory.csv)</span></div>
        <div className={styles.infoRow}>🤖 <span>Google Gemini 2.5</span></div>
      </div>
    </nav>
  );
}
