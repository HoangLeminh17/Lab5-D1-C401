// Core domain types for Pharmacist Assistant

export interface FDAInfo {
  Hoat_Chat: string;
  Duong_Dung: string;
  Chi_Dinh: string;
  Chong_Chi_Dinh: string;
  Tac_Dung_Phu: string;
  success: boolean;
}

export interface InventoryDrug {
  Ten_Thuoc: string;
  Hoat_Chat: string;
  Ton_Kho: number;
}

export type RecommendationVariant = 'equivalent' | 'alternative' | 'fallback';

export interface DrugRecommendation {
  id: string;
  drug: InventoryDrug;
  variant: RecommendationVariant;
  reason: string;
}

export interface ConsultationResult {
  brand_name: string;
  fda_info: FDAInfo | null;
  alternative_drugs: InventoryDrug[];
  recommendation: string;
  success: boolean;
  error_message: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  result?: ConsultationResult;
}

export interface ConsultationHistoryItem {
  id: string;
  brandName: string;
  status: 'approved' | 'rejected' | 'pending';
  timestamp: Date;
  alternativesFound: number;
}

export interface FilterState {
  stockFilter: 'all' | 'in_stock' | 'low_stock';
  variants: RecommendationVariant[];
}

export type StockLevel = 'out' | 'low' | 'ok' | 'high';

export function getStockLevel(stock: number): StockLevel {
  if (stock === 0) return 'out';
  if (stock <= 30) return 'low';
  if (stock <= 80) return 'ok';
  return 'high';
}

export function getStockLabelVI(level: StockLevel): string {
  const labels: Record<StockLevel, string> = {
    out: 'Hết hàng', low: 'Sắp hết', ok: 'Còn hàng', high: 'Đủ hàng',
  };
  return labels[level];
}

export function getVariantLabel(variant: RecommendationVariant, lang: 'vi' | 'en' = 'vi'): string {
  const vi: Record<RecommendationVariant, string> = {
    equivalent: 'Tương đương', alternative: 'Thay thế', fallback: 'Dự phòng',
  };
  const en: Record<RecommendationVariant, string> = {
    equivalent: 'Equivalent', alternative: 'Alternative', fallback: 'Fallback',
  };
  return lang === 'vi' ? vi[variant] : en[variant];
}

export function buildRecommendations(
  drugs: InventoryDrug[],
  activeIngredient: string
): DrugRecommendation[] {
  return drugs.map((drug, idx) => {
    const sameIngredient = drug.Hoat_Chat.toLowerCase().trim() === activeIngredient.toLowerCase().trim();
    const variant: RecommendationVariant = sameIngredient
      ? (idx < 3 ? 'equivalent' : 'alternative')
      : 'fallback';
    const reason = sameIngredient
      ? 'Cùng hoạt chất với thuốc gốc'
      : 'Khác nhóm dược lý';
    return { id: `rec-${idx}`, drug, variant, reason };
  });
}
