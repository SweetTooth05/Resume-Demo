import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Grid,
  Typography,
  Alert,
  Skeleton,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { LineChart, Line, XAxis, YAxis, Tooltip, BarChart, Bar, Cell, ResponsiveContainer } from 'recharts';
import { dashboardAPI, stockAPI, financialAPI } from '../services/api';

interface FinancialData {
  totalIncome: number;
  totalExpenses: number;
  totalAssets: number;
  totalDebts: number;
  netWorth: number;
  monthlySavings: number;
  cashOnHand: number;
  stocksValue: number;
  propertyAssets: number;
  monthlyDebtPayments: number;
}

interface AssetBreakdown {
  cash: number;
  stocks: number;
  real_estate: number;
  vehicles: number;
  investments: number;
  other: number;
}

interface ExpenseData {
  name: string;
  value: number;
}

interface NetWorthData {
  month: string;
  netWorth: number;
}

interface StockRec {
  ticker: string;
  name: string;
  prediction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  current_price?: number;
}

const fmt = (n: number) =>
  `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const ASSET_COLORS = ['#1B365D', '#A65E2E', '#2E5077', '#C17A48', '#4A6B8F', '#8B6914'];

const SIGNAL_STYLES: Record<string, { bg: string; color: string }> = {
  BUY:  { bg: 'rgba(29,107,79,0.1)',   color: '#1D6B4F' },
  SELL: { bg: 'rgba(181,71,71,0.1)',   color: '#B54747' },
  HOLD: { bg: 'rgba(107,101,96,0.1)',  color: '#6B6560' },
};

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Typography
    sx={{
      fontFamily: '"DM Sans", sans-serif',
      fontSize: '10px',
      fontWeight: 700,
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      color: 'text.secondary',
      mb: 2,
    }}
  >
    {children}
  </Typography>
);

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const [financialData, setFinancialData] = useState<FinancialData | null>(null);
  const [expenseData, setExpenseData] = useState<ExpenseData[]>([]);
  const [netWorthData, setNetWorthData] = useState<NetWorthData[]>([]);
  const [topStocks, setTopStocks] = useState<StockRec[]>([]);
  const [financialHealth, setFinancialHealth] = useState<number | null>(null);
  const [assetBreakdown, setAssetBreakdown] = useState<AssetBreakdown | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataWarning, setDataWarning] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      setDataWarning(null);

      const [dashRes, stockRes, healthRes, expRes, nwRes] = await Promise.allSettled([
        dashboardAPI.getDashboardData(),
        stockAPI.getRecommendations(),
        dashboardAPI.getFinancialHealth(),
        dashboardAPI.getExpenseBreakdown(),
        dashboardAPI.getNetWorthHistory(),
      ]);

      if (dashRes.status === 'fulfilled') {
        const d = dashRes.value;
        setFinancialData({
          totalIncome: d.totals?.income ?? 0,
          totalExpenses: d.totals?.expenses ?? 0,
          totalAssets: d.totals?.assets ?? 0,
          totalDebts: d.totals?.debts ?? 0,
          netWorth: d.totals?.netWorth ?? 0,
          monthlySavings: d.totals?.monthlySavings ?? 0,
          cashOnHand: d.totals?.cashOnHand ?? 0,
          stocksValue: d.totals?.stocksValue ?? 0,
          propertyAssets: d.totals?.propertyAssets ?? 0,
          monthlyDebtPayments: d.totals?.monthlyDebtPayments ?? 0,
        });
        if (d.asset_breakdown) setAssetBreakdown(d.asset_breakdown as AssetBreakdown);
        if (d.expense_breakdown?.length) {
          setExpenseData(
            (d.expense_breakdown as Array<Record<string, unknown>>).map((item) => ({
              name: String(item.name ?? item.category ?? 'Other'),
              value: Number(item.value ?? item.amount ?? 0),
            }))
          );
        }
      } else {
        // fallback to financial/summary
        try {
          const fallback = await financialAPI.getSummary();
          const s = fallback.summary;
          setFinancialData({
            totalIncome: s.total_income ?? 0,
            totalExpenses: s.total_expenses ?? 0,
            totalAssets: s.total_assets ?? 0,
            totalDebts: s.total_debts ?? 0,
            netWorth: s.net_worth ?? 0,
            monthlySavings: s.monthly_savings ?? 0,
            cashOnHand: s.cash_on_hand ?? 0,
            stocksValue: s.total_stocks_value ?? 0,
            propertyAssets: s.total_property_assets ?? 0,
            monthlyDebtPayments: s.monthly_debt_payments ?? 0,
          });
          if (fallback.asset_breakdown) setAssetBreakdown(fallback.asset_breakdown as AssetBreakdown);
        } catch {
          setError('Could not load financial data. Is the API running?');
        }
      }

      if (stockRes.status === 'fulfilled') {
        setTopStocks((stockRes.value.recommendations ?? []).slice(0, 8));
      } else {
        setDataWarning('Stock recommendations unavailable.');
      }

      if (healthRes.status === 'fulfilled') {
        setFinancialHealth(healthRes.value.score ?? null);
      }

      if (expRes.status === 'fulfilled' && expRes.value.breakdown?.length) {
        setExpenseData(
          (expRes.value.breakdown as Array<{ category: string; amount: number }>).map((item) => ({
            name: item.category,
            value: item.amount,
          }))
        );
      }

      if (nwRes.status === 'fulfilled' && nwRes.value.history?.length) {
        setNetWorthData(nwRes.value.history);
      }

      setLoading(false);
    };

    fetchAll();
  }, []);

  const computedHealth = useMemo(() => {
    if (financialHealth !== null) return financialHealth;
    if (!financialData || financialData.totalIncome === 0) return null;
    const savingsRate = (financialData.monthlySavings / financialData.totalIncome) * 100;
    const dtiRatio = (financialData.totalDebts / financialData.totalIncome) * 12;
    const atdRatio = financialData.totalAssets / (financialData.totalDebts || 1);
    let score = 0;
    score += savingsRate >= 20 ? 40 : savingsRate >= 15 ? 35 : savingsRate >= 10 ? 30 : savingsRate >= 5 ? 20 : 10;
    score += dtiRatio <= 0.3 ? 30 : dtiRatio <= 0.5 ? 25 : dtiRatio <= 0.7 ? 20 : dtiRatio <= 1.0 ? 15 : 10;
    score += atdRatio >= 3 ? 30 : atdRatio >= 2 ? 25 : atdRatio >= 1.5 ? 20 : atdRatio >= 1 ? 15 : 10;
    return Math.min(100, Math.max(0, score));
  }, [financialHealth, financialData]);

  const healthLabel = (s: number) => s >= 80 ? 'Excellent' : s >= 60 ? 'Good' : s >= 40 ? 'Fair' : 'Poor';
  const healthColor = (s: number) => s >= 80 ? '#1D6B4F' : s >= 60 ? '#A65E2E' : s >= 40 ? '#C17A48' : '#B54747';

  const hasData = financialData &&
    (financialData.totalIncome > 0 || financialData.totalExpenses > 0 ||
     financialData.totalAssets > 0 || financialData.cashOnHand > 0 || financialData.stocksValue > 0);

  const assetTotal = assetBreakdown
    ? Object.values(assetBreakdown).reduce((a, b) => a + b, 0)
    : 0;

  const assetSegments = assetBreakdown && assetTotal > 0
    ? [
        { label: 'Cash', value: assetBreakdown.cash, color: ASSET_COLORS[0] },
        { label: 'Stocks', value: assetBreakdown.stocks, color: ASSET_COLORS[1] },
        { label: 'Real estate', value: assetBreakdown.real_estate, color: ASSET_COLORS[2] },
        { label: 'Vehicles', value: assetBreakdown.vehicles, color: ASSET_COLORS[3] },
        { label: 'Investments', value: assetBreakdown.investments, color: ASSET_COLORS[4] },
        { label: 'Other', value: assetBreakdown.other, color: ASSET_COLORS[5] },
      ].filter((s) => s.value > 0)
    : [];

  const tooltipStyle = {
    backgroundColor: theme.palette.background.paper,
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: 10,
    color: theme.palette.text.primary,
    fontSize: 12,
    boxShadow: '0 4px 16px rgba(27,54,93,0.1)',
  };

  if (loading) {
    return (
      <Box sx={{ p: { xs: 2, sm: 3, md: 4 }, maxWidth: 1200, mx: 'auto', width: '100%' }}>
        <Skeleton variant="text" width={200} height={48} sx={{ mb: 1 }} />
        <Skeleton variant="rectangular" height={96} sx={{ borderRadius: 3, mb: 4 }} />
        <Skeleton variant="rectangular" height={120} sx={{ borderRadius: 2, mb: 4 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}><Skeleton variant="rectangular" height={260} sx={{ borderRadius: 2 }} /></Grid>
          <Grid item xs={12} md={6}><Skeleton variant="rectangular" height={260} sx={{ borderRadius: 2 }} /></Grid>
        </Grid>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        flexGrow: 1,
        p: { xs: 2, sm: 3, md: 4 },
        maxWidth: 1280,
        mx: 'auto',
        width: '100%',
        overflow: 'auto',
      }}
    >
      {/* Page heading */}
      <Box sx={{ mb: 4, animation: 'fadeUp 0.4s cubic-bezier(0.16,1,0.3,1) both' }}>
        <Typography
          variant="h4"
          sx={{
            fontFamily: '"Fraunces", Georgia, serif',
            fontSize: 'clamp(1.6rem, 3vw, 2.25rem)',
            fontWeight: 600,
            letterSpacing: '-0.03em',
            color: 'primary.dark',
            mb: 0.5,
          }}
        >
          Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Your financial position at a glance.
        </Typography>
      </Box>

      {dataWarning && (
        <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setDataWarning(null)}>
          {dataWarning}
        </Alert>
      )}

      {/* Stat strip */}
      <Box
        className="stat-strip animate-fade-up animate-fade-up-1"
        sx={{ mb: 4 }}
      >
        {[
          { label: 'Monthly income', value: hasData ? fmt(financialData!.totalIncome) : '—', color: '#1D6B4F' },
          { label: 'Monthly expenses', value: hasData ? fmt(financialData!.totalExpenses) : '—', color: '#B54747' },
          { label: 'Net worth', value: hasData ? fmt(financialData!.netWorth) : '—', color: 'var(--color-navy-900)' },
          { label: 'Monthly savings', value: hasData ? fmt(financialData!.monthlySavings) : '—', color: financialData && financialData.monthlySavings >= 0 ? '#1D6B4F' : '#B54747' },
        ].map((stat) => (
          <Box key={stat.label} className="stat-item">
            <span className="stat-label">{stat.label}</span>
            <span className="stat-value" style={{ color: stat.color }}>{stat.value}</span>
          </Box>
        ))}
      </Box>

      {/* Financial health */}
      {computedHealth !== null && (
        <Box
          sx={{
            mb: 4,
            pb: 4,
            borderBottom: '1px solid',
            borderColor: 'divider',
            animation: 'fadeUp 0.4s 0.06s cubic-bezier(0.16,1,0.3,1) both',
          }}
        >
          <SectionLabel>Financial Health</SectionLabel>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2, mb: 1 }}>
            <Typography
              sx={{
                fontFamily: '"Fraunces", serif',
                fontSize: 'clamp(3rem, 6vw, 4.5rem)',
                fontWeight: 600,
                lineHeight: 1,
                color: healthColor(computedHealth),
              }}
            >
              {computedHealth}
            </Typography>
            <Typography
              sx={{
                fontFamily: '"Fraunces", serif',
                fontSize: 'clamp(1.2rem, 2vw, 1.5rem)',
                fontWeight: 500,
                color: healthColor(computedHealth),
              }}
            >
              {healthLabel(computedHealth)}
            </Typography>
          </Box>
          <Box
            sx={{
              height: '4px',
              borderRadius: '2px',
              backgroundColor: 'divider',
              maxWidth: 480,
              overflow: 'hidden',
              mb: 1.5,
            }}
          >
            <Box
              sx={{
                height: '100%',
                width: `${computedHealth}%`,
                backgroundColor: healthColor(computedHealth),
                borderRadius: '2px',
                transition: 'width 0.8s cubic-bezier(0.16,1,0.3,1)',
              }}
            />
          </Box>
          <Typography variant="caption" color="text.secondary">
            Based on savings rate, debt-to-income ratio, and asset coverage.
          </Typography>
        </Box>
      )}

      {/* Asset breakdown */}
      {assetSegments.length > 0 && (
        <Box
          sx={{
            mb: 4,
            pb: 4,
            borderBottom: '1px solid',
            borderColor: 'divider',
            animation: 'fadeUp 0.4s 0.12s cubic-bezier(0.16,1,0.3,1) both',
          }}
        >
          <SectionLabel>Asset Breakdown</SectionLabel>
          <Box className="asset-bar" sx={{ mb: 2 }}>
            {assetSegments.map((seg) => (
              <Box
                key={seg.label}
                className="asset-bar-segment"
                title={`${seg.label}: ${fmt(seg.value)}`}
                sx={{
                  flex: seg.value / assetTotal,
                  backgroundColor: seg.color,
                  minWidth: '4px',
                }}
              />
            ))}
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '12px 24px' }}>
            {assetSegments.map((seg) => (
              <Box key={seg.label} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: seg.color, flexShrink: 0 }} />
                <Typography variant="caption" color="text.secondary">{seg.label}</Typography>
                <Typography variant="caption" fontWeight={600}>{fmt(seg.value)}</Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Charts */}
      {hasData && (expenseData.length > 0 || netWorthData.length > 0) && (
        <Grid
          container
          spacing={4}
          sx={{
            mb: 4,
            animation: 'fadeUp 0.4s 0.18s cubic-bezier(0.16,1,0.3,1) both',
          }}
        >
          {expenseData.length > 0 && (
            <Grid item xs={12} lg={6}>
              <SectionLabel>Expense Breakdown</SectionLabel>
              <Box sx={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={expenseData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <XAxis
                      dataKey="name"
                      tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Amount']}
                      contentStyle={tooltipStyle}
                      cursor={{ fill: 'rgba(27,54,93,0.04)' }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {expenseData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={ASSET_COLORS[index % ASSET_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Grid>
          )}

          {netWorthData.length > 0 && (
            <Grid item xs={12} lg={expenseData.length > 0 ? 6 : 12}>
              <SectionLabel>Net Worth History</SectionLabel>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                Book assets & debts by when added; portfolio uses today's prices.
              </Typography>
              <Box sx={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={netWorthData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <XAxis
                      dataKey="month"
                      tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Net worth']}
                      contentStyle={tooltipStyle}
                    />
                    <Line
                      type="monotone"
                      dataKey="netWorth"
                      stroke={theme.palette.secondary.main}
                      strokeWidth={2.5}
                      dot={{ fill: theme.palette.primary.main, r: 3, strokeWidth: 0 }}
                      activeDot={{ r: 5, fill: theme.palette.secondary.main }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </Grid>
          )}
        </Grid>
      )}

      {/* Market signals */}
      <Box sx={{ animation: 'fadeUp 0.4s 0.24s cubic-bezier(0.16,1,0.3,1) both' }}>
        <SectionLabel>Market Signals</SectionLabel>
        {topStocks.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No recommendations available. The stock model may be loading.
          </Typography>
        ) : (
          <Box sx={{ overflowX: 'auto' }}>
            <Box
              component="table"
              sx={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '13px',
                fontFamily: '"DM Sans", sans-serif',
              }}
            >
              <Box component="thead">
                <Box component="tr">
                  {['Ticker', 'Name', 'Price', 'Signal', 'Confidence'].map((h) => (
                    <Box
                      key={h}
                      component="th"
                      sx={{
                        textAlign: 'left',
                        padding: '8px 12px 8px 0',
                        fontSize: '10px',
                        fontWeight: 700,
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        color: 'text.secondary',
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {h}
                    </Box>
                  ))}
                </Box>
              </Box>
              <Box component="tbody">
                {topStocks.map((stock) => {
                  const sig = SIGNAL_STYLES[stock.prediction] ?? SIGNAL_STYLES.HOLD;
                  return (
                    <Box
                      key={stock.ticker}
                      component="tr"
                      sx={{
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                        '&:last-child': { borderBottom: 'none' },
                        '&:hover td, &:hover th': { backgroundColor: 'rgba(27,54,93,0.025)' },
                      }}
                    >
                      <Box component="td" sx={{ py: 1.5, pr: 3, fontWeight: 700, color: 'primary.dark', whiteSpace: 'nowrap' }}>
                        {stock.ticker}
                      </Box>
                      <Box component="td" sx={{ py: 1.5, pr: 3, color: 'text.secondary', minWidth: 140 }}>
                        {stock.name}
                      </Box>
                      <Box component="td" sx={{ py: 1.5, pr: 3, fontWeight: 600, whiteSpace: 'nowrap' }}>
                        {typeof stock.current_price === 'number' ? `$${stock.current_price.toFixed(2)}` : '—'}
                      </Box>
                      <Box component="td" sx={{ py: 1.5, pr: 3 }}>
                        <Box
                          sx={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            px: 1.25,
                            py: 0.25,
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 700,
                            letterSpacing: '0.06em',
                            textTransform: 'uppercase',
                            backgroundColor: sig.bg,
                            color: sig.color,
                          }}
                        >
                          {stock.prediction}
                        </Box>
                      </Box>
                      <Box component="td" sx={{ py: 1.5, pr: 0, color: 'text.secondary' }}>
                        {(stock.confidence * 100).toFixed(0)}%
                      </Box>
                    </Box>
                  );
                })}
              </Box>
            </Box>
          </Box>
        )}
      </Box>

      {/* Getting started */}
      {!hasData && (
        <Box
          sx={{
            mt: 4,
            p: 4,
            border: '1px dashed',
            borderColor: 'divider',
            borderRadius: 3,
            textAlign: 'center',
          }}
        >
          <Typography variant="h6" sx={{ mb: 1, fontFamily: '"Fraunces", serif', color: 'primary.dark' }}>
            Ready to get started?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Add income, expenses, assets, and debts in the <strong>Finances</strong> tab to see your full dashboard.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;
