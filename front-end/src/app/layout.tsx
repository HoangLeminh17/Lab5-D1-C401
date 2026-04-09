import type { Metadata } from 'next';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'Pharmacist Assistant — Trợ lý Dược sĩ',
  description:
    'Hệ thống gợi ý thuốc thay thế thông minh dành cho dược sĩ lâm sàng. AI-powered drug alternative advisory system.',
  keywords: ['pharmacist', 'drug alternatives', 'dược sĩ', 'thuốc thay thế', 'OpenFDA'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💊</text></svg>" />
      </head>
      <body>{children}</body>
    </html>
  );
}
