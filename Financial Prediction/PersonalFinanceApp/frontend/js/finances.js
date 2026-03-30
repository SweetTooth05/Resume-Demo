'use strict';

const INCOME_CATS = ['Salary', 'Freelance', 'Investment', 'Business', 'Other'];
const EXPENSE_CATS = ['Housing', 'Transportation', 'Food', 'Utilities', 'Entertainment', 'Healthcare', 'Other'];
const ASSET_CATS = ['Cash', 'Investments', 'Real Estate', 'Vehicles', 'Other'];
const DEBT_CATS = ['Credit Card', 'Student Loan', 'Mortgage', 'Car Loan', 'Personal Loan', 'Other'];

let finSummary = null;
let financesInited = false;

const renderItems = (listId, items, deleteFn, editFn) => {
  const el = document.getElementById(listId);
  if (!items?.length) {
    el.innerHTML = '<div class="empty-msg">No entries yet. Add one above.</div>';
    return;
  }
  el.innerHTML = items.map(item => `
    <div class="item-row" data-id="${item.id}">
      <span class="item-name">${item.name}</span>
      <span class="item-amount">${formatCurrency(item.amount)}</span>
      <span class="category-chip">${item.category}</span>
      <div class="item-actions">
        <button class="btn-icon" data-action="edit" data-id="${item.id}" title="Edit">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button class="btn-icon btn-icon-danger" data-action="delete" data-id="${item.id}" title="Delete">
          <i class="fa-solid fa-trash"></i>
        </button>
      </div>
    </div>
  `).join('');

  el.querySelectorAll('[data-action="edit"]').forEach(btn => {
    btn.addEventListener('click', () => editFn(parseInt(btn.dataset.id)));
  });
  el.querySelectorAll('[data-action="delete"]').forEach(btn => {
    btn.addEventListener('click', () => deleteFn(parseInt(btn.dataset.id)));
  });
};

const loadFinances = async () => {
  showLoading(true);
  try {
    const data = await api.financial.summary();
    finSummary = data;
    renderItems('income-list', data.items?.incomes, deleteIncome, editIncome);
    renderItems('expense-list', data.items?.expenses, deleteExpense, editExpense);
    renderItems('asset-list', data.items?.assets, deleteAsset, editAsset);
    renderItems('debt-list', data.items?.debts, deleteDebt, editDebt);
  } catch (err) {
    showToast('Failed to load finances: ' + err.message, 'error');
  } finally {
    showLoading(false);
  }
};

const makeEditModal = (title, fields, onSave) => {
  const existing = document.getElementById('edit-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'edit-modal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3>${title}</h3>
        <button class="modal-close"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <form id="edit-modal-form">
        ${fields.map(f => `
          <div class="form-group">
            <label>${f.label}</label>
            ${f.type === 'select'
              ? `<select name="${f.name}">${f.options.map(o => `<option value="${o}" ${o === f.value ? 'selected' : ''}>${o}</option>`).join('')}</select>`
              : `<input type="${f.type}" name="${f.name}" value="${f.value || ''}" step="${f.step || ''}" required>`
            }
          </div>
        `).join('')}
        <div id="modal-error" class="error-message"></div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary modal-cancel">Cancel</button>
          <button type="submit" class="btn btn-primary">Save</button>
        </div>
      </form>
    </div>
  `;

  document.body.appendChild(modal);
  modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
  modal.querySelector('.modal-cancel').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });

  modal.querySelector('#edit-modal-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const errEl = document.getElementById('modal-error');
    errEl.textContent = '';
    try {
      await onSave(fd);
      modal.remove();
      await loadFinances();
      showToast('Updated successfully', 'success');
    } catch (err) {
      errEl.textContent = err.message;
    }
  });
};

const deleteIncome = async (id) => {
  if (!confirm('Delete this income entry?')) return;
  try {
    await api.financial.deleteIncome(id);
    await loadFinances();
    showToast('Deleted', 'success');
  } catch (e) { showToast(e.message, 'error'); }
};

const deleteExpense = async (id) => {
  if (!confirm('Delete this expense?')) return;
  try {
    await api.financial.deleteExpense(id);
    await loadFinances();
    showToast('Deleted', 'success');
  } catch (e) { showToast(e.message, 'error'); }
};

const deleteAsset = async (id) => {
  if (!confirm('Delete this asset?')) return;
  try {
    await api.financial.deleteAsset(id);
    await loadFinances();
    showToast('Deleted', 'success');
  } catch (e) { showToast(e.message, 'error'); }
};

const deleteDebt = async (id) => {
  if (!confirm('Delete this debt?')) return;
  try {
    await api.financial.deleteDebt(id);
    await loadFinances();
    showToast('Deleted', 'success');
  } catch (e) { showToast(e.message, 'error'); }
};

const editIncome = (id) => {
  const item = finSummary?.items?.incomes?.find(i => i.id === id);
  if (!item) return;
  makeEditModal('Edit Income', [
    { label: 'Name', type: 'text', name: 'name', value: item.name },
    { label: 'Amount ($)', type: 'number', name: 'amount', value: item.amount, step: '0.01' },
    { label: 'Category', type: 'select', name: 'category', value: item.category, options: INCOME_CATS },
  ], (fd) => api.financial.updateIncome(id, {
    name: fd.get('name'),
    amount: parseFloat(fd.get('amount')),
    category: fd.get('category'),
  }));
};

const editExpense = (id) => {
  const item = finSummary?.items?.expenses?.find(i => i.id === id);
  if (!item) return;
  makeEditModal('Edit Expense', [
    { label: 'Name', type: 'text', name: 'name', value: item.name },
    { label: 'Amount ($)', type: 'number', name: 'amount', value: item.amount, step: '0.01' },
    { label: 'Category', type: 'select', name: 'category', value: item.category, options: EXPENSE_CATS },
  ], (fd) => api.financial.updateExpense(id, {
    name: fd.get('name'),
    amount: parseFloat(fd.get('amount')),
    category: fd.get('category'),
  }));
};

const editAsset = (id) => {
  const item = finSummary?.items?.assets?.find(i => i.id === id);
  if (!item) return;
  makeEditModal('Edit Asset', [
    { label: 'Name', type: 'text', name: 'name', value: item.name },
    { label: 'Value ($)', type: 'number', name: 'amount', value: item.amount, step: '0.01' },
    { label: 'Category', type: 'select', name: 'category', value: item.category, options: ASSET_CATS },
  ], (fd) => api.financial.updateAsset(id, {
    name: fd.get('name'),
    amount: parseFloat(fd.get('amount')),
    category: fd.get('category'),
  }));
};

const editDebt = (id) => {
  const item = finSummary?.items?.debts?.find(i => i.id === id);
  if (!item) return;
  makeEditModal('Edit Debt', [
    { label: 'Name', type: 'text', name: 'name', value: item.name },
    { label: 'Balance ($)', type: 'number', name: 'amount', value: item.amount, step: '0.01' },
    { label: 'Category', type: 'select', name: 'category', value: item.category, options: DEBT_CATS },
  ], (fd) => api.financial.updateDebt(id, {
    name: fd.get('name'),
    amount: parseFloat(fd.get('amount')),
    category: fd.get('category'),
  }));
};

const initFinances = () => {
  if (!financesInited) {
    financesInited = true;

    document.querySelectorAll('#page-finances .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#page-finances .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('#page-finances .tab-content').forEach(t => t.classList.add('hidden'));
        document.getElementById(`tab-${btn.dataset.tab}`).classList.remove('hidden');
      });
    });

    document.getElementById('add-income-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.financial.addIncome({
          name: fd.get('item_name'),
          amount: parseFloat(fd.get('amount')),
          category: fd.get('category'),
        });
        e.target.reset();
        await loadFinances();
        showToast('Income added', 'success');
      } catch (err) { showToast(err.message, 'error'); }
    });

    document.getElementById('add-expense-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.financial.addExpense({
          name: fd.get('item_name'),
          amount: parseFloat(fd.get('amount')),
          category: fd.get('category'),
        });
        e.target.reset();
        await loadFinances();
        showToast('Expense added', 'success');
      } catch (err) { showToast(err.message, 'error'); }
    });

    document.getElementById('add-asset-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.financial.addAsset({
          name: fd.get('item_name'),
          amount: parseFloat(fd.get('amount')),
          category: fd.get('category'),
        });
        e.target.reset();
        await loadFinances();
        showToast('Asset added', 'success');
      } catch (err) { showToast(err.message, 'error'); }
    });

    document.getElementById('add-debt-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.financial.addDebt({
          name: fd.get('item_name'),
          amount: parseFloat(fd.get('amount')),
          category: fd.get('category'),
        });
        e.target.reset();
        await loadFinances();
        showToast('Debt added', 'success');
      } catch (err) { showToast(err.message, 'error'); }
    });
  }

  loadFinances();
};
