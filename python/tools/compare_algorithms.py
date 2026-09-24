import os
import glob
import json
import base64
import argparse

def get_ull_logo_base64():
    """
    Reads the official ULL white logo from RSD-Slides repository if available,
    otherwise returns an empty string.
    """
    candidates = [
        "/home/ogomez/repo/RSD-Slides/common/icono-ull-blanco.png",
        os.path.expanduser("~/repo/RSD-Slides/common/icono-ull-blanco.png")
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass
    return ""

def load_results(results_dir="results"):
    """
    Loads all JSON results from results/<algorithm>/<sequence>.json
    and returns a structured dictionary:
    {
      "algorithms": [...],
      "sequences": [...],
      "data": [
         {
           "algorithm": str,
           "sequence": str,
           "aggregated_metrics": { ... },
           "frame_metrics": [ ... ]
         }
      ]
    }
    """
    json_files = glob.glob(os.path.join(results_dir, "*", "*.json"))
    
    if not json_files:
        print(f"No result files found in {results_dir}/")
        return {"algorithms": [], "sequences": [], "data": []}
        
    records = []
    algorithms = set()
    sequences = set()
    
    for jpath in json_files:
        try:
            with open(jpath, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading {jpath}: {e}")
            continue
            
        algo = data.get("algorithm", "unknown")
        seq = data.get("sequence", "unknown")
        
        algorithms.add(algo)
        sequences.add(seq)
        
        agg = data.get("aggregated_metrics", {})
        frames = data.get("frame_metrics", [])
        
        # Calculate mean inference time in ms
        times_ms = [f.get("inference_time", 0) * 1000 for f in frames if "inference_time" in f]
        mean_time_ms = sum(times_ms) / len(times_ms) if times_ms else 0.0
        
        # Standardize metric keys for frames and aggregation
        processed_frames = []
        for f in frames:
            processed_frames.append({
                "frame": f.get("frame", 0),
                "Mean IoU": f.get("iou", 0.0),
                "Mean Corner Error (px)": f.get("corner_error_px", 0.0),
                "Mean Corner Error (%)": f.get("corner_error_pct", 0.0),
                "Mean Pointing Error": f.get("pointing_error", 0.0),
                "Mean Inference Time (ms)": f.get("inference_time", 0.0) * 1000
            })
            
        rec = {
            "algorithm": algo,
            "sequence": seq,
            "aggregated": {
                "Mean IoU": agg.get("Mean IoU", 0.0),
                "Mean Corner Error (px)": agg.get("Mean Corner Error (px)", 0.0),
                "Mean Corner Error (%)": agg.get("Mean Corner Error (%)", 0.0),
                "Mean Pointing Error": agg.get("Mean Pointing Error (relative)", agg.get("Mean Pointing Error", 0.0)),
                "Mean Inference Time (ms)": mean_time_ms
            },
            "frames": processed_frames
        }
        records.append(rec)
        
    return {
        "algorithms": sorted(list(algorithms)),
        "sequences": sorted(list(sequences)),
        "data": records
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DaBaCo Benchmark - Algorithm Comparison (ULL)</title>
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <!-- ULL Typography: Montserrat & Inconsolata -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;600;700&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            /* ULL Brand Colors */
            --ull-primary: #57068C;        /* RGB(87, 6, 140) ULL Purple */
            --ull-primary-light: #9d4edd;
            --ull-primary-glow: rgba(157, 78, 221, 0.25);
            --ull-secondary: #e0a922;      /* Golden Amber accent for dark mode */
            --ull-secondary-raw: #634A00;
            
            /* Dark Theme (Default) */
            --bg-color: #0b0914;
            --card-bg: #141124;
            --card-sub-bg: #1d1833;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --border-color: #272147;
            --input-bg: #1d1833;
            --chart-grid: #241e3d;
            --chart-text: #e5e7eb;
        }

        [data-theme="light"] {
            /* Light Theme */
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --card-sub-bg: #fafafa;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --border-color: #e5e7eb;
            --input-bg: #ffffff;
            --ull-primary-light: #57068C;
            --ull-primary-glow: rgba(87, 6, 140, 0.12);
            --chart-grid: #e5e7eb;
            --chart-text: #1f2937;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Montserrat', sans-serif;
            transition: background-color 0.25s ease, border-color 0.25s ease, color 0.25s ease;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            padding: 24px;
            min-height: 100vh;
        }

        .container {
            max-width: 1440px;
            margin: 0 auto;
        }

        header {
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #38025c 0%, #1f0133 100%);
            color: #ffffff;
            padding: 18px 28px;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
            border: 1px solid #4a0974;
        }

        [data-theme="light"] header {
            background: linear-gradient(135deg, #57068C 0%, #3e0463 100%);
            border: none;
        }

        .header-title-group {
            display: flex;
            align-items: center;
            gap: 18px;
        }

        .ull-logo-img {
            height: 44px;
            width: auto;
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }

        h1 {
            font-size: 1.45rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .badge {
            font-size: 0.75rem;
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid rgba(255, 255, 255, 0.25);
        }

        .theme-toggle-btn {
            background: rgba(255, 255, 255, 0.15);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .theme-toggle-btn:hover {
            background: rgba(255, 255, 255, 0.25);
        }

        .controls-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            background-color: var(--card-bg);
            padding: 20px 24px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            margin-bottom: 24px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        }

        .control-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        label {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--ull-primary-light);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        select {
            background-color: var(--input-bg);
            color: var(--text-primary);
            border: 1.5px solid var(--border-color);
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            outline: none;
            cursor: pointer;
        }

        select:focus {
            border-color: var(--ull-primary-light);
            box-shadow: 0 0 0 3px var(--ull-primary-glow);
        }

        .algo-checkboxes {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            background-color: var(--input-bg);
            padding: 8px 14px;
            border-radius: 8px;
            border: 1.5px solid var(--border-color);
            min-height: 42px;
            align-items: center;
        }

        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: var(--text-primary);
            cursor: pointer;
            font-weight: 600;
            font-family: 'Inconsolata', monospace;
        }

        .checkbox-label input {
            cursor: pointer;
            accent-color: var(--ull-primary-light);
            width: 16px;
            height: 16px;
        }

        .main-layout {
            display: grid;
            grid-template-columns: 370px 1fr;
            gap: 24px;
        }

        @media (max-width: 1024px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
        }

        .summary-card {
            background-color: var(--card-bg);
            padding: 22px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
            display: flex;
            flex-direction: column;
            gap: 16px;
            height: fit-content;
        }

        .summary-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--ull-primary-light);
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .summary-list {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .summary-item {
            background-color: var(--card-sub-bg);
            border: 1.5px solid var(--border-color);
            border-radius: 10px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .summary-item-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }

        .summary-algo-name {
            font-size: 0.95rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: 'Inconsolata', monospace;
            color: var(--text-primary);
        }

        .algo-dot {
            width: 12px;
            height: 12px;
            border-radius: 3px;
            display: inline-block;
        }

        .summary-metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px 12px;
        }

        .metric-stat {
            display: flex;
            flex-direction: column;
            padding: 4px 6px;
            border-radius: 6px;
            background: rgba(0, 0, 0, 0.15);
        }

        [data-theme="light"] .metric-stat {
            background: #fafafa;
        }

        .metric-stat-label {
            font-size: 0.65rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        .metric-stat-val {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Inconsolata', monospace;
        }

        .metric-stat.active-metric {
            background-color: var(--ull-primary-glow);
            border-left: 3px solid var(--ull-primary-light);
        }

        .metric-stat.active-metric .metric-stat-val {
            color: var(--ull-primary-light);
        }

        .metric-stat.active-metric .metric-stat-label {
            color: var(--ull-primary-light);
            font-weight: 700;
        }

        .summary-sub {
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .chart-card {
            background-color: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
            display: flex;
            flex-direction: column;
        }

        .chart-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
            flex-wrap: wrap;
            gap: 10px;
        }

        .chart-title-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .chart-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0;
            user-select: text !important;
            -webkit-user-select: text !important;
            cursor: text;
        }

        .copy-title-btn {
            background-color: var(--card-sub-bg);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-family: 'Montserrat', sans-serif;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 5px 10px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .copy-title-btn:hover {
            color: var(--ull-primary-light);
            border-color: var(--ull-primary-light);
            background-color: var(--ull-primary-glow);
        }

        .copy-title-btn.copied {
            color: #10b981;
            border-color: #10b981;
            background-color: rgba(16, 185, 129, 0.1);
        }

        .gtitle, .xtitle, .ytitle, text, .summary-title, .summary-algo-name, .metric-stat-val {
            user-select: text !important;
            -webkit-user-select: text !important;
            cursor: text !important;
        }

        #chart-container {
            width: 100%;
            height: 620px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title-group">
                __LOGO_HTML__
                <div>
                    <h1>DaBaCo Algorithm Benchmark</h1>
                    <div style="font-size: 0.8rem; opacity: 0.85; margin-top: 2px;">Universidad de La Laguna · Performance Visualizer</div>
                </div>
            </div>
            <div class="header-actions">
                <button class="theme-toggle-btn" onclick="toggleTheme()" id="theme-btn">☀️ Light Mode</button>
                <span class="badge">Interactive Analysis</span>
            </div>
        </header>

        <div class="controls-grid">
            <!-- Metric Selector -->
            <div class="control-group">
                <label for="metric-select">Metric</label>
                <select id="metric-select" onchange="updateView()">
                    <option value="Mean IoU">Mean IoU (Higher is better)</option>
                    <option value="Mean Corner Error (px)">Mean Corner Error px (Lower is better)</option>
                    <option value="Mean Corner Error (%)">Mean Corner Error % (Lower is better)</option>
                    <option value="Mean Pointing Error">Mean Pointing Error (Lower is better)</option>
                    <option value="Mean Inference Time (ms)">Inference Time ms (Lower is better)</option>
                </select>
            </div>

            <!-- Mode / Scope Selector -->
            <div class="control-group">
                <label for="scope-select">View Scope</label>
                <select id="scope-select" onchange="updateView()">
                    <option value="__GLOBAL__">Global (Bar per Sequence)</option>
                </select>
            </div>

            <!-- Algorithms Selector -->
            <div class="control-group" style="grid-column: span 2;">
                <label>Algorithms to Compare</label>
                <div class="algo-checkboxes" id="algo-checkboxes">
                    <!-- Checkboxes populated via JS -->
                </div>
            </div>
        </div>

        <div class="main-layout">
            <!-- Summary Box -->
            <div class="summary-card">
                <div class="summary-title" id="summary-title">Global Averages</div>
                <div class="summary-list" id="summary-list">
                    <!-- Average metrics rendered here -->
                </div>
            </div>

            <!-- Main Bar Chart -->
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title-wrapper">
                        <h2 id="chart-title" class="chart-title">DaBaCo Benchmark</h2>
                        <button class="copy-title-btn" id="copy-title-btn" onclick="copySequenceName()" title="Copy sequence name">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                            <span>Copy Sequence</span>
                        </button>
                    </div>
                </div>
                <div id="chart-container"></div>
            </div>
        </div>
    </div>

    <script>
        const payload = __DATA_JSON__;
        const rawData = payload.data;
        const algorithms = payload.algorithms;
        const sequences = payload.sequences;

        const allMetricKeys = [
            "Mean IoU",
            "Mean Corner Error (px)",
            "Mean Corner Error (%)",
            "Mean Pointing Error",
            "Mean Inference Time (ms)"
        ];

        const metricShortNames = {
            "Mean IoU": "IoU",
            "Mean Corner Error (px)": "Corner px",
            "Mean Corner Error (%)": "Corner %",
            "Mean Pointing Error": "Pointing",
            "Mean Inference Time (ms)": "Time ms"
        };

        // ULL Academic Palette tuned for both dark and light modes
        const colorPalette = [
            '#a855f7', // ULL Vibrant Purple
            '#eab308', // ULL Gold/Bronze
            '#38bdf8', // Sky / Cyan
            '#ec4899', // Magenta
            '#34d399', // Emerald
            '#f97316', // Warm Amber
            '#818cf8', // Indigo
            '#f43f5e'  // Coral
        ];
        
        const algoColorMap = {};
        algorithms.forEach((algo, idx) => {
            algoColorMap[algo] = colorPalette[idx % colorPalette.length];
        });

        // Theme management
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            document.getElementById('theme-btn').textContent = (next === 'dark') ? '☀️ Light Mode' : '🌙 Dark Mode';
            updateView();
        }

        // Populate Sequence / Scope Selector
        const scopeSelect = document.getElementById('scope-select');
        sequences.forEach(seq => {
            const opt = document.createElement('option');
            opt.value = seq;
            opt.textContent = `Sequence: ${seq} (Bar per Frame)`;
            scopeSelect.appendChild(opt);
        });

        // Populate Algorithm Checkboxes
        const algoContainer = document.getElementById('algo-checkboxes');
        algorithms.forEach(algo => {
            const label = document.createElement('label');
            label.className = 'checkbox-label';
            label.innerHTML = `
                <input type="checkbox" value="${algo}" checked onchange="updateView()">
                <span class="algo-dot" style="background-color: ${algoColorMap[algo]}"></span>
                ${algo}
            `;
            algoContainer.appendChild(label);
        });

        function copySequenceName() {
            const selectedScope = document.getElementById('scope-select').value;
            if (!selectedScope || selectedScope === '__GLOBAL__') return;
            navigator.clipboard.writeText(selectedScope).then(() => {
                const btn = document.getElementById('copy-title-btn');
                if (btn) {
                    btn.classList.add('copied');
                    btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg><span>Copied sequence!</span>`;
                    setTimeout(() => {
                        btn.classList.remove('copied');
                        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg><span>Copy Sequence</span>`;
                    }, 1800);
                }
            }).catch(err => {
                console.error('Failed to copy sequence name: ', err);
            });
        }

        function updateView() {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            const selectedMetric = document.getElementById('metric-select').value;
            const selectedScope = document.getElementById('scope-select').value;
            
            const checkedAlgos = Array.from(
                document.querySelectorAll('#algo-checkboxes input:checked')
            ).map(cb => cb.value);

            const isGlobal = (selectedScope === '__GLOBAL__');
            
            // 1. Update Title & Header
            const chartTitleEl = document.getElementById('chart-title');
            const copyBtn = document.getElementById('copy-title-btn');
            const titleText = isGlobal 
                ? `${selectedMetric} by Sequence (Global Mode)` 
                : `${selectedMetric} by Frame — ${selectedScope}`;
            if (chartTitleEl) {
                chartTitleEl.textContent = titleText;
            }
            if (copyBtn) {
                if (isGlobal) {
                    copyBtn.style.display = 'none';
                } else {
                    copyBtn.style.display = 'inline-flex';
                    copyBtn.title = `Copy sequence name: ${selectedScope}`;
                }
            }

            // 2. Update Summary Card
            const summaryTitle = document.getElementById('summary-title');
            const summaryList = document.getElementById('summary-list');
            summaryList.innerHTML = '';

            if (isGlobal) {
                summaryTitle.textContent = "Global Averages (All Sequences)";
            } else {
                summaryTitle.textContent = `Sequence Average: ${selectedScope}`;
            }

            let traces = [];

            if (isGlobal) {
                // GLOBAL MODE:
                checkedAlgos.forEach(algo => {
                    const xVals = [];
                    const yVals = [];
                    
                    const metricSums = {};
                    allMetricKeys.forEach(k => { metricSums[k] = { sum: 0, count: 0 }; });

                    sequences.forEach(seq => {
                        const item = rawData.find(d => d.algorithm === algo && d.sequence === seq);
                        if (item && item.aggregated) {
                            allMetricKeys.forEach(k => {
                                if (item.aggregated[k] !== undefined && item.aggregated[k] !== null) {
                                    metricSums[k].sum += item.aggregated[k];
                                    metricSums[k].count++;
                                }
                            });
                            
                            if (item.aggregated[selectedMetric] !== undefined) {
                                xVals.push(seq);
                                yVals.push(item.aggregated[selectedMetric]);
                            }
                        }
                    });

                    // Render summary item
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'summary-item';
                    
                    let metricsHtml = '<div class="summary-metrics-grid">';
                    allMetricKeys.forEach(k => {
                        const count = metricSums[k].count;
                        const avg = count > 0 ? (metricSums[k].sum / count) : 0;
                        const isActive = (k === selectedMetric) ? ' active-metric' : '';
                        metricsHtml += `
                            <div class="metric-stat${isActive}">
                                <span class="metric-stat-label">${metricShortNames[k]}</span>
                                <span class="metric-stat-val">${avg.toFixed(3)}</span>
                            </div>
                        `;
                    });
                    metricsHtml += '</div>';

                    itemDiv.innerHTML = `
                        <div class="summary-item-header">
                            <span class="summary-algo-name">
                                <span class="algo-dot" style="background-color: ${algoColorMap[algo]}"></span>
                                ${algo}
                            </span>
                            <span class="summary-sub">${metricSums[selectedMetric].count} sequences</span>
                        </div>
                        ${metricsHtml}
                    `;
                    summaryList.appendChild(itemDiv);

                    traces.push({
                        name: algo,
                        x: xVals,
                        y: yVals,
                        type: 'bar',
                        marker: { color: algoColorMap[algo] }
                    });
                });

            } else {
                // SEQUENCE MODE:
                checkedAlgos.forEach(algo => {
                    const item = rawData.find(d => d.algorithm === algo && d.sequence === selectedScope);
                    const xVals = [];
                    const yVals = [];

                    const metricSums = {};
                    allMetricKeys.forEach(k => { metricSums[k] = { sum: 0, count: 0 }; });

                    if (item && item.frames && item.frames.length > 0) {
                        item.frames.forEach(f => {
                            allMetricKeys.forEach(k => {
                                if (f[k] !== undefined && f[k] !== null) {
                                    metricSums[k].sum += f[k];
                                    metricSums[k].count++;
                                }
                            });
                            
                            xVals.push(f.frame);
                            yVals.push(f[selectedMetric] || 0.0);
                        });
                    }

                    // Render summary item
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'summary-item';

                    let metricsHtml = '<div class="summary-metrics-grid">';
                    allMetricKeys.forEach(k => {
                        let avg = 0;
                        if (metricSums[k].count > 0) {
                            avg = metricSums[k].sum / metricSums[k].count;
                        } else if (item && item.aggregated && item.aggregated[k] !== undefined) {
                            avg = item.aggregated[k];
                        }
                        const isActive = (k === selectedMetric) ? ' active-metric' : '';
                        metricsHtml += `
                            <div class="metric-stat${isActive}">
                                <span class="metric-stat-label">${metricShortNames[k]}</span>
                                <span class="metric-stat-val">${avg.toFixed(3)}</span>
                            </div>
                        `;
                    });
                    metricsHtml += '</div>';

                    itemDiv.innerHTML = `
                        <div class="summary-item-header">
                            <span class="summary-algo-name">
                                <span class="algo-dot" style="background-color: ${algoColorMap[algo]}"></span>
                                ${algo}
                            </span>
                            <span class="summary-sub">${metricSums[selectedMetric].count} frames</span>
                        </div>
                        ${metricsHtml}
                    `;
                    summaryList.appendChild(itemDiv);

                    traces.push({
                        name: algo,
                        x: xVals,
                        y: yVals,
                        type: 'bar',
                        marker: { color: algoColorMap[algo] }
                    });
                });
            }

            const gridColor = isDark ? '#272147' : '#e5e7eb';
            const titleColor = isDark ? '#f3f4f6' : '#1f2937';
            const axisTextColor = isDark ? '#9ca3af' : '#6b7280';

            const xaxisConfig = isGlobal ? {
                title: { 
                    text: 'Sequence', 
                    font: { color: axisTextColor, size: 12, family: 'Montserrat' },
                    standoff: 15
                },
                type: 'category',
                tickfont: { color: titleColor, size: 10, family: 'Inconsolata' },
                tickangle: -40,
                automargin: true,
                gridcolor: gridColor
            } : {
                title: { 
                    text: 'Frame Number', 
                    font: { color: axisTextColor, size: 12, family: 'Montserrat' },
                    standoff: 15
                },
                tickfont: { color: titleColor, size: 11, family: 'Inconsolata' },
                tickangle: 0,
                automargin: true,
                gridcolor: gridColor,
                rangeslider: { visible: true, thickness: 0.06, bgcolor: isDark ? '#141124' : '#f0f0f0' }
            };

            const layout = {
                barmode: 'group',
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { family: 'Montserrat', color: titleColor },
                xaxis: xaxisConfig,
                yaxis: {
                    title: { text: selectedMetric, font: { color: axisTextColor, size: 12, family: 'Montserrat' } },
                    tickfont: { color: titleColor, size: 12, family: 'Inconsolata' },
                    gridcolor: gridColor
                },
                showlegend: false,
                margin: { t: 20, b: isGlobal ? 130 : 70, l: 60, r: 30 }
            };

            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false
            };

            Plotly.newPlot('chart-container', traces, layout, config);
        }

        // Initial render
        updateView();
    </script>
</body>
</html>
"""

def generate_html_report(results_payload, output_path="docs/index.html"):
    """
    Generates a standalone, interactive HTML dashboard with ULL dark/light mode
    and the official ULL logo embedded. Default output is docs/index.html so it
    is automatically served by GitHub Pages.
    """
    logo_b64 = get_ull_logo_base64()
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="ULL Logo" class="ull-logo-img">'
    else:
        logo_html = '<div style="background:#57068C;color:#fff;font-weight:800;padding:6px 12px;border-radius:8px;">ULL</div>'
        
    data_json = json.dumps(results_payload)
    
    html_content = HTML_TEMPLATE.replace("__LOGO_HTML__", logo_html).replace("__DATA_JSON__", data_json)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Interactive comparison report (ULL Theme with Dark Mode & Official Logo) generated at: {os.path.abspath(output_path)}")

def main():
    parser = argparse.ArgumentParser(description="Generate interactive HTML comparison dashboard (ULL Theme)")
    parser.add_argument("--results_dir", default="results", help="Directory containing the results")
    parser.add_argument("--output", default="docs/index.html", help="Path to output HTML file (default: docs/index.html for GitHub Pages)")
    args = parser.parse_args()
    
    print(f"Loading results from {args.results_dir}...")
    results_payload = load_results(args.results_dir)
    
    if not results_payload["data"]:
        print("No evaluation records found. Run evaluate_algorithm.py first.")
        return
        
    generate_html_report(results_payload, output_path=args.output)

if __name__ == "__main__":
    main()
