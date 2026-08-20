import json

OUT = "/home/claude/bi_demand_forecasting_project/output"

with open(f"{OUT}/kpi_summary_public.json", encoding="utf-8") as f:
    KPI = json.load(f)
with open(f"{OUT}/ml_model_comparison.json", encoding="utf-8") as f:
    ML = json.load(f)

DATA = {"kpi": KPI, "ml": ML}
data_json = json.dumps(DATA, ensure_ascii=False)

HTML = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BUTL 2025 — BI Dashboard &amp; Demand Forecasting (Real Data, Anonymized)</title>
<style>
  :root {
    --surface-1:  #fcfcfb;
    --page:       #f9f9f7;
    --text-1:     #0b0b0b;
    --text-2:     #52514e;
    --muted:      #898781;
    --grid:       #e1e0d9;
    --border:     rgba(11,11,11,0.10);
    --good:       #0ca30c;
    --critical:   #d03b3b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--page); color: var(--text-1);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 28px 32px 60px;
  }
  h1 { font-size: 21px; margin: 0 0 4px; }
  .subtitle { color: var(--text-2); font-size: 13px; margin: 0 0 10px; line-height: 1.5; }
  .subtitle b { color: var(--text-1); }
  .banner {
    background: #fff8e6; border: 1px solid #ecd394; border-radius: 8px;
    padding: 10px 14px; font-size: 12.5px; color: #6b5416; margin-bottom: 22px; line-height: 1.5;
  }
  .kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 24px; }
  .kpi-card {
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px;
  }
  .kpi-label { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
  .kpi-value { font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; }
  .kpi-sub { font-size: 11.5px; color: var(--text-2); margin-top: 4px; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
  .panel {
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 18px 20px;
  }
  .panel h2 { font-size: 14px; margin: 0 0 2px; }
  .panel .desc { font-size: 12px; color: var(--text-2); margin: 0 0 14px; }
  .chart-wrap svg { display: block; width: 100%; height: auto; overflow: visible; }
  .bar-label { font-size: 11px; fill: var(--text-2); font-variant-numeric: tabular-nums; }
  .axis-label { font-size: 10px; fill: var(--muted); }
  .cat-label { font-size: 11px; fill: var(--text-1); }
  .legend { font-size: 11.5px; fill: var(--text-2); }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  th, td { text-align: right; padding: 7px 8px; border-bottom: 1px solid var(--grid); }
  th:first-child, td:first-child { text-align: left; }
  th { color: var(--muted); font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: .02em; }
  .insight {
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 20px; margin-bottom: 16px; font-size: 13px; line-height: 1.65; color: var(--text-2);
  }
  .insight b { color: var(--text-1); }
  .tag { display: inline-block; font-size: 10.5px; font-weight: 700; padding: 1px 7px; border-radius: 20px; margin-left: 6px; }
  .tag.good { background: #e5f6e5; color: #0a6b0a; }
  .tag.bad { background: #fbe7e6; color: #a12b2b; }
  footer { color: var(--muted); font-size: 11.5px; margin-top: 20px; }
</style>
</head>
<body>
  <h1>BUTL 2025 — BI Dashboard &amp; Demand Forecasting</h1>
  <p class="subtitle"><b>Dữ liệu THẬT</b> vận hành BUTL năm 2025 (490.928 trip &middot; 68.964 no-driver-found &middot; 455.937 user).</p>
  <div class="banner">
    Doanh thu (Net Revenue), AOV và giá trị discount trung bình đã được <b>ẩn danh hóa</b> thành % thị phần / chỉ số
    (trung bình = 100) để bảo mật số liệu kinh doanh thật của doanh nghiệp — không hiển thị số VND tuyệt đối.
    Số lượng chuyến, tỷ lệ (%) và MAPE mô hình là số thật vì không làm lộ quy mô tài chính.
  </div>

  <div class="kpi-row" id="kpiRow"></div>

  <div class="grid-2">
    <div class="panel">
      <h2>Tổng Booking theo tháng</h2>
      <p class="desc">Tăng trưởng rõ rệt nửa cuối năm (Q4 &gt; Q1)</p>
      <div class="chart-wrap" id="bookingTrendChart"></div>
    </div>
    <div class="panel">
      <h2>Completion / Cancellation / No-Driver-Found Rate theo tháng</h2>
      <p class="desc">1 trục Y duy nhất — không dual-axis</p>
      <div class="chart-wrap" id="rateTrendChart"></div>
    </div>
  </div>

  <div class="grid-2">
    <div class="panel">
      <h2>Failure Rate theo tỉnh/thành (Top 15 theo tổng nhu cầu)</h2>
      <p class="desc">Failure Rate = (Cancelled + No-Driver-Found) / Tổng nhu cầu (Total Booking + No-Driver-Found)</p>
      <div class="chart-wrap" id="cityFailureChart"></div>
    </div>
    <div class="panel">
      <h2>Failure Rate theo khung giờ x ngày trong tuần</h2>
      <p class="desc">Đậm hơn = tỷ lệ thất bại (huỷ + không tìm được tài xế) cao hơn</p>
      <div class="chart-wrap" id="heatmapChart"></div>
    </div>
  </div>

  <div class="grid-2">
    <div class="panel">
      <h2>So sánh model dự báo (MAPE trên tập test)</h2>
      <p class="desc">Test = 2 tháng cuối năm, giữ nguyên trạng, không nhìn thấy lúc train</p>
      <div class="chart-wrap" id="mlCompareChart"></div>
    </div>
    <div class="panel">
      <h2>Feature Importance — Gradient Boosting</h2>
      <p class="desc">lag_1 (booking hôm qua) chiếm phần lớn tầm quan trọng</p>
      <div class="chart-wrap" id="featImpChart"></div>
    </div>
  </div>

  <div class="insight" id="insightBox"></div>

  <div class="panel">
    <h2>Chi tiết Failure Rate theo tỉnh/thành</h2>
    <div id="cityTableWrap"><table id="cityTable"></table></div>
  </div>

  <footer>BI Dashboard tương tác (HTML + SVG thuần) &middot; Xây dựng từ dữ liệu vận hành thật BUTL 2025, số liệu tài chính đã ẩn danh hóa &middot; Trần Thị Cẩm Loan — Marketing Data Analyst</footer>

<script>
const DATA = __DATA_JSON__;
const KPI = DATA.kpi, ML = DATA.ml;
const PALETTE = { blue: '#2a78d6', orange: '#eb6834', aqua: '#1baf7a', yellow: '#eda100', violet: '#4a3aa7', magenta: '#e87ba4' };
const fmtN = n => new Intl.NumberFormat('vi-VN').format(Math.round(n));
const fmtPct = n => n.toFixed(1) + '%';

const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}

function hBarChart(containerId, { labels, values, colors, valueFmt }) {
  const container = document.getElementById(containerId);
  const W = container.clientWidth || 460, rowH = 22, gap = 7;
  const H = labels.length * (rowH + gap) + 10;
  const leftPad = 130, rightPad = 60;
  const maxV = Math.max(...values.map(v => Math.abs(v))) * 1.15 || 1;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H });

  for (let i = 0; i <= 4; i++) {
    const x = leftPad + (i / 4) * (W - leftPad - rightPad);
    svg.appendChild(el('line', { x1: x, x2: x, y1: 4, y2: H - 4, stroke: '#e1e0d9', 'stroke-width': 1 }));
  }

  labels.forEach((lab, i) => {
    const y = i * (rowH + gap) + 6;
    const barW = (Math.abs(values[i]) / maxV) * (W - leftPad - rightPad);
    const catText = el('text', { x: leftPad - 10, y: y + rowH / 2 + 4, 'text-anchor': 'end', class: 'cat-label' });
    catText.textContent = lab;
    svg.appendChild(catText);
    svg.appendChild(el('rect', { x: leftPad, y, width: Math.max(barW, 2), height: rowH, rx: 3, fill: colors[i] }));
    const valText = el('text', { x: leftPad + barW + 8, y: y + rowH / 2 + 4, class: 'bar-label' });
    valText.textContent = valueFmt(values[i]);
    svg.appendChild(valText);
  });

  container.innerHTML = '';
  container.appendChild(svg);
}

function vBarChart(containerId, { labels, values, colors, valueFmt }) {
  const container = document.getElementById(containerId);
  const W = container.clientWidth || 460, H = 250;
  const topPad = 20, bottomPad = 46;
  const n = labels.length;
  const barGap = 16;
  const barW = (W - barGap * (n + 1)) / n;
  const maxV = Math.max(...values) * 1.2;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H });

  for (let i = 0; i <= 3; i++) {
    const y = topPad + (i / 3) * (H - topPad - bottomPad);
    svg.appendChild(el('line', { x1: 0, x2: W, y1: y, y2: y, stroke: '#e1e0d9', 'stroke-width': 1 }));
  }

  labels.forEach((lab, i) => {
    const x = barGap + i * (barW + barGap);
    const h = (values[i] / maxV) * (H - topPad - bottomPad);
    const y = H - bottomPad - h;
    svg.appendChild(el('rect', { x, y, width: barW, height: h, rx: 4, fill: colors[i] }));
    const valText = el('text', { x: x + barW / 2, y: y - 6, 'text-anchor': 'middle', class: 'bar-label' });
    valText.textContent = valueFmt(values[i]);
    svg.appendChild(valText);
    const words = lab.split(' ');
    const mid = Math.ceil(words.length / 2);
    const line1 = words.slice(0, mid).join(' '), line2 = words.slice(mid).join(' ');
    const l1 = el('text', { x: x + barW / 2, y: H - 26, 'text-anchor': 'middle', class: 'axis-label' });
    l1.textContent = line1;
    svg.appendChild(l1);
    if (line2) {
      const l2 = el('text', { x: x + barW / 2, y: H - 14, 'text-anchor': 'middle', class: 'axis-label' });
      l2.textContent = line2;
      svg.appendChild(l2);
    }
  });

  container.innerHTML = '';
  container.appendChild(svg);
}

function lineChart(containerId, { xLabels, series, colors, valueFmt }) {
  // series: [{name, values}], single Y axis (never dual-axis)
  const container = document.getElementById(containerId);
  const W = container.clientWidth || 460, H = 260;
  const topPad = 16, bottomPad = 30, leftPad = 34, rightPad = 12;
  const allVals = series.flatMap(s => s.values);
  const maxV = Math.max(...allVals) * 1.15;
  const minV = 0;
  const plotW = W - leftPad - rightPad, plotH = H - topPad - bottomPad;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H });

  for (let i = 0; i <= 4; i++) {
    const y = topPad + (i / 4) * plotH;
    svg.appendChild(el('line', { x1: leftPad, x2: W - rightPad, y1: y, y2: y, stroke: '#e1e0d9', 'stroke-width': 1 }));
    const val = maxV - (i / 4) * (maxV - minV);
    const t = el('text', { x: leftPad - 6, y: y + 3, 'text-anchor': 'end', class: 'axis-label' });
    t.textContent = Math.round(val);
    svg.appendChild(t);
  }

  const stepX = plotW / (xLabels.length - 1);
  xLabels.forEach((lab, i) => {
    if (i % 2 === 0) {
      const t = el('text', { x: leftPad + i * stepX, y: H - 8, 'text-anchor': 'middle', class: 'axis-label' });
      t.textContent = lab;
      svg.appendChild(t);
    }
  });

  series.forEach((s, si) => {
    const pts = s.values.map((v, i) => [leftPad + i * stepX, topPad + plotH - ((v - minV) / (maxV - minV)) * plotH]);
    const d = pts.map((p, i) => (i === 0 ? 'M' : 'L') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
    svg.appendChild(el('path', { d, fill: 'none', stroke: colors[si], 'stroke-width': 2.2 }));
    pts.forEach(p => svg.appendChild(el('circle', { cx: p[0], cy: p[1], r: 2.6, fill: colors[si] })));
  });

  // legend
  series.forEach((s, si) => {
    const lx = leftPad + si * 150, ly = topPad - 4;
    svg.appendChild(el('circle', { cx: lx, cy: ly, r: 4, fill: colors[si] }));
    const t = el('text', { x: lx + 8, y: ly + 4, class: 'legend' });
    t.textContent = s.name;
    svg.appendChild(t);
  });

  container.innerHTML = '';
  container.appendChild(svg);
}

function heatmapChart(containerId, { days, hours, values }) {
  const container = document.getElementById(containerId);
  const W = container.clientWidth || 460;
  const leftPad = 60, topPad = 8, rightPad = 8, bottomPad = 20;
  const cellW = (W - leftPad - rightPad) / hours.length;
  const cellH = 24;
  const H = days.length * cellH + topPad + bottomPad;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H });

  const maxV = 100;
  const seq = v => {
    // sequential single-hue blue ramp, light -> dark
    const t = Math.min(v / maxV, 1);
    const lightness = 92 - t * 62; // 92% (light) -> 30% (dark)
    return `hsl(214, 70%, ${lightness}%)`;
  };

  days.forEach((d, ri) => {
    const y = topPad + ri * cellH;
    const lbl = el('text', { x: leftPad - 8, y: y + cellH / 2 + 4, 'text-anchor': 'end', class: 'cat-label' });
    lbl.textContent = d.slice(0, 3);
    svg.appendChild(lbl);
    hours.forEach((h, ci) => {
      const x = leftPad + ci * cellW;
      const v = values[ri][ci];
      svg.appendChild(el('rect', { x, y, width: cellW - 1, height: cellH - 2, fill: seq(v) }));
    });
  });

  [0, 6, 12, 18, 23].forEach(h => {
    const x = leftPad + h * cellW + cellW / 2;
    const t = el('text', { x, y: topPad + days.length * cellH + 12, 'text-anchor': 'middle', class: 'axis-label' });
    t.textContent = h + 'h';
    svg.appendChild(t);
  });

  container.innerHTML = '';
  container.appendChild(svg);
}

// ---------- KPI cards ----------
document.getElementById('kpiRow').innerHTML = [
  { label: 'Total Booking (2025)', value: fmtN(KPI.kpi.total_booking), sub: `${fmtN(KPI.kpi.completed)} completed` },
  { label: 'Completion Rate', value: fmtPct(KPI.kpi.completion_rate_pct), sub: 'trên tổng nhu cầu' },
  { label: 'Cancellation Rate', value: fmtPct(KPI.kpi.cancellation_rate_pct), sub: 'trên total booking' },
  { label: 'No-Driver-Found Rate', value: fmtPct(KPI.kpi.no_driver_found_rate_pct), sub: `${fmtN(KPI.kpi.no_driver_found)} lượt` },
  { label: 'New Users 2025', value: fmtN(KPI.kpi.new_users_2025), sub: 'tài khoản đăng ký mới' },
].map(k => `
  <div class="kpi-card">
    <div class="kpi-label">${k.label}</div>
    <div class="kpi-value">${k.value}</div>
    <div class="kpi-sub">${k.sub}</div>
  </div>`).join('');

// ---------- Booking trend ----------
const MONTH_LABELS = KPI.monthly_trend.map(m => 'T' + m.month);
vBarChart('bookingTrendChart', {
  labels: MONTH_LABELS,
  values: KPI.monthly_trend.map(m => m.total_booking),
  colors: KPI.monthly_trend.map(() => PALETTE.blue),
  valueFmt: v => fmtN(v),
});

// ---------- Rate trend (single axis, 3 series) ----------
lineChart('rateTrendChart', {
  xLabels: MONTH_LABELS,
  series: [
    { name: 'Completion %', values: KPI.monthly_trend.map(m => m.completion_rate) },
    { name: 'Cancellation %', values: KPI.monthly_trend.map(m => m.cancellation_rate) },
  ],
  colors: [PALETTE.aqua, PALETTE.orange],
});

// ---------- City failure ----------
const cityTop10 = KPI.city_failure_top15.slice(0, 10);
hBarChart('cityFailureChart', {
  labels: cityTop10.map(c => c.city_raw),
  values: cityTop10.map(c => c.failure_rate),
  colors: cityTop10.map(c => c.failure_rate >= 70 ? '#d03b3b' : c.failure_rate >= 50 ? '#eb6834' : '#eda100'),
  valueFmt: v => fmtPct(v),
});

// ---------- Heatmap ----------
heatmapChart('heatmapChart', KPI.heatmap_failure_rate);

// ---------- ML comparison ----------
const mc = ML.model_comparison;
const mcOrder = ['NaiveBaseline_lag7', 'LinearRegression', 'RandomForest', 'GradientBoosting'];
const mcLabel = { NaiveBaseline_lag7: 'Naive (lag 7)', LinearRegression: 'Linear Reg.', RandomForest: 'Random Forest', GradientBoosting: 'Gradient Boosting' };
hBarChart('mlCompareChart', {
  labels: mcOrder.map(k => mcLabel[k]),
  values: mcOrder.map(k => mc[k]['MAPE_%']),
  colors: mcOrder.map(k => k === ML.selected_model ? '#0ca30c' : '#898781'),
  valueFmt: v => v.toFixed(2) + '%',
});

// ---------- Feature importance ----------
const fi = ML.feature_importance[ML.selected_model];
const fiSorted = Object.entries(fi).sort((a, b) => b[1] - a[1]).slice(0, 6);
hBarChart('featImpChart', {
  labels: fiSorted.map(f => f[0]),
  values: fiSorted.map(f => f[1]),
  colors: fiSorted.map(() => PALETTE.violet),
  valueFmt: v => (v * 100).toFixed(1) + '%',
});

// ---------- Insight ----------
const worstCity = [...KPI.city_failure_top15].sort((a, b) => b.failure_rate - a.failure_rate)[0];
document.getElementById('insightBox').innerHTML = `
  <b>Insight chính:</b> Model <b>${mcLabel[ML.selected_model]}</b> đạt MAPE
  <b>${mc[ML.selected_model]['MAPE_%'].toFixed(2)}%</b> so với baseline naive
  <b>${mc.NaiveBaseline_lag7['MAPE_%'].toFixed(2)}%</b> <span class="tag good">CẢI THIỆN ~${(100 - mc[ML.selected_model]['MAPE_%'] / mc.NaiveBaseline_lag7['MAPE_%'] * 100).toFixed(1)}%</span> —
  feature quan trọng nhất là <b>lag_1</b> (booking hôm qua), cho thấy nhu cầu có tính lặp lại rất mạnh theo ngày liền trước.<br><br>
  Về vận hành, <b>${worstCity.city_raw}</b> có Failure Rate cao nhất trong nhóm nhu cầu lớn
  (<b>${fmtPct(worstCity.failure_rate)}</b>) <span class="tag bad">CẦN ƯU TIÊN</span> — kết hợp với heatmap khung giờ×ngày để xác định
  đúng khung giờ cao điểm cần bổ sung tài xế thay vì dàn trải đều cả ngày.
`;

// ---------- City table ----------
const tbl = document.getElementById('cityTable');
tbl.innerHTML = `
  <thead><tr><th>Tỉnh/Thành</th><th>Tổng nhu cầu</th><th>Failure Rate</th></tr></thead>
  <tbody>
    ${KPI.city_failure_top15.map(c => `
      <tr>
        <td>${c.city_raw}</td>
        <td>${fmtN(c.total_demand)}</td>
        <td>${fmtPct(c.failure_rate)}</td>
      </tr>`).join('')}
  </tbody>
`;
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA_JSON__", data_json)

out_path = f"{OUT}/dashboard_public.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)
print("written", out_path, len(HTML), "bytes")
