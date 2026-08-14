'use client';

import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Plus, X, CheckCircle, Package, FilePlus } from 'lucide-react';
import Layout from '@/components/Layout';
import { tradingApi, TradeRecordRequest, Transaction, Portfolio, PositionAggregate } from '@/lib/api';
import { formatCurrency, Currency } from '@/lib/currency';

function TradeForm() {
  const [formData, setFormData] = useState<TradeRecordRequest>({
    portfolio_id: 1,
    market: 'crypto',
    symbol: '',
    side: 'buy',
    type: 'open',
    quantity: 0,
    price: 0,
    fee: 0,
  });

  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [positions, setPositions] = useState<PositionAggregate[]>([]);
  const [selectedPosition, setSelectedPosition] = useState<PositionAggregate | null>(null);
  const [tradeMode, setTradeMode] = useState<'new' | 'existing'>('new');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchPortfolios() {
      try {
        const res = await tradingApi.portfolios.list();
        setPortfolios(res.data);
      } catch (error) {
        console.error('Failed to fetch portfolios:', error);
      }
    }
    fetchPortfolios();
  }, []);

  useEffect(() => {
    async function fetchPositions() {
      if (formData.portfolio_id) {
        try {
          const res = await tradingApi.portfolios.summary(formData.portfolio_id);
          const openPositions = res.data.positions.filter((p: PositionAggregate) => p.status === 'open');
          setPositions(openPositions);
        } catch (error) {
          console.error('Failed to fetch positions:', error);
        }
      }
    }
    fetchPositions();
  }, [formData.portfolio_id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const submitData = { ...formData };
      if (selectedPosition) {
        submitData.symbol = selectedPosition.symbol;
        submitData.market = selectedPosition.market;
        submitData.side = selectedPosition.side;
      }
      await tradingApi.transactions.record(submitData);
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setFormData({
          portfolio_id: 1,
          market: 'crypto',
          symbol: '',
          side: 'buy',
          type: 'open',
          quantity: 0,
          price: 0,
          fee: 0,
        });
        setSelectedPosition(null);
        setTradeMode('new');
      }, 2000);
    } catch (error) {
      console.error('Failed to record trade:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalAmount = formData.quantity * formData.price;

  const currentPortfolio = portfolios.find(p => p.id === formData.portfolio_id);
  const currency = (currentPortfolio?.currency || 'USD') as Currency;

  return (
    <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Record Trade</h2>
        {submitted && (
          <div className="flex items-center gap-2 text-green-500">
            <CheckCircle className="w-5 h-5" />
            <span className="text-sm font-medium">Trade recorded successfully</span>
          </div>
        )}
      </div>

      <div className="flex gap-2 mb-6">
        <button
          type="button"
          onClick={() => { setTradeMode('new'); setSelectedPosition(null); }}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg font-medium transition-colors ${
            tradeMode === 'new'
              ? 'bg-primary-500 text-white'
              : 'bg-dark-700 text-dark-600 hover:bg-dark-600'
          }`}
        >
          <FilePlus className="w-4 h-4" />
          New Position
        </button>
        <button
          type="button"
          onClick={() => setTradeMode('existing')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg font-medium transition-colors ${
            tradeMode === 'existing'
              ? 'bg-primary-500 text-white'
              : 'bg-dark-700 text-dark-600 hover:bg-dark-600'
          }`}
        >
          <Package className="w-4 h-4" />
          Existing Position
        </button>
      </div>

      {tradeMode === 'existing' && (
        <div className="mb-6">
          <label className="block text-sm text-dark-600 mb-2">Select Position</label>
          <select
            value={selectedPosition?.position_id || ''}
            onChange={(e) => {
              const pos = positions.find(p => p.position_id === parseInt(e.target.value));
              setSelectedPosition(pos || null);
              if (pos) {
                setFormData({ ...formData, type: 'add' });
              }
            }}
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
          >
            <option value="">Choose a position...</option>
            {positions.map((pos) => (
              <option key={pos.position_id} value={pos.position_id}>
                {pos.symbol} ({pos.side}) - {formatCurrency(pos.total_amount, currency)}
              </option>
            ))}
          </select>

          {selectedPosition && (
            <div className="mt-4 p-4 bg-dark-700 rounded-lg">
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-dark-600">Symbol</p>
                  <p className="text-white font-medium">{selectedPosition.symbol}</p>
                </div>
                <div>
                  <p className="text-dark-600">Side</p>
                  <p className={`font-medium ${selectedPosition.side === 'buy' ? 'text-green-500' : 'text-red-500'}`}>
                    {selectedPosition.side.toUpperCase()}
                  </p>
                </div>
                <div>
                  <p className="text-dark-600">Quantity</p>
                  <p className="text-white font-medium">{selectedPosition.total_quantity}</p>
                </div>
                <div>
                  <p className="text-dark-600">Avg Price</p>
                  <p className="text-white font-medium">{formatCurrency(selectedPosition.avg_price, currency)}</p>
                </div>
                <div>
                  <p className="text-dark-600">Total Value</p>
                  <p className="text-white font-medium">{formatCurrency(selectedPosition.total_amount, currency)}</p>
                </div>
                <div>
                  <p className="text-dark-600">Status</p>
                  <p className="text-blue-500 font-medium">{selectedPosition.status.toUpperCase()}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-dark-600 mb-2">Portfolio</label>
            <select
              value={formData.portfolio_id}
              onChange={(e) => {
                setFormData({ ...formData, portfolio_id: parseInt(e.target.value) });
                setSelectedPosition(null);
              }}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
            >
              {portfolios.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.currency})
                </option>
              ))}
            </select>
          </div>
          {tradeMode === 'new' && (
            <>
              <div>
                <label className="block text-sm text-dark-600 mb-2">Market</label>
                <select
                  value={formData.market}
                  onChange={(e) => setFormData({ ...formData, market: e.target.value })}
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                >
                  <option value="crypto">Crypto</option>
                  <option value="stock">Stock</option>
                  <option value="futures">Futures</option>
                  <option value="etf">ETF</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-dark-600 mb-2">Symbol</label>
                <input
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                  placeholder="BTCUSDT"
                  className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </>
          )}
          {tradeMode === 'existing' && (
            <div className="col-span-2">
              <label className="block text-sm text-dark-600 mb-2">Trade Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as TradeRecordRequest['type'] })}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
              >
                <option value="add">Add to Position</option>
                <option value="reduce">Reduce Position</option>
                <option value="close">Close Position</option>
              </select>
            </div>
          )}
          {tradeMode === 'new' && (
            <div>
              <label className="block text-sm text-dark-600 mb-2">Trade Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as TradeRecordRequest['type'] })}
                className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
              >
                <option value="open">Open Position</option>
              </select>
            </div>
          )}
        </div>

        {tradeMode === 'new' && (
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setFormData({ ...formData, side: 'buy' })}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors ${
                formData.side === 'buy'
                  ? 'bg-green-500/20 text-green-500 border border-green-500'
                  : 'bg-dark-700 text-dark-600 border border-dark-600 hover:border-dark-500'
              }`}
            >
              <ArrowUpRight className="w-5 h-5" />
              Buy
            </button>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, side: 'sell' })}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors ${
                formData.side === 'sell'
                  ? 'bg-red-500/20 text-red-500 border border-red-500'
                  : 'bg-dark-700 text-dark-600 border border-dark-600 hover:border-dark-500'
              }`}
            >
              <ArrowDownRight className="w-5 h-5" />
              Sell
            </button>
          </div>
        )}

        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-dark-600 mb-2">Quantity</label>
            <input
              type="number"
              step="0.0001"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) || 0 })}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm text-dark-600 mb-2">Price ({currency})</label>
            <input
              type="number"
              step="0.01"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm text-dark-600 mb-2">Fee ({currency})</label>
            <input
              type="number"
              step="0.01"
              value={formData.fee}
              onChange={(e) => setFormData({ ...formData, fee: parseFloat(e.target.value) || 0 })}
              className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm text-dark-600 mb-2">Total Amount</label>
            <div className="bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white font-medium">
              {formatCurrency(totalAmount, currency)}
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || (!selectedPosition && !formData.symbol) || formData.quantity <= 0 || formData.price <= 0}
          className="w-full flex items-center justify-center gap-2 py-3 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Plus className="w-5 h-5" />
          )}
          Record Trade
        </button>
      </form>
    </div>
  );
}

function TradeHistory() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshTransactions = async () => {
    setLoading(true);
    try {
      const res = await tradingApi.transactions.list();
      setTransactions(res.data);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-dark-700 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
      <div className="flex items-center justify-between p-6 border-b border-dark-700">
        <h2 className="text-lg font-semibold text-white">Trade History</h2>
        <button
          onClick={refreshTransactions}
          className="flex items-center gap-2 px-4 py-2 bg-dark-700 text-white rounded-lg hover:bg-dark-600 transition-colors"
        >
          <X className="w-4 h-4" />
          Refresh
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-dark-700/50">
              <th className="text-left px-6 py-3 text-sm font-medium text-dark-600">Symbol</th>
              <th className="text-left px-6 py-3 text-sm font-medium text-dark-600">Type</th>
              <th className="text-left px-6 py-3 text-sm font-medium text-dark-600">Side</th>
              <th className="text-right px-6 py-3 text-sm font-medium text-dark-600">Quantity</th>
              <th className="text-right px-6 py-3 text-sm font-medium text-dark-600">Price</th>
              <th className="text-right px-6 py-3 text-sm font-medium text-dark-600">Amount</th>
              <th className="text-right px-6 py-3 text-sm font-medium text-dark-600">Fee</th>
              <th className="text-right px-6 py-3 text-sm font-medium text-dark-600">Date</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length > 0 ? (
              transactions.map((transaction) => (
                <tr key={transaction.id} className="border-b border-dark-700 hover:bg-dark-700/30">
                  <td className="px-6 py-4 font-medium text-white">{transaction.symbol}</td>
                  <td className="px-6 py-4 text-sm text-dark-600">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      transaction.type === 'open' ? 'bg-blue-500/20 text-blue-500' :
                      transaction.type === 'add' ? 'bg-green-500/20 text-green-500' :
                      transaction.type === 'reduce' ? 'bg-yellow-500/20 text-yellow-500' :
                      'bg-red-500/20 text-red-500'
                    }`}>
                      {transaction.type}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      transaction.side === 'buy' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'
                    }`}>
                      {transaction.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-white">{transaction.quantity}</td>
                  <td className="px-6 py-4 text-right text-white">${transaction.price.toFixed(2)}</td>
                  <td className={`px-6 py-4 text-right font-medium ${
                    transaction.side === 'buy' ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {transaction.side === 'buy' ? '-' : '+'}${transaction.amount.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-right text-dark-600">-${transaction.fee.toFixed(2)}</td>
                  <td className="px-6 py-4 text-right text-dark-600 text-sm">
                    {new Date(transaction.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center text-dark-600">
                  No trades recorded yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function TradePage() {
  return (
    <Layout currentPage="trade">
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Trade</h1>
            <p className="text-dark-600 mt-1">Record your trades and manage positions</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-1">
            <TradeForm />
          </div>
          <div className="col-span-2">
            <TradeHistory />
          </div>
        </div>
      </div>
    </Layout>
  );
}