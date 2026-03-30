'use strict';

let netWorthChart = null;
let expenseChart = null;

const renderSummaryCards = (totals) => {
  const cards = [
    { label: 'Total Income', value: totals.income, icon: 'fa-circle-dollar-to-slot', cls: 'green' },
    { label: 'Total Expenses', value: totals.expenses, icon: 'fa-receipt', cls: 'red' },
    { label: 'Total Assets', value: totals.assets, icon: 'fa-building-columns', cls: 'blue' },
    { label: 'Total Debts', value: totals.debts, icon: 'fa-credit-card', cls: 'orange' },
    { label: 'Net Worth', value: totals.netWorth, icon: 'fa-wallet', cls: totals.netWorth >= 0 ? 'primary' : 'red' },
    { label: 'Monthly Savings', value: totals.monthlySavings, icon: 'fa-piggy-bank', cls: totals.monthlySavings >= 0 ? 'green' : 'red' },
  ];
  document.getElementById('summary-cards').innerHTML = cards.map(c => `
    <div class="card summary-card">
      <div class="summary-icon icon-${c.cls}">
        <i class="fa-solid ${c.icon}"></i>
      </div>
      <div class="summary-body">
        <p class="summary-label">${c.label}</p>
        <p class="summary-value ${c.value < 0 ? 'negative' : ''}">${formatCurrency(c.value)}</p>
      </div>
    </div>
  `).join('');
};

const renderNetWorthChart = (history) => {
  const ctx = document.getElementById('net-worth-chart').getContext('2d');
  if (netWorthChart) netWorthChart.destroy();
  netWorthChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: history.map(h => h.month),
      datasets: [{
        label: 'Net Worth',
        data: history.map(h => h.netWorth),
        borderColor: '#1029CC',
        backgroundColor: 'rgba(16,41,204,0.07)',
        borderWidth: 2.5,
        pointRadius: 4,
        pointBackgroundColor: '#1029CC',
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          ticks: { callback: (v) => formatCurrency(v) },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        x: { grid: { display: false } },
      },
    },
  });
};

const renderExpenseChart = (breakdown) => {
  const ctx = document.getElementById('expense-chart').getContext('2d');
  if (expenseChart) expenseChart.destroy();
  const items = breakdown.breakdown || [];
  if (!items.length) {
    ctx.canvas.parentElement.innerHTML = '<p class="empty-msg">No expense data yet.</p>';
    return;
  }
  const labels = items.map(b => b.category);
  const data = items.map(b => b.amount);
  expenseChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: [
          '#1029CC', '#CC6123', '#27ae60', '#e74c3c',
          '#9b59b6', '#f39c12', '#1abc9c', '#e67e22',
        ],
        borderWidth: 2,
        borderColor: '#FAFAFC',
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, font: { size: 12 } } },
      },
    },
  });
};

const renderHealth = (health) => {
  const container = document.getElementById('health-container');
  const score = health.score;
  if (score === null || score === undefined) {
    container.innerHTML = '<p class="empty-msg">Add income data to see your financial health score.</p>';
    return;
  }
  const color = score >= 70 ? '#27ae60' : score >= 40 ? '#f39c12' : '#e74c3c';
  const circumference = 157;
  const dashLen = (score / 100) * circumference;
  container.innerHTML = `
    <div class="health-gauge-wrap">
      <div class="health-gauge">
        <svg viewBox="0 0 120 80" class="gauge-svg">
          <path d="M 10 70 A 50 50 0 0 1 110 70"
            fill="none" stroke="#DDDDE4" stroke-width="10" stroke-linecap="round"/>
          <path d="M 10 70 A 50 50 0 0 1 110 70"
            fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round"
            stroke-dasharray="${dashLen} ${circumference}" />
        </svg>
        <div class="gauge-score" style="color:${color}">${Math.round(score)}</div>
        <div class="gauge-label">/ 100</div>
      </div>
      <div class="gauge-desc">
        <p style="color:${color};font-weight:600;font-size:1.1rem">
          ${score >= 70 ? 'Excellent' : score >= 40 ? 'Fair' : 'Needs Attention'}
        </p>
        <p class="text-muted">Based on income, expenses, savings ratio, and debt load</p>
      </div>
    </div>
  `;
};

const renderDashboardRecs = (recs) => {
  const grid = document.getElementById('recommendations-grid');
  if (!recs?.length) {
    grid.innerHTML = '<p class="empty-msg">No recommendations available.</p>';
    return;
  }
  grid.innerHTML = recs.slice(0, 6).map(r => `
    <div class="rec-card">
      <div class="rec-header">
        <span class="rec-ticker">${r.ticker}</span>
        <span class="signal-chip signal-${r.prediction}">${r.prediction}</span>
      </div>
      <div class="rec-prices">
        <div class="price-item">
          <span class="price-label">Current</span>
          <span class="price-val">${formatCurrency(r.current_price)}</span>
        </div>
        <div class="price-item">
          <span class="price-label">Predicted</span>
          <span class="price-val">${formatCurrency(r.predicted_price)}</span>
        </div>
      </div>
      <div class="confidence-wrap">
        <span class="conf-label">Confidence</span>
        <div class="conf-bar-bg">
          <div class="conf-bar" style="width:${(r.confidence * 100).toFixed(0)}%"></div>
        </div>
        <span class="conf-pct">${(r.confidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  `).join('');
};

const initDashboard = async () => {
  showLoading(true);
  try {
    const [dash, health, breakdown, history, recs] = await Promise.allSettled([
      api.dashboard.get(),
      api.dashboard.health(),
      api.dashboard.expenseBreakdown(),
      api.dashboard.netWorthHistory(),
      api.stocks.recommendations(),
    ]);

    if (dash.status === 'fulfilled' && dash.value?.totals) {
      renderSummaryCards(dash.value.totals);
    }
    if (history.status === 'fulfilled' && history.value?.history) {
      renderNetWorthChart(history.value.history);
    }
    if (breakdown.status === 'fulfilled') {
      renderExpenseChart(breakdown.value);
    }
    if (health.status === 'fulfilled') {
      renderHealth(health.value);
    }
    if (recs.status === 'fulfilled' && recs.value?.recommendations) {
      renderDashboardRecs(recs.value.recommendations);
    }
  } catch (err) {
    showToast('Failed to load dashboard: ' + err.message, 'error');
  } finally {
    showLoading(false);
  }
};
