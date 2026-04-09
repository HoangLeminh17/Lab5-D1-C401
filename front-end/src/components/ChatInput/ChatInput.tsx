'use client';
import { useRef, useEffect } from 'react';
import styles from './ChatInput.module.css';

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  isLoading = false,
  placeholder = 'Nhập tên thuốc hết hàng… (ví dụ: Advil, Tylenol, Zithromax)',
  maxLength = 200,
}: ChatInputProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [value]);

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) onSubmit();
    }
  };

  const pct = Math.round((value.length / maxLength) * 100);
  const countCls = [
    styles.charCount,
    pct >= 100 ? styles.atLimit : pct >= 80 ? styles.nearLimit : '',
  ].filter(Boolean).join(' ');

  const canSend = value.trim().length > 0 && !isLoading;

  return (
    <div>
      <div className={styles.wrapper}>
        <div className={styles.inputArea}>
          <textarea
            ref={ref}
            id="drug-search-input"
            className={styles.textarea}
            value={value}
            onChange={(e) => onChange(e.target.value.slice(0, maxLength))}
            onKeyDown={handleKey}
            placeholder={placeholder}
            rows={1}
            disabled={isLoading}
            aria-label="Nhập tên thuốc"
            autoComplete="off"
            spellCheck={false}
          />

          <div className={styles.inputMeta}>
            {value.length > 0 && (
              <button
                type="button"
                className={styles.clearBtn}
                onClick={() => onChange('')}
                aria-label="Clear input"
                title="Xóa"
              >✕</button>
            )}
            <span className={countCls}>{value.length}/{maxLength}</span>
          </div>
        </div>

        <button
          type="button"
          id="send-btn"
          className={styles.sendBtn}
          onClick={onSubmit}
          disabled={!canSend}
          aria-label="Gửi"
          title="Gửi (Enter)"
        >
          {isLoading ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="3" strokeDasharray="40 60" strokeLinecap="round">
                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.8s" repeatCount="indefinite"/>
              </circle>
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </button>
      </div>
      <p className={styles.hint}>Enter để tìm kiếm · Shift+Enter xuống dòng</p>
    </div>
  );
}
