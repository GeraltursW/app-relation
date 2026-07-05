import { NODE_IMG_DIR, WIDGET_IMG_DIR } from "../data/graph.js";

const IMG_EXTS = ["", ".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG", ".webp", ".WEBP"];

export function buildCandidatePaths(dir, index) {
  return IMG_EXTS.map((ext) => `${dir}${index}${ext}`);
}

export function nodeImagePaths(index) {
  return buildCandidatePaths(NODE_IMG_DIR, index);
}

export function widgetImagePaths(index) {
  return buildCandidatePaths(WIDGET_IMG_DIR, index);
}

export function placeholderSvg(title, kind = "页面截图") {
  const safeTitle = String(title || "image").slice(0, 18);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="360" height="220" viewBox="0 0 360 220">
      <rect width="360" height="220" rx="24" fill="#eef4ff"/>
      <rect x="38" y="34" width="284" height="152" rx="18" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
      <rect x="68" y="62" width="108" height="12" rx="6" fill="#2563eb" opacity=".85"/>
      <rect x="68" y="90" width="224" height="10" rx="5" fill="#94a3b8" opacity=".7"/>
      <rect x="68" y="112" width="184" height="10" rx="5" fill="#cbd5e1"/>
      <rect x="68" y="142" width="92" height="24" rx="12" fill="#0f766e" opacity=".9"/>
      <text x="180" y="202" font-family="Arial, sans-serif" font-size="16" font-weight="700" text-anchor="middle" fill="#334155">${safeTitle}</text>
      <text x="180" y="26" font-family="Arial, sans-serif" font-size="13" text-anchor="middle" fill="#64748b">${kind}</text>
    </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}
