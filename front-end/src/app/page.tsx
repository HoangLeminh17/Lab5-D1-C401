'use client';

import { useState, useEffect, useCallback } from 'react';

import Sidebar from '@/components/Sidebar/Sidebar';
import DrugInfoPanel from '@/components/DrugInfoPanel/DrugInfoPanel';
import RecommendationCard from '@/components/RecommendationCard/RecommendationCard';
import ChatInput from '@/components/ChatInput/ChatInput';
import LoadingState from '@/components/LoadingState/LoadingState';
import { FilterCheckboxGroup } from '@/components/FilterCheckbox/FilterCheckbox';

import {
  ConsultationResult,
  DrugRecommendation,
  FilterState,
  RecommendationVariant,
  buildRecommendations,
} from '@/types';

import styles from './page.module.css';

const EXAMPLE_DRUGS = ['Advil', 'Tylenol', 'Zithromax', 'Nexium', 'Glucophage'];

const VARIANT_OPTIONS = [
  { id: 'equivalent', label: 'Tương đương', colorDot: '#0F766E' },
  { id: 'alternative', label: 'Thay thế',   colorDot: '#F59E0B' },
  { id: 'fallback',    label: 'Dự phòng',   colorDot: '#DC2626' },
];

const STOCK_OPTIONS = [
  { id: 'all',       label: 'Tất cả' },
  { id: 'in_stock',  label: 'Còn hàng', colorDot: '#16A34A' },
  { id: 'low_stock', label: 'Sắp hết',  colorDot: '#D97706' },
];

/** Render markdown text as plain paragraphs — no external deps needed */
function SimpleMarkdown({ text }: { text: string }) {
  const lines = text.split('\n');
  return (
    <div className="markdown-body">
      {lines.map((line, i) => {
        if (line.startsWith('## ')) return <h2 key={i}>{line.slice(3)}</h2>;
        if (line.startsWith('### ')) return <h3 key={i}>{line.slice(4)}</h3>;
        if (line.startsWith('# ')) return <h2 key={i}>{line.slice(2)}</h2>;
        if (line.startsWith('> ')) return <blockquote key={i}>{line.slice(2)}</blockquote>;
        if (line.startsWith('- ') || line.startsWith('* '))
          return <p key={i} style={{ paddingLeft: 16 }}>• {line.slice(2)}</p>;
        if (line.startsWith('---')) return <hr key={i} />;
        if (line.trim() === '') return <br key={i} />;
        // Inline bold: **text**
        const bold = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        return <p key={i} dangerouslySetInnerHTML={{ __html: bold }} />;
      })}
    </div>
  );
}

export default function HomePage() {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ConsultationResult | null>(null);
  const [recommendations, setRecommendations] = useState<DrugRecommendation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [clock, setClock] = useState('');

  const [filters, setFilters] = useState<FilterState>({
    stockFilter: 'all',
    variants: ['equivalent', 'alternative', 'fallback'],
  });

  // Live clock
  useEffect(() => {
    const tick = () =>
      setClock(new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const handleSubmit = useCallback(async () => {
    const query = inputValue.trim();
    if (!query || isLoading) return;

    setIsLoading(true);
    setResult(null);
    setRecommendations([]);
    setError(null);

    try {
      const res = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_name: query }),
      });

      const data: ConsultationResult = await res.json();
      setResult(data);

      if (data.success && data.fda_info) {
        const recs = buildRecommendations(data.alternative_drugs, data.fda_info.Hoat_Chat);
        setRecommendations(recs);
      } else {
        setError(data.error_message || 'Không tìm thấy dữ liệu.');
      }
    } catch {
      setError('Lỗi kết nối. Vui lòng kiểm tra mạng và thử lại.');
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading]);

  const handleNewConsultation = () => {
    setResult(null);
    setRecommendations([]);
    setError(null);
    setInputValue('');
  };

  // Apply filters
  const filtered = recommendations.filter((r) => {
    const variantOk = filters.variants.includes(r.variant);
    let stockOk = true;
    if (filters.stockFilter === 'in_stock')  stockOk = r.drug.Ton_Kho > 30;
    if (filters.stockFilter === 'low_stock') stockOk = r.drug.Ton_Kho > 0 && r.drug.Ton_Kho <= 30;
    return variantOk && stockOk;
  });

  // Count by variant for filter badge counts
  const variantCounts = recommendations.reduce<Record<string, number>>((acc, r) => {
    acc[r.variant] = (acc[r.variant] ?? 0) + 1;
    return acc;
  }, {});

  const variantOptionsWithCount = VARIANT_OPTIONS.map((o) => ({
    ...o,
    count: variantCounts[o.id] ?? 0,
  }));

  const activeFilters = filters.variants.length < 3 || filters.stockFilter !== 'all';

  return (
    <div className={styles.appShell}>
      {/* Left sidebar */}
      <Sidebar
        history={[]}
        onNewConsultation={handleNewConsultation}
        onSelectHistory={() => {}}
      />

      {/* Main column */}
      <main className={styles.main}>
        {/* Top bar */}
        <header className={styles.topBar}>
          <div className={styles.topBarLeft}>
            <h1 className={styles.pageTitle}>
              Gợi ý thuốc thay thế
            </h1>
            <p className={styles.pageSubtitle}>
              Tra cứu OpenFDA · Đối chiếu tồn kho · Tư vấn lâm sàng
            </p>
          </div>
          <div className={styles.topBarRight}>
            <span className={styles.clock}>{clock}</span>
          </div>
        </header>

        {/* Filter bar — only when results are loaded */}
        {recommendations.length > 0 && (
          <div className={styles.filterBar}>
            <span className={styles.filterBarLabel}>Lọc:</span>
            <div className={styles.filterRow}>
              <FilterCheckboxGroup
                groupLabel=""
                options={variantOptionsWithCount}
                selected={filters.variants}
                onChange={(v) =>
                  setFilters((f) => ({ ...f, variants: v as RecommendationVariant[] }))
                }
              />
            </div>
            <div className={styles.filterRow} style={{ marginLeft: 'auto' }}>
              <FilterCheckboxGroup
                groupLabel=""
                options={STOCK_OPTIONS}
                selected={[filters.stockFilter]}
                onChange={(v) => {
                  const last = v[v.length - 1] ?? 'all';
                  setFilters((f) => ({
                    ...f,
                    stockFilter: last as FilterState['stockFilter'],
                  }));
                }}
              />
            </div>
            {activeFilters && (
              <button
                type="button"
                className={styles.clearFiltersBtn}
                onClick={() =>
                  setFilters({ stockFilter: 'all', variants: ['equivalent', 'alternative', 'fallback'] })
                }
              >
                ✕ Xóa lọc
              </button>
            )}
          </div>
        )}

        {/* Scrollable results */}
        <div className={styles.resultsArea}>
          {/* Loading skeleton */}
          {isLoading && <LoadingState count={3} />}

          {/* Error state */}
          {!isLoading && error && (
            <div className={styles.errorBox} role="alert">
              <span className={styles.errorIcon}>❌</span>
              <div>
                <p className={styles.errorTitle}>Không tìm thấy</p>
                <p className={styles.errorMsg}>{error}</p>
              </div>
            </div>
          )}

          {/* Welcome state */}
          {!isLoading && !result && !error && (
            <div className={styles.welcomeState}>
              <div className={styles.welcomeIcon}>💊</div>
              <p className={styles.welcomeTitle}>Nhập tên thuốc hết hàng</p>
              <p className={styles.welcomeSub}>
                Hệ thống sẽ tra cứu OpenFDA, đối chiếu kho nội bộ và gợi ý thuốc thay thế tức thì.
              </p>

              <div className={styles.welcomeExamples}>
                {EXAMPLE_DRUGS.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={styles.exampleChip}
                    onClick={() => setInputValue(d)}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {!isLoading && result?.success && (
            <>
              <div className={styles.resultHeader}>
                <p className={styles.resultTitle}>
                  Thuốc thay thế cho <strong>{result.brand_name}</strong>
                </p>
                <span className={styles.resultCount}>
                  {filtered.length}/{recommendations.length} gợi ý
                </span>
              </div>

              {filtered.length === 0 && recommendations.length > 0 && (
                <div className={styles.errorBox}>
                  <span className={styles.errorIcon}>🔍</span>
                  <div>
                    <p className={styles.errorTitle}>Không có kết quả</p>
                    <p className={styles.errorMsg}>Thử thay đổi bộ lọc</p>
                  </div>
                </div>
              )}

              {recommendations.length === 0 && (
                <div className={styles.errorBox}>
                  <span className={styles.errorIcon}>📭</span>
                  <div>
                    <p className={styles.errorTitle}>Không có thuốc thay thế trong kho</p>
                    <p className={styles.errorMsg}>
                      Không tìm thấy thuốc cùng hoạt chất có sẵn trong kho.
                    </p>
                  </div>
                </div>
              )}

              {filtered.map((rec) => (
                <RecommendationCard
                  key={rec.id}
                  rec={rec}
                />
              ))}

              {/* AI Gemini recommendation box */}
              {result.recommendation && (
                <div className={styles.aiBox}>
                  <div className={styles.aiBoxHeader}>
                    <span className={styles.aiBoxIcon}>🤖</span>
                    <span className={styles.aiBoxTitle}>
                      Tư vấn lâm sàng — Google Gemini
                    </span>
                  </div>
                  <SimpleMarkdown text={result.recommendation} />
                </div>
              )}
            </>
          )}
        </div>


        {/* Chat input */}
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </main>

      {/* Right panel */}
      <DrugInfoPanel
        brandName={result?.brand_name}
        fdaInfo={result?.fda_info}
      />
    </div>
  );
}
