'use strict';

let portfolioInited = false;

const renderHoldings = (holdings) => {
  const tbody = document.getElementById('holdings-body');
  const summaryEl = document.getElementById('portfolio-summary');

  if (!holdings?.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-msg" style="text-align:center;padding:2rem">No holdings yet. Add a position above.</td></tr>';
    summaryEl.innerHTML = '<p class="summary-label" style="padding:1rem">No positions in portfolio.</p>';
    return;
  }

  let totalValue = 0;
  let totalCost = 0;
  holdings.forEach(h => {
    const cost = h.shares * h.avg_price;
    const current = h.current_price ? h.shares * h.current_price : cost;
    totalValue += current;
    totalCost += cost;
  });

  const totalPnl = totalValue - totalCost;
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0;
  const pnlClass = totalPnl >= 0 ? 'positive' : 'negative';

  summaryEl.innerHTML = `
    <div class="portfolio-summary-grid">
      <div class="pf-sum-item">
        <p class="summary-label">Portfolio Value</p>
        <p class="summary-value">${formatCurrency(totalValue)}</p>
      </div>
      <div class="pf-sum-item">
        <p class="summary-label">Total Cost</p>
        <p class="summary-value">${formatCurrency(totalCost)}</p>
      </div>
      <div class="pf-sum-item">
        <p class="summary-label">Total P&amp;L</p>
        <p class="summary-value ${pnlClass}">${formatCurrency(totalPnl)}</p>
      </div>
      <div class="pf-sum-item">
        <p class="summary-label">Return</p>
        <p class="summary-value ${pnlClass}">${totalPnlPct.toFixed(2)}%</p>
      </div>
    </div>
  `;

  tbody.innerHTML = holdings.map(h => {
    const cost = h.shares * h.avg_price;
    const current = h.current_price ? h.shares * h.current_price : cost;
    const pnl = current - cost;
    const pnlPct = cost > 0 ? (pnl / cost) * 100 : 0;
    const cls = pnl >= 0 ? 'positive' : 'negative';
    return `
      <tr>
        <td><span class="ticker-badge">${h.ticker}</span></td>
        <td>${h.shares.toLocaleString()}</td>
        <td>${formatCurrency(h.avg_price)}</td>
        <td>${h.current_price ? formatCurrency(h.current_price) : '<span class="text-muted">—</span>'}</td>
        <td class="${cls}">${formatCurrency(pnl)}</td>
        <td class="${cls}">${pnlPct.toFixed(2)}%</td>
        <td>
          <button class="btn-icon btn-icon-danger" data-remove="${h.id}" title="Remove">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => removeHolding(parseInt(btn.dataset.remove)));
  });
};

const loadPortfolio = async () => {
  showLoading(true);
  try {
    const data = await api.portfolio.get();
    renderHoldings(data.holdings);
  } catch (err) {
    showToast('Failed to load portfolio: ' + err.message, 'error');
  } finally {
    showLoading(false);
  }
};

const removeHolding = async (id) => {
  if (!confirm('Remove this holding from your portfolio?')) return;
  try {
    await api.portfolio.remove(id);
    await loadPortfolio();
    showToast('Holding removed', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

const initPortfolio = () => {
  if (!portfolioInited) {
    portfolioInited = true;
    document.getElementById('add-stock-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.portfolio.add({
          ticker: fd.get('ticker').toUpperCase(),
          shares: parseFloat(fd.get('shares')),
          avg_price: parseFloat(fd.get('avg_price')),
        });
        e.target.reset();
        await loadPortfolio();
        showToast('Position added', 'success');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }
  loadPortfolio();
};
