const IMG_EXTS = ["", ".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG", ".webp", ".WEBP"];

const pageMap = new Map(APP_PAGES.map((page) => [page.title, page]));
const childrenMap = APP_EDGES.reduce((map, edge) => {
  if (!map.has(edge.from)) map.set(edge.from, []);
  map.get(edge.from).push(edge);
  return map;
}, new Map());
const parentMap = new Map(APP_EDGES.map((edge) => [edge.to, edge.from]));
const collapsedNodes = new Set();
const selection = {
  type: "node",
  id: "root"
};

const elements = {
  graphRoot: document.getElementById("graphRoot"),
  graphScroll: document.getElementById("graphScroll"),
  treeNav: document.getElementById("treeNav"),
  searchInput: document.getElementById("searchInput"),
  statsBar: document.getElementById("statsBar"),
  detailTitle: document.getElementById("detailTitle"),
  summaryPanel: document.getElementById("summaryPanel"),
  imageStrip: document.getElementById("imageStrip"),
  jsonPanel: document.getElementById("jsonPanel"),
  preview: document.getElementById("preview"),
  previewTitle: document.getElementById("previewTitle"),
  previewImgs: document.getElementById("previewImgs")
};

function getOutgoingEdges(title) {
  return childrenMap.get(title) || [];
}

function hasVisibleChildren(title) {
  return getOutgoingEdges(title).length > 0 && !collapsedNodes.has(title);
}

function getGraphLevel(title) {
  if (title === "root") return 1;
  return parentMap.get(title) === "root" ? 2 : 3;
}

function buildCandidatePaths(dir, index) {
  return IMG_EXTS.map((ext) => `${dir}${index}${ext}`);
}

function placeholderSvg(title, kind = "页面截图") {
  const safeTitle = String(title || "image").slice(0, 18);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="360" height="220" viewBox="0 0 360 220">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stop-color="#e8f0ff"/>
          <stop offset="1" stop-color="#f7f9fc"/>
        </linearGradient>
      </defs>
      <rect width="360" height="220" rx="24" fill="url(#g)"/>
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

function setImageWithFallback(img, candidates, title, kind) {
  let cursor = 0;
  img.onerror = function handleImageError() {
    cursor += 1;
    if (cursor < candidates.length) {
      this.src = candidates[cursor];
      return;
    }
    this.onerror = null;
    this.src = placeholderSvg(title, kind);
  };
  img.src = candidates[0] || placeholderSvg(title, kind);
}

function createStat(label, value) {
  const item = document.createElement("div");
  item.className = "stat";
  item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
  return item;
}

function renderStats() {
  elements.statsBar.replaceChildren(
    createStat("节点", APP_PAGES.length),
    createStat("跳转", APP_EDGES.length),
    createStat("层级", "3"),
    createStat("状态", "演示版")
  );
}

function createEdgeLabel(edge, rootEdge = false) {
  const label = document.createElement("button");
  label.type = "button";
  label.className = rootEdge ? "edge-label root-edge" : "edge-label";
  label.dataset.edgeId = edge.id;

  const edgeImg = document.createElement("img");
  setImageWithFallback(edgeImg, buildCandidatePaths(WIDGET_IMG_DIR, edge.widget.imageIndex), edge.label, "组件截图");
  edgeImg.alt = edge.label;

  const text = document.createElement("span");
  text.className = "edge-text";
  text.innerHTML = `<strong>${edge.label}</strong><small>widget ${edge.widget.imageIndex}</small>`;

  label.append(edgeImg, text);
  label.addEventListener("click", (event) => {
    event.stopPropagation();
    selectEdge(edge);
  });
  return label;
}

function createNodeCard(page) {
  const level = getGraphLevel(page.title);
  const outgoing = getOutgoingEdges(page.title);
  const card = document.createElement("div");
  card.tabIndex = 0;
  card.role = "button";
  card.setAttribute("aria-label", page.title);
  card.className = `node-card level-${level}`;
  card.dataset.title = page.title;
  card.dataset.search = JSON.stringify(page).toLowerCase();
  card.id = `node-${encodeURIComponent(page.title)}`;

  const header = document.createElement("div");
  header.className = "node-header";

  const title = document.createElement("strong");
  title.className = "node-title";
  title.textContent = page.title;
  header.appendChild(title);

  if (outgoing.length) {
    const collapseButton = document.createElement("button");
    collapseButton.type = "button";
    collapseButton.className = "node-collapse";
    collapseButton.textContent = collapsedNodes.has(page.title) ? "+" : "-";
    collapseButton.setAttribute("aria-label", collapsedNodes.has(page.title) ? "展开下级节点" : "收起下级节点");
    collapseButton.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleNodeCollapse(page.title);
    });
    header.appendChild(collapseButton);
  }

  const thumb = document.createElement("img");
  thumb.className = "thumb";
  setImageWithFallback(thumb, buildCandidatePaths(NODE_IMG_DIR, page.imageIndex), page.title, "页面截图");
  thumb.alt = page.title;

  const type = document.createElement("span");
  type.className = "node-type";
  type.textContent = `${page.type} · 图 ${page.imageIndex}`;

  const meta = document.createElement("span");
  meta.className = "node-meta";
  meta.textContent = `L${level} · ${getOutgoingEdges(page.title).length} 条跳转`;

  card.append(header, thumb, type, meta);
  card.addEventListener("click", (event) => {
    event.stopPropagation();
    selectNode(page.title, true);
  });
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectNode(page.title, true);
    }
  });
  card.addEventListener("mouseenter", (event) => showPreview(page, event));
  card.addEventListener("mousemove", movePreview);
  card.addEventListener("mouseleave", hidePreview);
  return card;
}

function toggleNodeCollapse(title) {
  if (collapsedNodes.has(title)) {
    collapsedNodes.delete(title);
  } else {
    collapsedNodes.add(title);
  }
  renderGraph();
  applySearch(elements.searchInput.value);
  if (selection.type === "edge") {
    const selectedEdge = APP_EDGES.find((edge) => edge.id === selection.id);
    if (selectedEdge) selectEdge(selectedEdge);
    return;
  }
  selectNode(selection.id, false);
}

function renderGraph() {
  elements.graphRoot.innerHTML = "";
  elements.graphRoot.classList.toggle("root-collapsed", collapsedNodes.has("root"));

  const rootPage = pageMap.get("root");
  const rootCol = document.createElement("div");
  rootCol.className = "root-col";
  rootCol.appendChild(createNodeCard(rootPage));

  const bus = document.createElement("div");
  bus.className = "root-bus";

  const branchesCol = document.createElement("div");
  branchesCol.className = "branches-col";

  if (!hasVisibleChildren("root")) {
    elements.graphRoot.append(rootCol, bus, branchesCol);
    return;
  }

  getOutgoingEdges("root").forEach((rootEdge) => {
    const parentPage = pageMap.get(rootEdge.to);
    if (!parentPage) return;

    const branch = document.createElement("section");
    branch.className = "branch";

    const parentWrap = document.createElement("div");
    parentWrap.className = "parent-wrap";
    parentWrap.append(createEdgeLabel(rootEdge, true), createNodeCard(parentPage));

    const children = document.createElement("div");
    children.className = "children";

    if (hasVisibleChildren(parentPage.title)) {
      getOutgoingEdges(parentPage.title).forEach((childEdge) => {
        const childPage = pageMap.get(childEdge.to);
        if (!childPage) return;

        const childWrap = document.createElement("div");
        childWrap.className = "child-wrap";
        childWrap.append(createEdgeLabel(childEdge), createNodeCard(childPage));
        children.appendChild(childWrap);
      });
    } else {
      children.classList.add("collapsed-children");
    }

    branch.append(parentWrap, children);
    branchesCol.appendChild(branch);
  });

  elements.graphRoot.append(rootCol, bus, branchesCol);
}

function renderNav() {
  elements.treeNav.innerHTML = "";

  function buildNavNode(title) {
    const page = pageMap.get(title);
    const outgoing = getOutgoingEdges(title);
    const node = document.createElement("div");
    node.className = "nav-node";

    const row = document.createElement("button");
    row.type = "button";
    row.className = "nav-row";
    row.dataset.title = title;
    row.innerHTML = `
      <span class="toggle">${outgoing.length ? "-" : ""}</span>
      <span class="nav-name">${title}</span>
      <span class="nav-count">L${page ? getGraphLevel(page.title) : "-"}</span>
    `;
    row.addEventListener("click", () => selectNode(title, true));

    const toggle = row.querySelector(".toggle");
    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      if (!outgoing.length) return;
      node.classList.toggle("collapsed");
      toggle.textContent = node.classList.contains("collapsed") ? "+" : "-";
    });

    node.appendChild(row);

    if (outgoing.length) {
      const children = document.createElement("div");
      children.className = "nav-children";
      outgoing.forEach((edge) => children.appendChild(buildNavNode(edge.to)));
      node.appendChild(children);
    }
    return node;
  }

  elements.treeNav.appendChild(buildNavNode("root"));
}

function renderImageStrip(items) {
  elements.imageStrip.innerHTML = "";
  items.forEach(({ title, candidates, kind }) => {
    const img = document.createElement("img");
    setImageWithFallback(img, candidates, title, kind);
    img.alt = title;
    elements.imageStrip.appendChild(img);
  });
}

function setSummary(rows) {
  elements.summaryPanel.innerHTML = rows
    .map(([label, value]) => `<div class="summary-row"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function selectNode(title, scrollIntoView = false) {
  selection.type = "node";
  selection.id = title;
  document.querySelectorAll(".edge-label").forEach((el) => el.classList.remove("selected-edge"));
  document.querySelectorAll(".node-card").forEach((el) => el.classList.toggle("selected", el.dataset.title === title));
  document.querySelectorAll(".nav-row").forEach((el) => el.classList.toggle("active", el.dataset.title === title));

  const card = document.getElementById(`node-${encodeURIComponent(title)}`);
  if (scrollIntoView && card) card.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });

  const page = pageMap.get(title);
  if (!page) return;
  const outgoing = getOutgoingEdges(title);

  elements.detailTitle.textContent = page.title;
  setSummary([
    ["页面类型", page.type],
    ["图谱层级", `第 ${getGraphLevel(page.title)} 层`],
    ["父页面", parentMap.get(page.title) || "-"],
    ["页面截图", `图 ${page.imageIndex}`],
    ["下游跳转", `${outgoing.length} 条`],
    ["业务说明", page.purpose]
  ]);
  renderImageStrip([{ title: page.title, candidates: buildCandidatePaths(NODE_IMG_DIR, page.imageIndex), kind: "页面截图" }]);

  elements.jsonPanel.textContent = JSON.stringify({
    node: page,
    graphLevel: getGraphLevel(page.title),
    parent: parentMap.get(page.title) || null,
    outgoingEdges: outgoing
  }, null, 2);
}

function selectEdge(edge) {
  selection.type = "edge";
  selection.id = edge.id;
  document.querySelectorAll(".node-card").forEach((el) => el.classList.remove("selected"));
  document.querySelectorAll(".nav-row").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".edge-label").forEach((el) => el.classList.toggle("selected-edge", el.dataset.edgeId === edge.id));

  const fromPage = pageMap.get(edge.from);
  const toPage = pageMap.get(edge.to);
  elements.detailTitle.textContent = `${edge.from} -> ${edge.to}`;
  setSummary([
    ["跳转关系", `${edge.from} -> ${edge.to}`],
    ["入口语义", edge.label],
    ["组件类型", edge.widget.type],
    ["组件截图", `widget ${edge.widget.imageIndex}`],
    ["预期结果", edge.widget.expectedResult],
    ["置信度", edge.widget.confidence]
  ]);
  renderImageStrip([
    { title: edge.label, candidates: buildCandidatePaths(WIDGET_IMG_DIR, edge.widget.imageIndex), kind: "组件截图" },
    { title: edge.from, candidates: buildCandidatePaths(NODE_IMG_DIR, fromPage?.imageIndex), kind: "来源页面" },
    { title: edge.to, candidates: buildCandidatePaths(NODE_IMG_DIR, toPage?.imageIndex), kind: "目标页面" }
  ]);

  elements.jsonPanel.textContent = JSON.stringify({ edge, fromPage, toPage }, null, 2);
}

function showPreview(page, event) {
  elements.previewTitle.textContent = `${page.title} · 图 ${page.imageIndex}`;
  elements.previewImgs.innerHTML = "";
  const img = document.createElement("img");
  setImageWithFallback(img, buildCandidatePaths(NODE_IMG_DIR, page.imageIndex), page.title, "页面截图");
  img.alt = page.title;
  elements.previewImgs.appendChild(img);
  elements.preview.style.display = "block";
  movePreview(event);
}

function movePreview(event) {
  const offset = 18;
  const rect = elements.preview.getBoundingClientRect();
  let left = event.clientX + offset;
  let top = event.clientY + offset;
  if (left + rect.width > window.innerWidth) left = event.clientX - rect.width - offset;
  if (top + rect.height > window.innerHeight) top = event.clientY - rect.height - offset;
  elements.preview.style.left = `${Math.max(10, left)}px`;
  elements.preview.style.top = `${Math.max(10, top)}px`;
}

function hidePreview() {
  elements.preview.style.display = "none";
}

function applySearch(keyword) {
  const normalized = keyword.trim().toLowerCase();
  document.querySelectorAll(".node-card").forEach((card) => {
    const matched = !normalized || card.dataset.title.toLowerCase().includes(normalized) || card.dataset.search.includes(normalized);
    card.classList.toggle("dimmed", !matched);
  });
  document.querySelectorAll(".nav-row").forEach((row) => {
    const title = row.dataset.title || "";
    const page = pageMap.get(title);
    const matched = !normalized || title.toLowerCase().includes(normalized) || JSON.stringify(page || {}).toLowerCase().includes(normalized);
    row.classList.toggle("muted", !matched);
  });
}

elements.searchInput.addEventListener("input", (event) => applySearch(event.target.value));

function enableDragToPan() {
  let pointerIsDown = false;
  let isDragging = false;
  let startX = 0;
  let startY = 0;
  let startLeft = 0;
  let startTop = 0;
  let suppressNextClick = false;

  elements.graphScroll.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || event.target.closest("input, .node-collapse")) return;
    pointerIsDown = true;
    isDragging = false;
    startX = event.clientX;
    startY = event.clientY;
    startLeft = elements.graphScroll.scrollLeft;
    startTop = elements.graphScroll.scrollTop;
    elements.graphScroll.setPointerCapture(event.pointerId);
  });

  elements.graphScroll.addEventListener("pointermove", (event) => {
    if (!pointerIsDown) return;
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    if (!isDragging && Math.hypot(dx, dy) < 6) return;
    isDragging = true;
    suppressNextClick = true;
    elements.graphScroll.classList.add("dragging");
    elements.graphScroll.scrollLeft = startLeft - dx;
    elements.graphScroll.scrollTop = startTop - dy;
  });

  elements.graphScroll.addEventListener("click", (event) => {
    if (!suppressNextClick) return;
    event.preventDefault();
    event.stopPropagation();
    suppressNextClick = false;
  }, true);

  function stopDragging(event) {
    if (!pointerIsDown) return;
    pointerIsDown = false;
    if (suppressNextClick) {
      window.setTimeout(() => {
        suppressNextClick = false;
      }, 120);
    }
    isDragging = false;
    elements.graphScroll.classList.remove("dragging");
    if (elements.graphScroll.hasPointerCapture(event.pointerId)) {
      elements.graphScroll.releasePointerCapture(event.pointerId);
    }
  }

  elements.graphScroll.addEventListener("pointerup", stopDragging);
  elements.graphScroll.addEventListener("pointercancel", stopDragging);
  elements.graphScroll.addEventListener("pointerleave", stopDragging);
}

renderStats();
renderGraph();
renderNav();
enableDragToPan();
selectNode("root", false);
