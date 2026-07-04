const form = document.getElementById("query-form");
const questionInput = document.getElementById("question");
const cypherEl = document.getElementById("cypher");
const answerEl = document.getElementById("answer");
const errorEl = document.getElementById("error");
const tableEl = document.getElementById("table");
const statusEl = document.getElementById("status");
const svg = document.getElementById("graph");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  clearResults();
  statusEl.textContent = "질의 중...";

  try {
    const response = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    render(data);
  } catch (err) {
    showError("요청에 실패했습니다: " + err.message);
  } finally {
    statusEl.textContent = "";
  }
});

function clearResults() {
  cypherEl.textContent = "";
  answerEl.textContent = "";
  tableEl.innerHTML = "";
  svg.innerHTML = "";
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function render(data) {
  cypherEl.textContent = data.cypher || "(생성된 쿼리 없음)";
  if (data.error) {
    showError(data.error);
    return;
  }
  answerEl.textContent = data.answer || "(답변 없음)";
  renderTable(data.columns, data.rows);
  renderGraph(data.nodes, data.edges);
}

function renderTable(columns, rows) {
  if (!rows || rows.length === 0) {
    tableEl.textContent = "표로 보여줄 결과가 없습니다.";
    return;
  }
  const cols = columns && columns.length ? columns : Object.keys(rows[0]);
  const table = document.createElement("table");

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const col of cols) {
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const col of cols) {
      const td = document.createElement("td");
      td.textContent = formatCell(row[col]);
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);

  tableEl.appendChild(table);
}

function formatCell(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

// 외부 라이브러리 없이 그래프를 그리는 아주 단순한 force-directed 레이아웃.
// 반발력 + 스프링(엣지) + 중심 인력을 고정 횟수만큼 반복해 배치를 잡은 뒤
// SVG로 그리고, 노드는 드래그로 미세 조정할 수 있게 한다.
function renderGraph(nodes, edges) {
  if (!nodes || nodes.length === 0) {
    return;
  }

  const width = svg.clientWidth || 600;
  const height = svg.clientHeight || 500;

  const positioned = nodes.map((node, index) => ({
    ...node,
    x: width / 2 + Math.cos((index / nodes.length) * 2 * Math.PI) * Math.min(width, height) / 3,
    y: height / 2 + Math.sin((index / nodes.length) * 2 * Math.PI) * Math.min(width, height) / 3,
    vx: 0,
    vy: 0,
  }));
  const byId = new Map(positioned.map((n) => [n.id, n]));
  const links = (edges || [])
    .filter((edge) => byId.has(edge.source) && byId.has(edge.target))
    .map((edge) => ({ ...edge, a: byId.get(edge.source), b: byId.get(edge.target) }));

  simulate(positioned, links, width, height);
  draw(positioned, links);
}

function simulate(nodes, links, width, height) {
  const ITERATIONS = 300;
  const REPULSION = 2500;
  const EDGE_LENGTH = 130;

  for (let iter = 0; iter < ITERATIONS; iter++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        let dx = a.x - b.x;
        let dy = a.y - b.y;
        const distSq = Math.max(dx * dx + dy * dy, 0.01);
        const force = REPULSION / distSq;
        const dist = Math.sqrt(distSq);
        dx /= dist;
        dy /= dist;
        a.vx += dx * force;
        a.vy += dy * force;
        b.vx -= dx * force;
        b.vy -= dy * force;
      }
    }

    for (const link of links) {
      const { a, b } = link;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
      const force = (dist - EDGE_LENGTH) * 0.02;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }

    for (const node of nodes) {
      node.vx += (width / 2 - node.x) * 0.002;
      node.vy += (height / 2 - node.y) * 0.002;
      node.vx *= 0.85;
      node.vy *= 0.85;
      node.x += node.vx;
      node.y += node.vy;
      node.x = Math.max(30, Math.min(width - 30, node.x));
      node.y = Math.max(30, Math.min(height - 30, node.y));
    }
  }
}

const SVG_NS = "http://www.w3.org/2000/svg";

function draw(nodes, links) {
  svg.innerHTML = "";

  const linkElements = links.map((link) => {
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("class", "edge");
    svg.appendChild(line);

    const label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("class", "edge-label");
    label.textContent = link.type;
    svg.appendChild(label);

    return { line, label, link };
  });
  updateLinkPositions(linkElements);

  const incidentLinks = new Map();
  for (const entry of linkElements) {
    for (const node of [entry.link.a, entry.link.b]) {
      if (!incidentLinks.has(node)) incidentLinks.set(node, []);
      incidentLinks.get(node).push(entry);
    }
  }

  for (const node of nodes) {
    const g = document.createElementNS(SVG_NS, "g");
    g.setAttribute("class", "node");
    g.setAttribute("transform", `translate(${node.x},${node.y})`);

    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("r", 22);
    circle.setAttribute("class", "node-circle");
    g.appendChild(circle);

    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = [node.name, (node.labels || []).join(", "), node.description]
      .filter(Boolean)
      .join("\n");
    g.appendChild(title);

    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("class", "node-label");
    text.setAttribute("y", 36);
    text.textContent = node.name || "(이름 없음)";
    g.appendChild(text);

    svg.appendChild(g);
    makeDraggable(g, node, incidentLinks.get(node) || []);
  }
}

function updateLinkPositions(linkElements) {
  for (const { line, label, link } of linkElements) {
    line.setAttribute("x1", link.a.x);
    line.setAttribute("y1", link.a.y);
    line.setAttribute("x2", link.b.x);
    line.setAttribute("y2", link.b.y);
    label.setAttribute("x", (link.a.x + link.b.x) / 2);
    label.setAttribute("y", (link.a.y + link.b.y) / 2);
  }
}

function makeDraggable(g, node, incidentLinkEntries) {
  let dragging = false;

  const onMouseMove = (event) => {
    if (!dragging) return;
    const rect = svg.getBoundingClientRect();
    node.x = event.clientX - rect.left;
    node.y = event.clientY - rect.top;
    g.setAttribute("transform", `translate(${node.x},${node.y})`);
    updateLinkPositions(incidentLinkEntries);
  };

  g.addEventListener("mousedown", () => {
    dragging = true;
  });
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("mouseup", () => {
    dragging = false;
  });
}
