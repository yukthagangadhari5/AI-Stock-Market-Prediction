async function runPrediction() {
    const ticker = document.getElementById('ticker').value.trim().toUpperCase();
    const days   = document.getElementById('days').value;
  
    if (!ticker) { alert('Please enter a stock ticker.'); return; }
  
    document.getElementById('results').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('btn-text').textContent = '⏳ Running…';
  
    try {
      const res  = await fetch('/predict', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ ticker, days }),
      });
      const data = await res.json();
  
      if (data.error) { alert('Error: ' + data.error); return; }
  
      renderStats(data);
      renderChart(data);
  
      document.getElementById('loading').classList.add('hidden');
      document.getElementById('results').classList.remove('hidden');
    } catch (e) {
      alert('Request failed: ' + e.message);
    } finally {
      document.getElementById('btn-text').textContent = '🚀 Predict';
      document.getElementById('loading').classList.add('hidden');
    }
  }
  
  function renderStats(data) {
    const change = data.predicted_next - data.current_price;
    const pct    = ((change / data.current_price) * 100).toFixed(2);
    const color  = change >= 0 ? '#10b981' : '#ef4444';
    const arrow  = change >= 0 ? '▲' : '▼';
  
    document.getElementById('stats-row').innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Current Price</div>
        <div class="stat-value">$${data.current_price.toFixed(2)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Next Day Forecast</div>
        <div class="stat-value" style="color:${color}">${arrow} $${data.predicted_next.toFixed(2)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Expected Change</div>
        <div class="stat-value" style="color:${color}">${pct}%</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Ticker</div>
        <div class="stat-value">${data.ticker}</div>
      </div>
    `;
  }
  
  function renderChart(data) {
    const traces = [
      {
        x: data.historical_dates,
        y: data.actual_prices,
        name: 'Actual',
        type: 'scatter', mode: 'lines',
        line: { color: '#6366f1', width: 2 },
      },
      {
        x: data.historical_dates,
        y: data.predicted_prices,
        name: 'Predicted (Test)',
        type: 'scatter', mode: 'lines',
        line: { color: '#f59e0b', width: 2, dash: 'dot' },
      },
      {
        x: data.future_dates,
        y: data.future_prices,
        name: 'Forecast',
        type: 'scatter', mode: 'lines',
        line: { color: '#10b981', width: 2.5 },
        fill: 'tozeroy', fillcolor: 'rgba(16,185,129,0.05)',
      },
    ];
  
    const layout = {
      title:      { text: `${data.ticker} — Price Prediction`, font: { color: '#f1f5f9', size: 18 } },
      paper_bgcolor: '#111827',
      plot_bgcolor:  '#111827',
      font:          { color: '#94a3b8' },
      xaxis: { gridcolor: '#1f2937', showgrid: true },
      yaxis: { gridcolor: '#1f2937', showgrid: true, tickprefix: '$' },
      legend: { bgcolor: 'transparent' },
      hovermode: 'x unified',
      margin: { t: 60, b: 50, l: 60, r: 20 },
    };
  
    Plotly.newPlot('chart-container', traces, layout, { responsive: true, displayModeBar: false });
  }