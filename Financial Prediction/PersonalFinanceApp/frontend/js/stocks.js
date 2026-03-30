'use strict';

let stocksInited = false;
let searchTimer = null;

const renderStockCard = (s) => `
  <div class="rec-card">
    <div class="rec-header">
      <span class="rec-ticker">${s.ticker}</span>
      <span class="signal-chip signal-${s.prediction}">${s.prediction}</span>
    </div>
    <div class="rec-prices">
      <div class="price-item">
        <span class="price-label">Current</span>
        <span class="price-val">${formatCurrency(s.current_price)}</span>
      </div>
      <div class="price-item">
        <span class="price-label">Predicted</span>
        <span class="price-val ${s.predicted_price > s.current_price ? 'positive' : 'negative'}">
          ${formatCurrency(s.predicted_price)}
        </span>
      </div>
    </div>
    <div class="confidence-wrap">
      <span class="conf-label">Confidence</span>
      <div class="conf-bar-bg">
        <div class="conf-bar conf-bar-${s.prediction}" style="width:${(s.confidence * 100).toFixed(0)}%"></div>
      </div>
      <span class="conf-pct">${(s.confidence * 100).toFixed(0)}%</span>
    </div>
  </div>
`;

const doSearch = async (query) => {
  const resultsEl = document.getElementById('search-results');
  if (!query.trim()) {
    resultsEl.innerHTML = '';
    return;
  }
  resultsEl.innerHTML = '<p class="text-muted" style="padding:1rem">Searching...</p>';
  try {
    const data = await api.stocks.search(query);
    if (!data.predictions?.length) {
      resultsEl.innerHTML = '<p class="empty-msg">No results found.</p>';
      return;
    }
    resultsEl.innerHTML = data.predictions.map(renderStockCard).join('');
  } catch (err) {
    resultsEl.innerHTML = `<p class="empty-msg">Search failed: ${err.message}</p>`;
  }
};

const loadRecommendations = async () => {
  const grid = document.getElementById('buy-signals-grid');
  grid.innerHTML = '<p class="text-muted" style="padding:1rem">Loading recommendations...</p>';
  try {
    const data = await api.stocks.recommendations();
    if (!data.recommendations?.length) {
      grid.innerHTML = '<p class="empty-msg">No recommendations available.</p>';
      return;
    }
    grid.innerHTML = data.recommendations.map(renderStockCard).join('');
  } catch (err) {
    grid.innerHTML = `<p class="empty-msg">Failed to load: ${err.message}</p>`;
  }
};

const initStocks = () => {
  if (!stocksInited) {
    stocksInited = true;
    document.getElementById('stock-search').addEventListener('input', (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => doSearch(e.target.value), 400);
    });
  }
  loadRecommendations();
};
