import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Snackbar,
  Alert,
  CircularProgress,
  FormHelperText,
  Grid,
  IconButton,
  Tabs,
  Tab,
  Skeleton,
} from '@mui/material';
import { Add, Delete } from '@mui/icons-material';
import { financialAPI } from '../services/api';

const RECURRENCE_OPTIONS = [
  { value: 'none',        label: 'One-time / monthly budget' },
  { value: 'daily',       label: 'Daily' },
  { value: 'weekly',      label: 'Weekly' },
  { value: 'fortnightly', label: 'Biweekly' },
  { value: 'monthly',     label: 'Monthly' },
  { value: 'yearly',      label: 'Yearly' },
];

const RECURRENCE_LABELS: Record<string, string> = {
  none: 'Monthly',
  daily: 'Daily',
  weekly: 'Weekly',
  fortnightly: 'Biweekly',
  monthly: 'Monthly',
  yearly: 'Yearly',
};

const RECURRENCE_COLORS: Record<string, 'default' | 'success' | 'warning' | 'error' | 'primary' | 'secondary' | 'info'> = {
  none: 'default',
  daily: 'error',
  weekly: 'warning',
  fortnightly: 'info',
  monthly: 'primary',
  yearly: 'secondary',
};

type ItemType = 'income' | 'expense' | 'asset' | 'debt';

interface FinancialItem {
  id: string | number;
  name: string;
  amount: number;
  category: string;
  type: ItemType;
  recurrence_frequency?: string;
  recurrence_note?: string | null;
  payment_amount?: number | null;
  payment_frequency?: string | null;
  payment_note?: string | null;
}

interface SummaryState {
  total_income: number;
  total_expenses: number;
  total_assets: number;
  total_debts: number;
  monthly_savings: number;
  monthly_debt_payments: number;
  net_worth: number;
  cash_on_hand: number;
  total_stocks_value: number;
  total_property_assets: number;
}

const emptyForm = (type: ItemType = 'income') => ({
  name: '',
  amount: '',
  category: '',
  type,
  recurrence_frequency: 'monthly',
  recurrence_note: '',
  payment_amount: '',
  payment_frequency: 'monthly',
  payment_note: '',
});

const TYPE_CATEGORIES: Record<ItemType, string[]> = {
  income:  ['Salary', 'Freelance', 'Investment', 'Business', 'Other'],
  expense: ['Housing', 'Transportation', 'Food', 'Utilities', 'Entertainment', 'Healthcare', 'Other'],
  asset:   ['Cash', 'Investments', 'Real Estate', 'Vehicles', 'Other'],
  debt:    ['Credit Card', 'Student Loan', 'Mortgage', 'Car Loan', 'Personal Loan', 'Other'],
};

const fmt = (n: number) =>
  `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const TAB_TYPES: ItemType[] = ['income', 'expense', 'asset', 'debt'];
const TAB_LABELS = ['Income', 'Expenses', 'Assets', 'Debts'];

const Finances: React.FC = () => {
  const [items, setItems] = useState<FinancialItem[]>([]);
  const [summary, setSummary] = useState<SummaryState | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(emptyForm('income'));
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const formRef = useRef<HTMLDivElement>(null);
  const currentType = TAB_TYPES[activeTab];

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await financialAPI.getSummary();
      const s = data.summary;
      setSummary({
        total_income:         s.total_income ?? 0,
        total_expenses:       s.total_expenses ?? 0,
        total_assets:         s.total_assets ?? 0,
        total_debts:          s.total_debts ?? 0,
        monthly_savings:      s.monthly_savings ?? 0,
        monthly_debt_payments: s.monthly_debt_payments ?? 0,
        net_worth:            s.net_worth ?? 0,
        cash_on_hand:         s.cash_on_hand ?? 0,
        total_stocks_value:   s.total_stocks_value ?? 0,
        total_property_assets: s.total_property_assets ?? 0,
      });
      const rawItems: FinancialItem[] = [
        ...(data.items?.incomes  ?? []).map((i: Record<string, unknown>) => ({ ...i, type: 'income'  as const })),
        ...(data.items?.expenses ?? []).map((i: Record<string, unknown>) => ({ ...i, type: 'expense' as const })),
        ...(data.items?.assets   ?? []).map((i: Record<string, unknown>) => ({ ...i, type: 'asset'   as const })),
        ...(data.items?.debts    ?? []).map((i: Record<string, unknown>) => ({ ...i, type: 'debt'    as const })),
      ];
      setItems(rawItems);
    } catch {
      setSnackbar({ open: true, message: 'Could not load finances. Try refreshing.', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // Open inline form for current tab type
  const openForm = () => {
    setForm(emptyForm(currentType));
    setFormOpen(true);
    setTimeout(() => formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
  };

  const closeForm = () => {
    setFormOpen(false);
    setForm(emptyForm(currentType));
  };

  const handleTabChange = (_: React.SyntheticEvent, v: number) => {
    setActiveTab(v);
    setFormOpen(false);
    setConfirmDeleteId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.amount || !form.category) {
      setSnackbar({ open: true, message: 'Name, amount, and category are required.', severity: 'error' });
      return;
    }
    const amount = parseFloat(form.amount);
    if (Number.isNaN(amount) || amount <= 0) {
      setSnackbar({ open: true, message: 'Amount must be a positive number.', severity: 'error' });
      return;
    }
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = { name: form.name, amount, category: form.category };
      if (form.type === 'income' || form.type === 'expense') {
        payload.recurrence_frequency = form.recurrence_frequency;
        if (form.recurrence_note.trim()) payload.recurrence_note = form.recurrence_note.trim();
      }
      if (form.type === 'debt' && form.payment_amount.trim()) {
        const pa = parseFloat(form.payment_amount);
        if (!Number.isNaN(pa) && pa > 0) {
          payload.payment_amount = pa;
          payload.payment_frequency = form.payment_frequency || 'monthly';
          if (form.payment_note.trim()) payload.payment_note = form.payment_note.trim();
        }
      }
      await financialAPI.addItem(form.type, payload);
      await fetchData();
      setSnackbar({ open: true, message: `${form.type.charAt(0).toUpperCase() + form.type.slice(1)} added.`, severity: 'success' });
      closeForm();
    } catch {
      setSnackbar({ open: true, message: 'Failed to add item.', severity: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (item: FinancialItem) => {
    const key = `${item.type}-${item.id}`;
    if (confirmDeleteId !== key) {
      setConfirmDeleteId(key);
      setTimeout(() => setConfirmDeleteId((cur) => (cur === key ? null : cur)), 3000);
      return;
    }
    setConfirmDeleteId(null);
    try {
      await financialAPI.deleteItem(item.type, String(item.id));
      await fetchData();
      setSnackbar({ open: true, message: 'Removed.', severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: 'Failed to delete.', severity: 'error' });
    }
  };

  const visibleItems = items.filter((i) => i.type === currentType);

  // Summary total for current tab
  const tabTotal = (): string => {
    if (!summary) return '—';
    switch (currentType) {
      case 'income':  return fmt(summary.total_income);
      case 'expense': return fmt(summary.total_expenses);
      case 'asset':   return fmt(summary.total_assets);
      case 'debt':    return fmt(summary.total_debts);
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: { xs: 2, sm: 3, md: 4 }, overflow: 'auto' }}>
      {/* Heading */}
      <Box sx={{ mb: 3, animation: 'fadeUp 0.4s cubic-bezier(0.16,1,0.3,1) both' }}>
        <Typography
          variant="h4"
          sx={{
            fontFamily: '"Fraunces", Georgia, serif',
            fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 600,
            letterSpacing: '-0.03em',
            color: 'primary.dark',
          }}
        >
          Finances
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, maxWidth: 560 }}>
          For <strong>income</strong> and <strong>expenses</strong>, set recurrence to normalise monthly totals.
          Add <strong>Cash</strong> under Assets for bank balances. Stock values come from your portfolio.
        </Typography>
      </Box>

      {/* Summary strip */}
      {summary && (
        <Box
          className="stat-strip animate-fade-up animate-fade-up-2"
          sx={{ mb: 4, display: { xs: 'none', sm: 'flex' } }}
        >
          <Box className="stat-item">
            <span className="stat-label">Net worth</span>
            <span className="stat-value" style={{ color: 'var(--color-navy-900)' }}>{fmt(summary.net_worth)}</span>
          </Box>
          <Box className="stat-item">
            <span className="stat-label">Monthly savings</span>
            <span className="stat-value" style={{ color: summary.monthly_savings >= 0 ? 'var(--color-success)' : 'var(--color-error)' }}>
              {fmt(summary.monthly_savings)}
            </span>
          </Box>
          <Box className="stat-item">
            <span className="stat-label">Cash on hand</span>
            <span className="stat-value">{fmt(summary.cash_on_hand)}</span>
          </Box>
          <Box className="stat-item">
            <span className="stat-label">Debt payments / mo</span>
            <span className="stat-value">{fmt(summary.monthly_debt_payments)}</span>
          </Box>
        </Box>
      )}

      {/* Tabs */}
      <Box
        sx={{
          mb: 0,
          borderBottom: '1px solid',
          borderColor: 'divider',
          animation: 'fadeUp 0.4s 0.06s cubic-bezier(0.16,1,0.3,1) both',
        }}
      >
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          sx={{
            '& .MuiTab-root': { fontSize: '14px', fontWeight: 500, minWidth: 80 },
          }}
        >
          {TAB_LABELS.map((label, i) => (
            <Tab
              key={label}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {label}
                  {summary && (
                    <Typography
                      component="span"
                      sx={{
                        fontSize: '11px',
                        fontWeight: 600,
                        color: activeTab === i ? 'secondary.main' : 'text.tertiary',
                        display: { xs: 'none', sm: 'inline' },
                      }}
                    >
                      {i === 0 ? fmt(summary.total_income) :
                       i === 1 ? fmt(summary.total_expenses) :
                       i === 2 ? fmt(summary.total_assets) :
                                 fmt(summary.total_debts)}
                    </Typography>
                  )}
                </Box>
              }
            />
          ))}
        </Tabs>
      </Box>

      {/* Tab content */}
      <Box
        sx={{
          mt: 0,
          pt: 3,
          animation: 'fadeUp 0.35s 0.1s cubic-bezier(0.16,1,0.3,1) both',
        }}
      >
        {/* Add button + total */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Total: <strong>{tabTotal()}</strong>
          </Typography>
          <Button
            variant={formOpen ? 'outlined' : 'contained'}
            color="primary"
            startIcon={<Add />}
            onClick={formOpen ? closeForm : openForm}
            size="small"
          >
            {formOpen ? 'Cancel' : `Add ${currentType}`}
          </Button>
        </Box>

        {/* Inline form panel */}
        <Box
          ref={formRef}
          sx={{
            display: 'grid',
            gridTemplateRows: formOpen ? '1fr' : '0fr',
            transition: 'grid-template-rows 0.3s cubic-bezier(0.16,1,0.3,1)',
            mb: formOpen ? 3 : 0,
          }}
        >
          <Box sx={{ overflow: 'hidden' }}>
            <Box
              component="form"
              onSubmit={handleSubmit}
              sx={{
                p: 3,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 2,
                backgroundColor: 'background.paper',
                mt: 0.5,
              }}
            >
              <Typography variant="subtitle2" sx={{ mb: 2, color: 'primary.dark' }}>
                Add {currentType}
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    required
                    size="small"
                    label="Name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth required size="small">
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={form.category}
                      label="Category"
                      onChange={(e) => setForm({ ...form, category: e.target.value })}
                    >
                      {TYPE_CATEGORIES[currentType].map((c) => (
                        <MenuItem key={c} value={c}>{c}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    required
                    size="small"
                    type="number"
                    label={currentType === 'debt' ? 'Outstanding balance' : 'Amount (per period)'}
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                    inputProps={{ min: 0, step: '0.01' }}
                  />
                </Grid>

                {(currentType === 'income' || currentType === 'expense') && (
                  <>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth size="small">
                        <InputLabel>How often</InputLabel>
                        <Select
                          value={form.recurrence_frequency}
                          label="How often"
                          onChange={(e) => setForm({ ...form, recurrence_frequency: e.target.value })}
                        >
                          {RECURRENCE_OPTIONS.map((o) => (
                            <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                          ))}
                        </Select>
                        <FormHelperText>Used to normalise monthly totals</FormHelperText>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Note (optional)"
                        value={form.recurrence_note}
                        onChange={(e) => setForm({ ...form, recurrence_note: e.target.value })}
                        placeholder="e.g. Paid every second Tuesday"
                      />
                    </Grid>
                  </>
                )}

                {currentType === 'debt' && (
                  <>
                    <Grid item xs={12}>
                      <Typography variant="caption" color="text.secondary">
                        Optional: recurring payment amount (for monthly cash-flow)
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        size="small"
                        type="number"
                        label="Payment amount / period"
                        value={form.payment_amount}
                        onChange={(e) => setForm({ ...form, payment_amount: e.target.value })}
                        inputProps={{ min: 0, step: '0.01' }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Payment frequency</InputLabel>
                        <Select
                          value={form.payment_frequency}
                          label="Payment frequency"
                          onChange={(e) => setForm({ ...form, payment_frequency: e.target.value })}
                        >
                          {RECURRENCE_OPTIONS.filter((o) => o.value !== 'none').map((o) => (
                            <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </>
                )}

                <Grid item xs={12}>
                  <Button type="submit" variant="contained" disabled={submitting}>
                    {submitting ? <CircularProgress size={18} /> : 'Save'}
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </Box>

        {/* Items table */}
        {loading && !summary ? (
          <Box>
            {[1, 2, 3].map((i) => <Skeleton key={i} height={52} sx={{ mb: 0.5 }} />)}
          </Box>
        ) : visibleItems.length === 0 ? (
          <Box
            sx={{
              py: 6,
              textAlign: 'center',
              border: '1px dashed',
              borderColor: 'divider',
              borderRadius: 2,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              No {currentType} entries yet.{' '}
              <Box
                component="span"
                sx={{ color: 'primary.main', cursor: 'pointer', fontWeight: 600 }}
                onClick={openForm}
              >
                Add your first {currentType}.
              </Box>
            </Typography>
          </Box>
        ) : (
          <TableContainer>
            <Table size="small" className="responsive-table">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  {(currentType === 'income' || currentType === 'expense') && (
                    <TableCell>Recurrence</TableCell>
                  )}
                  {currentType === 'debt' && (
                    <TableCell>Payment</TableCell>
                  )}
                  <TableCell align="right" sx={{ width: 80 }} />
                </TableRow>
              </TableHead>
              <TableBody>
                {visibleItems.map((item) => {
                  const key = `${item.type}-${item.id}`;
                  const confirming = confirmDeleteId === key;
                  return (
                    <TableRow key={key} hover>
                      <TableCell sx={{ fontWeight: 500, maxWidth: 200 }}>
                        <Box>
                          {item.name}
                          {item.recurrence_note && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              {item.recurrence_note}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell sx={{ color: 'text.secondary' }}>{item.category}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                        {fmt(item.amount)}
                      </TableCell>
                      {(currentType === 'income' || currentType === 'expense') && (
                        <TableCell>
                          {item.recurrence_frequency && (
                            <Chip
                              label={RECURRENCE_LABELS[item.recurrence_frequency] ?? item.recurrence_frequency}
                              color={RECURRENCE_COLORS[item.recurrence_frequency] ?? 'default'}
                              size="small"
                              sx={{ fontSize: '11px' }}
                            />
                          )}
                        </TableCell>
                      )}
                      {currentType === 'debt' && (
                        <TableCell sx={{ fontSize: '12px', color: 'text.secondary' }}>
                          {item.payment_amount
                            ? `${fmt(item.payment_amount)} / ${item.payment_frequency ?? 'monthly'}`
                            : '—'}
                        </TableCell>
                      )}
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          color={confirming ? 'warning' : 'default'}
                          onClick={() => handleDelete(item)}
                          title={confirming ? 'Click again to confirm' : 'Delete'}
                          sx={{ color: confirming ? 'warning.main' : 'text.secondary' }}
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                        {confirming && (
                          <Typography variant="caption" color="warning.main" sx={{ display: 'block', fontSize: '10px', textAlign: 'center' }}>
                            Confirm?
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Finances;
