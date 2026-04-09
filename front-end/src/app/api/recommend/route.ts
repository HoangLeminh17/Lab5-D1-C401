import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { brand_name } = body as { brand_name: string };

    if (!brand_name?.trim()) {
      return NextResponse.json({ success: false, error_message: 'brand_name is required' }, { status: 400 });
    }

    // Try Python backend first (port 5000)
    try {
      const backendRes = await fetch('http://localhost:5000/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_name }),
        signal: AbortSignal.timeout(20000),
      });
      if (backendRes.ok) {
        const data = await backendRes.json();
        return NextResponse.json(data);
      }
    } catch {
      // Backend unavailable — fall through to direct OpenFDA
    }

    // --- Direct OpenFDA lookup ---
    const fdaRes = await fetch(
      `https://api.fda.gov/drug/label.json?search=openfda.brand_name:"${encodeURIComponent(brand_name)}"&limit=1`,
      { signal: AbortSignal.timeout(10000) }
    );

    if (!fdaRes.ok) {
      return NextResponse.json({
        brand_name, fda_info: null, alternative_drugs: [], recommendation: '',
        success: false,
        error_message: `Không tìm thấy "${brand_name}" trên FDA / Drug not found on FDA`,
      });
    }

    const fdaData = await fdaRes.json();
    const drug = fdaData.results?.[0];

    if (!drug) {
      return NextResponse.json({
        brand_name, fda_info: null, alternative_drugs: [], recommendation: '',
        success: false,
        error_message: `Không có dữ liệu FDA cho "${brand_name}" / No FDA data`,
      });
    }

    const getField = (val: unknown): string => {
      if (!val) return 'Not available in FDA database';
      if (Array.isArray(val)) return String(val[0]).slice(0, 600);
      return String(val).slice(0, 600);
    };

    const getIngredient = (d: Record<string, unknown>): string => {
      const ai = d.active_ingredient;
      if (Array.isArray(ai) && ai.length > 0) {
        const first = ai[0];
        if (typeof first === 'object' && first !== null)
          return (first as Record<string, string>).name ?? (first as Record<string, string>).value ?? 'Unknown';
        return String(first);
      }
      const openfda = (d.openfda as Record<string, unknown>) ?? {};
      const sub = openfda.substance_name;
      if (Array.isArray(sub) && sub.length > 0) return String(sub[0]);
      return 'Unknown';
    };

    const getRoute = (d: Record<string, unknown>): string => {
      const r = d.route;
      if (Array.isArray(r) && r.length > 0) return (r as string[]).slice(0, 2).join(', ');
      const openfda = (d.openfda as Record<string, unknown>) ?? {};
      const or_ = openfda.route;
      if (Array.isArray(or_) && or_.length > 0) return (or_ as string[]).slice(0, 2).join(', ');
      return 'Not available';
    };

    const fda_info = {
      Hoat_Chat: getIngredient(drug),
      Duong_Dung: getRoute(drug),
      Chi_Dinh: getField(drug.indications_and_usage),
      Chong_Chi_Dinh: getField(drug.contraindications || drug.warnings),
      Tac_Dung_Phu: getField(drug.adverse_reactions),
      success: true,
    };

    // Read inventory.csv (relative to project root)
    const fs = await import('fs');
    const path = await import('path');
    const csvPath = path.join(process.cwd(), '..', 'inventory.csv');

    let alternative_drugs: Array<{ Ten_Thuoc: string; Hoat_Chat: string; Ton_Kho: number }> = [];

    try {
      const csv = fs.readFileSync(csvPath, 'utf-8');
      const rows = csv.trim().split(/\r?\n/).slice(1);
      const activeIng = fda_info.Hoat_Chat.toLowerCase().trim();

      alternative_drugs = rows
        .map((row) => {
          const parts = row.split(',');
          return {
            Ten_Thuoc: parts[0]?.trim() ?? '',
            Hoat_Chat: parts[1]?.trim() ?? '',
            Ton_Kho: parseInt(parts[2]?.trim() ?? '0', 10),
          };
        })
        .filter(
          (d) =>
            d.Ton_Kho > 0 &&
            d.Ten_Thuoc !== brand_name &&
            (d.Hoat_Chat.toLowerCase() === activeIng ||
              activeIng.includes(d.Hoat_Chat.toLowerCase()))
        );
    } catch {
      // inventory.csv not accessible
    }

    return NextResponse.json({
      brand_name, fda_info, alternative_drugs,
      recommendation: '', success: true, error_message: '',
    });
  } catch (err) {
    return NextResponse.json(
      { brand_name: '', fda_info: null, alternative_drugs: [], recommendation: '', success: false, error_message: `Server error: ${String(err)}` },
      { status: 500 }
    );
  }
}
