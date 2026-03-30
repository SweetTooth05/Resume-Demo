import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  CircularProgress,
  InputAdornment,
  Skeleton,
} from '@mui/material';
import {
  Delete,
  TrendingUp,
  TrendingDown,
  Search,
  Add,
  Refresh,
} from '@mui/icons-material';
import { stockAPI, portfolioAPI } from '../services/api';

interface StockHolding {
  id: string;
  ticker: string;
  name: string;
  shares: number;
  avgPrice: number;
  currentPrice: number;
  prediction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  change: number;
  changePercent: number;
}

interface StockRecommendation {
  ticker: string;
  name: string;
  currentPrice: number;
  prediction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  change: number;
  changePercent: number;
}

type PredictionFilter = 'ALL' | 'BUY' | 'SELL' | 'HOLD';

const fmt = (n: number) =>
  n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const Stocks: React.FC = () => {
  const [holdings, setHoldings] = useState<StockHolding[]>([]);
  const [allRecommendations, setAllRecommendations] = useState<StockRecommendation[]>([]);
  const [filteredRecommendations, setFilteredRecommendations] = useState<StockRecommendation[]>([]);

  const [formOpen, setFormOpen] = useState(false);
  const [newHolding, setNewHolding] = useState({ ticker: '', shares: '', avgPrice: '' });
  const formRef = useRef<HTMLDivElement>(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [predictionFilter, setPredictionFilter] = useState<PredictionFilter>('ALL');
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await stockAPI.getRecommendations();
      if (response?.recommendations) {
        const mapped: StockRecommendation[] = response.recommendations
          .map((rec: any) => ({
            ticker: rec.ticker,
            name: rec.name || rec.ticker,
            currentPrice: rec.current_price || 0,
            prediction: rec.prediction,
            confidence: rec.confidence || 0,
            change: rec.change || 0,
            changePercent: rec.change_percent || 0,
          }))
          .sort((a: StockRecommendation, b: StockRecommendation) => b.confidence - a.confidence)
          .slice(0, 20);
        setAllRecommendations(mapped);
        setFilteredRecommendations(mapped);
      } else {
        setAllRecommendations([]);
        setFilteredRecommendations([]);
      }
    } catch {
      setError('Failed to load stock recommendations.');
      setAllRecommendations([]);
      setFilteredRecommendations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPortfolio = useCallback(async () => {
    setPortfolioLoading(true);
    try {
      const response = await portfolioAPI.getPortfolio();
      const mapped: StockHolding[] = (response?.holdings ?? []).map((h) => ({
        id: h.id,
        ticker: h.ticker,
        name: h.name,
        shares: h.shares,
        avgPrice: h.avg_price,
        currentPrice: h.current_price,
        prediction: h.prediction,
        confidence: h.confidence,
        change: h.change,
        changePercent: h.change_percent,
      }));
      setHoldings(mapped);
    } catch {
      setHoldings([]);
    } finally {
      setPortfolioLoading(false);
    }
  }, []);

  const searchStocks = useCallback(
    async (query: string) => {
      if (!query.trim()) {
        const base =
          predictionFilter === 'ALL'
            ? allRecommendations
            : allRecommendations.filter((r) => r.prediction === predictionFilter);
        setFilteredRecommendations(base);
        return;
      }
      setSearchLoading(true);
      try {
        const response = await stockAPI.searchStocks(query);
        if (response?.predictions) {
          const results: StockRecommendation[] = response.predictions.map((p: any) => ({
            ticker: p.ticker,
            name: p.name || p.ticker,
            currentPrice: p.current_price || 0,
            prediction: p.prediction,
            confidence: p.confidence || 0,
            change: p.change || 0,
            changePercent: p.change_percent || 0,
          }));
          setFilteredRecommendations(results);
        } else {
          setFilteredRecommendations([]);
        }
      } catch {
        setFilteredRecommendations([]);
      } finally {
        setSearchLoading(false);
      }
    },
    [allRecommendations, predictionFilter],
  );

  useEffect(() => {
    fetchRecommendations();
    fetchPortfolio();
  }, [fetchRecommendations, fetchPortfolio]);

  useEffect(() => {
    if (!searchTerm) {
      const base =
        predictionFilter === 'ALL'
          ? allRecommendations
          : allRecommendations.filter((r) => r.prediction === predictionFilter);
      setFilteredRecommendations(base);
    } else {
      void searchStocks(searchTerm);
    }
  }, [searchTerm, predictionFilter, allRecommendations, searchStocks]);

  const openForm = () => {
    setFormOpen(true);
    setTimeout(() => formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60);
  };

  const closeForm = () => {
    setFormOpen(false);
    setNewHolding({ ticker: '', shares: '', avgPrice: '' });
  };

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHolding.ticker || !newHolding.shares || !newHolding.avgPrice) return;
    setAddLoading(true);
    try {
      await portfolioAPI.addStock({
        ticker: newHolding.ticker.toUpperCase(),
        shares: parseInt(newHolding.shares),
        avgPrice: parseFloat(newHolding.avgPrice),
      });
      await fetchPortfolio();
      closeForm();
    } catch {
      setError('Failed to add holding. Please try again.');
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteHolding = async (id: string) => {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id);
      setTimeout(() => setConfirmDeleteId((prev) => (prev === id ? null : prev)), 3000);
      return;
    }
    setConfirmDeleteId(null);
    try {
      await portfolioAPI.removeStock(id);
      await fetchPortfolio();
    } catch {
      setError('Failed to remove holding.');
    }
  };

  // Portfolio metrics
  const portfolioValue = holdings.reduce((s, h) => s + h.shares * h.currentPrice, 0);
  const portfolioCost = holdings.reduce((s, h) => s + h.shares * h.avgPrice, 0);
  const totalPL = portfolioValue - portfolioCost;
  const totalPLPct = portfolioCost > 0 ? (totalPL / portfolioCost) * 100 : 0;
  const buyCount = allRecommendations.filter((r) => r.prediction === 'BUY').length;

  const PILLS: { label: string; value: PredictionFilter }[] = [
    { label: 'All', value: 'ALL' },
    { label: 'Buy', value: 'BUY' },
    { label: 'Sell', value: 'SELL' },
    { label: 'Hold', value: 'HOLD' },
  ];

  const inputSx = {
    '& .MuiOutlinedInput-root': { backgroundColor: 'background.paper', borderRadius: '8px' },
    '& .MuiInputLabel-root': { fontSize: '13px' },
  };

  return (
    <Box
      sx={{
        flexGrow: 1,
        px: { xs: 2, sm: 3, md: 5 },
        py: { xs: 3, sm: 4 },
        maxWidth: 1200,
        mx: 'auto',
        width: '100%',
        height: '100%',
        overflow: 'auto',
      }}
    >
      {/* Page header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          mb: 4,
          animation: 'fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) both',
        }}
      >
        <Box>
          <Typography
            sx={{
              fontFamily: '"Fraunces", Georgia, serif',
              fontSize: 'clamp(1.75rem, 4vw, 2.25rem)',
              fontWeight: 600,
              color: 'primary.dark',
              letterSpacing: '-0.025em',
              lineHeight: 1,
              mb: 0.5,
            }}
          >
            Stocks
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '13px' }}>
            Portfolio tracking &amp; AI-powered recommendations
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={<Add />}
          onClick={openForm}
          sx={{ fontSize: '13px', py: 1, px: 2.5, display: { xs: 'none', sm: 'flex' } }}
        >
          Add holding
        </Button>
      </Box>

      {error && (
        <Alert
          severity="warning"
          sx={{ mb: 3, animation: 'fadeUp 0.3s ease both' }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Stat strip */}
      <Box
        className="stat-strip"
        sx={{ mb: 4, animation: 'fadeUp 0.5s 0.05s cubic-bezier(0.16,1,0.3,1) both' }}
      >
        <Box className="stat-item">
          <span className="stat-label">Portfolio value</span>
          <span className="stat-value">
            {portfolioLoading ? <Skeleton width={80} /> : holdings.length > 0 ? `$${fmt(portfolioValue)}` : '—'}
          </span>
        </Box>
        <Box className="stat-item">
          <span className="stat-label">Total P&amp;L</span>
          <span
            className="stat-value"
            style={{
              color: totalPL >= 0 ? 'var(--color-success)' : 'var(--color-error)',
            }}
          >
            {portfolioLoading ? (
              <Skeleton width={80} />
            ) : holdings.length > 0 ? (
              `${totalPL >= 0 ? '+' : ''}$${fmt(Math.abs(totalPL))} (${totalPLPct >= 0 ? '+' : ''}${totalPLPct.toFixed(1)}%)`
            ) : (
              '—'
            )}
          </span>
        </Box>
        <Box className="stat-item">
          <span className="stat-label">Holdings</span>
          <span className="stat-value">
            {portfolioLoading ? <Skeleton width={32} /> : holdings.length}
          </span>
        </Box>
        <Box className="stat-item">
          <span className="stat-label">Buy signals</span>
          <span className="stat-value" style={{ color: 'var(--color-success)' }}>
            {loading ? <Skeleton width={24} /> : buyCount}
          </span>
        </Box>
      </Box>

      {/* Holdings section */}
      <Box sx={{ mb: 5, animation: 'fadeUp 0.5s 0.1s cubic-bezier(0.16,1,0.3,1) both' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography
            sx={{
              fontFamily: '"Fraunces", Georgia, serif',
              fontSize: '1.125rem',
              fontWeight: 600,
              color: 'primary.dark',
            }}
          >
            Your holdings
          </Typography>
          <Button
            size="small"
            startIcon={<Add />}
            onClick={openForm}
            sx={{ fontSize: '12px', display: { xs: 'flex', sm: 'none' } }}
          >
            Add
          </Button>
        </Box>

        {/* Inline add form */}
        <Box
          ref={formRef}
          sx={{
            display: 'grid',
            gridTemplateRows: formOpen ? '1fr' : '0fr',
            transition: 'grid-template-rows 0.3s cubic-bezier(0.16,1,0.3,1)',
          }}
        >
          <Box sx={{ overflow: 'hidden' }}>
            <Box
              component="form"
              onSubmit={handleAddHolding}
              sx={{
                mb: 2,
                p: { xs: 2, sm: 3 },
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 2,
                backgroundColor: 'background.paper',
              }}
            >
              <Typography
                sx={{
                  fontFamily: '"Fraunces", Georgia, serif',
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: 'primary.dark',
                  mb: 2,
                }}
              >
                Add holding
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr 1fr' },
                  gap: 2,
                  mb: 2,
                }}
              >
                <TextField
                  required
                  label="Ticker"
                  placeholder="AAPL"
                  value={newHolding.ticker}
                  onChange={(e) => setNewHolding({ ...newHolding, ticker: e.target.value })}
                  size="small"
                  sx={inputSx}
                  inputProps={{ style: { textTransform: 'uppercase' } }}
                />
                <TextField
                  required
                  label="Shares"
                  type="number"
                  placeholder="10"
                  value={newHolding.shares}
                  onChange={(e) => setNewHolding({ ...newHolding, shares: e.target.value })}
                  size="small"
                  sx={inputSx}
                  inputProps={{ min: 0.001, step: 0.001 }}
                />
                <TextField
                  required
                  label="Avg cost / share"
                  type="number"
                  placeholder="150.00"
                  value={newHolding.avgPrice}
                  onChange={(e) => setNewHolding({ ...newHolding, avgPrice: e.target.value })}
                  size="small"
                  sx={inputSx}
                  InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
                  inputProps={{ min: 0.01, step: 0.01 }}
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 1.5 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={addLoading}
                  sx={{ fontSize: '13px', py: 0.75 }}
                >
                  {addLoading ? 'Adding…' : 'Add holding'}
                </Button>
                <Button
                  type="button"
                  variant="text"
                  onClick={closeForm}
                  sx={{ fontSize: '13px', color: 'text.secondary' }}
                >
                  Cancel
                </Button>
              </Box>
            </Box>
          </Box>
        </Box>

        {portfolioLoading ? (
          <Box>
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} height={48} sx={{ mb: 0.5, borderRadius: 1 }} />
            ))}
          </Box>
        ) : holdings.length === 0 ? (
          <Box
            sx={{
              py: 5,
              textAlign: 'center',
              border: '1.5px dashed',
              borderColor: 'divider',
              borderRadius: 2,
              color: 'text.secondary',
            }}
          >
            <Typography sx={{ fontSize: '14px', mb: 1 }}>No holdings yet</Typography>
            <Typography sx={{ fontSize: '12px', color: 'text.secondary' }}>
              Add your first position to track performance
            </Typography>
          </Box>
        ) : (
          <TableContainer sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Stock</TableCell>
                  <TableCell align="right">Shares</TableCell>
                  <TableCell align="right" sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                    Avg cost
                  </TableCell>
                  <TableCell align="right">Current</TableCell>
                  <TableCell align="right">P&amp;L</TableCell>
                  <TableCell align="center">Signal</TableCell>
                  <TableCell align="right" sx={{ width: 48 }} />
                </TableRow>
              </TableHead>
              <TableBody>
                {holdings.map((h) => {
                  const pl = (h.currentPrice - h.avgPrice) * h.shares;
                  const plPct =
                    h.avgPrice > 0 ? ((h.currentPrice - h.avgPrice) / h.avgPrice) * 100 : 0;
                  const isConfirming = confirmDeleteId === h.id;
                  return (
                    <TableRow
                      key={h.id}
                      sx={{
                        '&:hover': { backgroundColor: 'rgba(27,54,93,0.03)' },
                        transition: 'background-color 0.15s',
                      }}
                    >
                      <TableCell>
                        <Typography sx={{ fontSize: '13px', fontWeight: 600, color: 'primary.dark' }}>
                          {h.ticker}
                        </Typography>
                        <Typography sx={{ fontSize: '11px', color: 'text.secondary' }}>
                          {h.name}
                        </Typography>
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '13px' }}>
                        {h.shares}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ fontSize: '13px', display: { xs: 'none', sm: 'table-cell' } }}
                      >
                        ${fmt(h.avgPrice)}
                      </TableCell>
                      <TableCell align="right">
                        <Typography sx={{ fontSize: '13px' }}>${fmt(h.currentPrice)}</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.25 }}>
                          {h.change >= 0 ? (
                            <TrendingUp sx={{ fontSize: 11, color: 'success.main' }} />
                          ) : (
                            <TrendingDown sx={{ fontSize: 11, color: 'error.main' }} />
                          )}
                          <Typography
                            sx={{
                              fontSize: '11px',
                              color: h.change >= 0 ? 'success.main' : 'error.main',
                            }}
                          >
                            {h.changePercent >= 0 ? '+' : ''}{h.changePercent.toFixed(1)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          sx={{
                            fontSize: '13px',
                            fontWeight: 600,
                            color: pl >= 0 ? 'success.main' : 'error.main',
                          }}
                        >
                          {pl >= 0 ? '+' : ''}${fmt(Math.abs(pl))}
                        </Typography>
                        <Typography
                          sx={{
                            fontSize: '11px',
                            color: pl >= 0 ? 'success.main' : 'error.main',
                          }}
                        >
                          {plPct >= 0 ? '+' : ''}{plPct.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <span className={`signal-badge--${h.prediction.toLowerCase()}`}>
                          {h.prediction}
                        </span>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteHolding(h.id)}
                            sx={{
                              color: isConfirming ? 'error.main' : 'text.secondary',
                              transition: 'color 0.15s',
                            }}
                          >
                            <Delete sx={{ fontSize: 16 }} />
                          </IconButton>
                          {isConfirming && (
                            <Typography sx={{ fontSize: '10px', color: 'error.main', mt: -0.5 }}>
                              Confirm?
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      {/* Recommendations section */}
      <Box sx={{ animation: 'fadeUp 0.5s 0.15s cubic-bezier(0.16,1,0.3,1) both' }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: { sm: 'center' },
            gap: 2,
            mb: 2,
          }}
        >
          <Typography
            sx={{
              fontFamily: '"Fraunces", Georgia, serif',
              fontSize: '1.125rem',
              fontWeight: 600,
              color: 'primary.dark',
              mr: 'auto',
            }}
          >
            Recommendations
            {loading && <CircularProgress size={14} sx={{ ml: 1.5, verticalAlign: 'middle' }} />}
          </Typography>

          {/* Search */}
          <TextField
            placeholder="Search ticker or name…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            sx={{ ...inputSx, width: { xs: '100%', sm: 220 } }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  {searchLoading ? (
                    <CircularProgress size={16} />
                  ) : (
                    <Search sx={{ fontSize: 18, color: 'text.secondary' }} />
                  )}
                </InputAdornment>
              ),
            }}
          />

          {/* Refresh */}
          <IconButton
            size="small"
            onClick={fetchRecommendations}
            disabled={loading}
            title="Refresh recommendations"
            sx={{ color: 'text.secondary', border: '1px solid', borderColor: 'divider', borderRadius: 1.5 }}
          >
            <Refresh sx={{ fontSize: 18 }} />
          </IconButton>
        </Box>

        {/* Filter pills */}
        <Box className="filter-pills" sx={{ mb: 2 }}>
          {PILLS.map((p) => (
            <button
              key={p.value}
              className={`filter-pill${predictionFilter === p.value ? ' filter-pill--active' : ''}`}
              onClick={() => setPredictionFilter(p.value)}
              type="button"
            >
              {p.label}
              {p.value !== 'ALL' && (
                <span style={{ marginLeft: 4, opacity: 0.65 }}>
                  {allRecommendations.filter((r) => r.prediction === p.value).length}
                </span>
              )}
            </button>
          ))}
        </Box>

        {loading && filteredRecommendations.length === 0 ? (
          <Box>
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} height={44} sx={{ mb: 0.5, borderRadius: 1 }} />
            ))}
          </Box>
        ) : filteredRecommendations.length === 0 ? (
          <Box
            sx={{
              py: 5,
              textAlign: 'center',
              border: '1.5px dashed',
              borderColor: 'divider',
              borderRadius: 2,
              color: 'text.secondary',
            }}
          >
            <Typography sx={{ fontSize: '14px' }}>
              {searchTerm ? `No results for "${searchTerm}"` : 'No recommendations available'}
            </Typography>
          </Box>
        ) : (
          <TableContainer sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Stock</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right" sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                    Day change
                  </TableCell>
                  <TableCell align="center">Signal</TableCell>
                  <TableCell align="right">Confidence</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredRecommendations.map((rec) => (
                  <TableRow
                    key={rec.ticker}
                    sx={{
                      '&:hover': { backgroundColor: 'rgba(27,54,93,0.03)' },
                      transition: 'background-color 0.15s',
                    }}
                  >
                    <TableCell>
                      <Typography sx={{ fontSize: '13px', fontWeight: 600, color: 'primary.dark' }}>
                        {rec.ticker}
                      </Typography>
                      <Typography sx={{ fontSize: '11px', color: 'text.secondary' }}>
                        {rec.name}
                      </Typography>
                    </TableCell>
                    <TableCell align="right" sx={{ fontSize: '13px' }}>
                      ${fmt(rec.currentPrice)}
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{ display: { xs: 'none', md: 'table-cell' } }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                        {rec.change >= 0 ? (
                          <TrendingUp sx={{ fontSize: 13, color: 'success.main' }} />
                        ) : (
                          <TrendingDown sx={{ fontSize: 13, color: 'error.main' }} />
                        )}
                        <Typography
                          sx={{
                            fontSize: '12px',
                            color: rec.change >= 0 ? 'success.main' : 'error.main',
                          }}
                        >
                          {rec.changePercent >= 0 ? '+' : ''}{rec.changePercent.toFixed(2)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <span className={`signal-badge--${rec.prediction.toLowerCase()}`}>
                        {rec.prediction}
                      </span>
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                        <Box
                          sx={{
                            width: 48,
                            height: 4,
                            borderRadius: 2,
                            backgroundColor: 'rgba(27,54,93,0.1)',
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              height: '100%',
                              width: `${(rec.confidence * 100).toFixed(0)}%`,
                              backgroundColor:
                                rec.prediction === 'BUY'
                                  ? 'success.main'
                                  : rec.prediction === 'SELL'
                                  ? 'error.main'
                                  : 'warning.main',
                              borderRadius: 2,
                            }}
                          />
                        </Box>
                        <Typography sx={{ fontSize: '12px', color: 'text.secondary', minWidth: 32 }}>
                          {(rec.confidence * 100).toFixed(0)}%
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </Box>
  );
};

export default Stocks;
