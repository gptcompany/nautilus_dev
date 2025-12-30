/**
 * Build Script - Bundle dashboard into standalone HTML file.
 *
 * Usage:
 *   node build.js          - Build production bundle
 *   node build.js --watch  - Watch mode for development
 */

const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');

const DIST_DIR = path.join(__dirname, 'dist');
const SRC_DIR = path.join(__dirname, 'src');
const STYLES_DIR = path.join(__dirname, 'styles');

// Ensure dist directory exists
if (!fs.existsSync(DIST_DIR)) {
    fs.mkdirSync(DIST_DIR, { recursive: true });
}

/**
 * Build JavaScript bundle.
 */
async function buildJS() {
    console.log('Building JavaScript bundle...');

    await esbuild.build({
        entryPoints: [path.join(SRC_DIR, 'app.js')],
        bundle: true,
        minify: true,
        format: 'iife',
        globalName: 'Dashboard',
        outfile: path.join(DIST_DIR, 'bundle.js'),
        sourcemap: false,
    });

    console.log('  ✓ bundle.js');
}

/**
 * Read and minify CSS.
 */
function buildCSS() {
    console.log('Building CSS...');

    const cssPath = path.join(STYLES_DIR, 'main.css');
    let css = '';

    if (fs.existsSync(cssPath)) {
        css = fs.readFileSync(cssPath, 'utf8');
        // Basic minification
        css = css
            .replace(/\/\*[\s\S]*?\*\//g, '')  // Remove comments
            .replace(/\s+/g, ' ')              // Collapse whitespace
            .replace(/\s*([{}:;,])\s*/g, '$1') // Remove space around punctuation
            .trim();
    }

    console.log('  ✓ main.css');
    return css;
}

/**
 * Get Lightweight Charts library.
 */
function getLightweightCharts() {
    console.log('Including Lightweight Charts...');

    // Try to read from node_modules
    const lwcPath = path.join(__dirname, 'node_modules', 'lightweight-charts', 'dist', 'lightweight-charts.standalone.production.js');

    if (fs.existsSync(lwcPath)) {
        console.log('  ✓ From node_modules');
        return fs.readFileSync(lwcPath, 'utf8');
    }

    // Fallback: Use CDN reference (not inlined)
    console.log('  ⚠ node_modules not found, using CDN reference');
    return null;
}

/**
 * Build standalone HTML file.
 */
async function buildHTML() {
    console.log('\nBuilding standalone HTML...\n');

    // Build components
    await buildJS();
    const css = buildCSS();
    const lwc = getLightweightCharts();

    // Read JS bundle
    const bundle = fs.readFileSync(path.join(DIST_DIR, 'bundle.js'), 'utf8');

    // Generate HTML
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Dashboard - Real-Time OI, Funding & Liquidations</title>
    <style>${css}</style>
</head>
<body>
    <div id="app">
        <!-- Header -->
        <header id="dashboard-header">
            <div class="header-left">
                <h1>Trading Dashboard</h1>
                <div id="connection-status" class="status disconnected">
                    <span class="status-dot"></span>
                    <span class="status-text">Disconnected</span>
                </div>
            </div>
            <div class="header-right">
                <select id="symbol-selector">
                    <option value="BTCUSDT-PERP">BTCUSDT-PERP</option>
                    <option value="ETHUSDT-PERP">ETHUSDT-PERP</option>
                </select>
            </div>
        </header>

        <!-- Main Content -->
        <main id="dashboard-main">
            <!-- Funding Display -->
            <section id="funding-section">
                <div id="funding-display">
                    <span class="funding-label">Funding Rate</span>
                    <span id="funding-value" class="funding-value neutral">--</span>
                    <span id="funding-next" class="funding-next">Next: --</span>
                </div>
            </section>

            <!-- Historical Data Controls -->
            <section id="historical-section">
                <div id="historical-controls">
                    <label for="date-from">From:</label>
                    <input type="date" id="date-from">
                    <label for="date-to">To:</label>
                    <input type="date" id="date-to">
                    <button id="load-historical">Load Historical</button>
                    <span id="historical-progress"></span>
                </div>
            </section>

            <!-- Charts -->
            <section id="charts-section">
                <div id="oi-chart-container" class="chart-container">
                    <div class="chart-header">
                        <span class="chart-title">Open Interest (USD)</span>
                    </div>
                    <div id="oi-chart" class="chart"></div>
                </div>

                <div id="funding-chart-container" class="chart-container">
                    <div class="chart-header">
                        <span class="chart-title">Funding Rate History (%)</span>
                    </div>
                    <div id="funding-chart" class="chart"></div>
                </div>
            </section>
        </main>

        <!-- Footer -->
        <footer id="dashboard-footer">
            <span>Data from: Binance, Bybit, Hyperliquid</span>
            <span id="last-update">Last update: --</span>
        </footer>
    </div>

    <!-- Lightweight Charts -->
    ${lwc ? `<script>${lwc}</script>` : '<script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>'}

    <!-- Application Bundle -->
    <script>${bundle}</script>
</body>
</html>`;

    // Write output
    const outputPath = path.join(DIST_DIR, 'dashboard.html');
    fs.writeFileSync(outputPath, html);

    // Report size
    const size = fs.statSync(outputPath).size;
    const sizeKB = (size / 1024).toFixed(1);

    console.log(`\n✓ Built ${outputPath}`);
    console.log(`  Size: ${sizeKB} KB`);
}

/**
 * Watch mode for development.
 */
async function watch() {
    console.log('Starting watch mode...\n');

    const ctx = await esbuild.context({
        entryPoints: [path.join(SRC_DIR, 'app.js')],
        bundle: true,
        format: 'iife',
        globalName: 'Dashboard',
        outfile: path.join(DIST_DIR, 'bundle.js'),
        sourcemap: true,
    });

    await ctx.watch();
    console.log('Watching for changes...');
}

// Main
const args = process.argv.slice(2);

if (args.includes('--watch')) {
    watch().catch(console.error);
} else {
    buildHTML().catch(err => {
        console.error('Build failed:', err);
        process.exit(1);
    });
}
