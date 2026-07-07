export function placeholderSvg(title, kind = "页面截图") {
  const safeTitle = String(title || "image").slice(0, 18);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="360" height="640" viewBox="0 0 360 640">
      <rect width="360" height="640" rx="36" fill="#eef4ff"/>
      <rect x="42" y="36" width="276" height="568" rx="28" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
      <rect x="78" y="76" width="124" height="14" rx="7" fill="#2563eb" opacity=".85"/>
      <rect x="78" y="120" width="204" height="12" rx="6" fill="#94a3b8" opacity=".7"/>
      <rect x="78" y="150" width="160" height="12" rx="6" fill="#cbd5e1"/>
      <rect x="78" y="210" width="204" height="260" rx="18" fill="#dbeafe"/>
      <rect x="108" y="510" width="144" height="34" rx="17" fill="#0f766e" opacity=".9"/>
      <text x="180" y="584" font-family="Arial, sans-serif" font-size="17" font-weight="700" text-anchor="middle" fill="#334155">${safeTitle}</text>
      <text x="180" y="28" font-family="Arial, sans-serif" font-size="13" text-anchor="middle" fill="#64748b">${kind}</text>
    </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

