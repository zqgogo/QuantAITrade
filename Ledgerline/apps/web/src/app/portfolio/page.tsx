'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, PieChart, Wallet, ArrowRight } from 'lucide-react';
import Layout from '@/components/Layout';
import { tradingApi, PortfolioSummary, PositionAggregate } from '@/lib/api';
import { formatCurrency, Currency } from '@/lib/currency';

function PortfolioHeader({ summary, currency }: { summary: PortfolioSummary; currency: Currency }) {
  const isProfit = summary.total_pnl_percent >= 0;

  return (
    <div className="bg-gradient-to-r from-primary-500/20 to-primary-600/10 rounded-xl p-6 border border-primary-500/30">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-primary-400 mb-1">{summary.portfolio_name}</p>
          <h2 className="text-3xl font-bold text-white">{formatCurrency(summary.total_value, currency)}</h2>
          <div className="flex items-center gap-2 mt-2">
            <span className={`text-lg font-medium ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
              {isProfit ? '+' : ''}{formatCurrency(summary.total_pnl, currency)}
            </span>
            <span className={`text-sm ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
              ({isProfit ? '+' : ''}{summary.total_pnl_percent.toFixed(2)}%)
            </span>
            {isProfit ? <TrendingUp className="w-4 h-4 text-green-500" /> : <TrendingDown className="w-4 h-4 text-red-500" />}
          </div>
        </div>
        <div className="flex items-center gap-8">
          <div className="text-center">
            <p className="text-sm text-dark-600">Open Positions</p>
            <p className="text-xl font-bold text-white">{summary.positions.filter(p => p.status === 'open').length}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-dark-600">Total Trades</p>
            <p className="text-xl font-bold text-white">-</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-dark-600">Win Rate</p>
            <p className="text-xl font-bold text-white">-</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function PositionChart({ positions, currency }: { positions: PositionAggregate[]; currency: Currency }) {
  const openPositions = positions.filter(p => p.status === 'open');
  const totalValue = openPositions.reduce((sum, p) => sum + p.total_amount, 0);

  const colors = [
    'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500',
    'bg-pink-500', 'bg-orange-500', 'bg-cyan-500', 'bg-red-500'
  ];

  return (
    <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <PieChart className="w-5 h-5 text-primary-500" />
        Portfolio Allocation
      </h3>
      {totalValue > 0 ? (
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="#334155"
                strokeWidth="12"
              />
              {openPositions.map((position, index) => {
                const percentage = (position.total_amount / totalValue) * 100;
                const offset = openPositions.slice(0, index).reduce((sum, p) => sum + (p.total_amount / totalValue) * 100, 0);
                return (
                  <circle
                    key={position.position_id}
                    cx="64"
                    cy="64"
                    r="56"
                    fill="none"
                    stroke={colors[index % colors.length]}
                    strokeWidth="12"
                    strokeDasharray={`${percentage * 3.52} 352`}
                    strokeDashoffset={-offset * 3.52}
                    className="transition-all duration-500"
                  />
                );
              })}
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-lg font-bold text-white">{formatCurrency(totalValue, currency)}</p>
                <p className="text-xs text-dark-600">Total</p>
              </div>
            </div>
          </div>
          <div className="flex-1 space-y-3">
            {openPositions.map((position, index) => (
              <div key={position.position_id} className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${colors[index % colors.length]}`} />
                <span className="text-sm text-white flex-1">{position.symbol}</span>
                <span className="text-sm text-dark-600">
                  {((position.total_amount / totalValue) * 100).toFixed(1)}%
                </span>
                <span className="text-sm font-medium text-white">
                  {formatCurrency(position.total_amount, currency)}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <PieChart className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-600">No positions to display</p>
        </div>
      )}
    </div>
  );
}

function PositionDetail({ position, currency }: { position: PositionAggregate; currency: Currency }) {
  const isProfit = position.pnl_percent !== null && position.pnl_percent >= 0;

  return (
    <div className="bg-dark-800 rounded-xl p-6 border border-dark-700 hover:border-dark-600 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            position.side === 'buy' ? 'bg-green-500/20' : 'bg-red-500/20'
          }`}>
            <Wallet className={`w-5 h-5 ${
              position.side === 'buy' ? 'text-green-500' : 'text-red-500'
            }`} />
          </div>
          <div>
            <h4 className="font-semibold text-white text-lg">{position.symbol}</h4>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                position.side === 'buy' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'
              }`}>
                {position.side.toUpperCase()}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                position.status === 'open' ? 'bg-blue-500/20 text-blue-500' : 'bg-dark-700 text-dark-600'
              }`}>
                {position.status.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
        <div className={`text-right ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
          <p className="text-xl font-bold">
            {isProfit ? '+' : ''}{formatCurrency(position.pnl || 0, currency)}
          </p>
          <p className="text-sm">
            ({isProfit ? '+' : ''}{(position.pnl_percent || 0).toFixed(2)}%)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <div>
          <p className="text-xs text-dark-600">Quantity</p>
          <p className="text-white font-medium">{position.total_quantity}</p>
        </div>
        <div>
          <p className="text-xs text-dark-600">Avg Price</p>
          <p className="text-white font-medium">{formatCurrency(position.avg_price, currency)}</p>
        </div>
        <div>
          <p className="text-xs text-dark-600">Total Value</p>
          <p className="text-white font-medium">{formatCurrency(position.total_amount, currency)}</p>
        </div>
        <div>
          <p className="text-xs text-dark-600">Total Fees</p>
          <p className="text-dark-600 font-medium">{formatCurrency(position.total_fee, currency)}</p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-dark-700">
        <span className="text-xs text-dark-600">Opened: {new Date(position.opened_at).toLocaleDateString()}</span>
        <button className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          position.status === 'open'
            ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30'
            : 'bg-dark-700 text-dark-600 cursor-not-allowed'
        }`} disabled={position.status !== 'open'}>
          <ArrowRight className="w-4 h-4" />
          Close Position
        </button>
      </div>
    </div>
  );
}

export default function PortfolioPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [currency, setCurrency] = useState<Currency>('USD');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [summaryRes, portfolioRes] = await Promise.all([
          tradingApi.portfolios.summary(1),
          tradingApi.portfolios.get(1),
        ]);
        setSummary(summaryRes.data);
        setCurrency((portfolioRes.data.currency || 'USD') as Currency);
      } catch (error) {
        console.error('Failed to fetch portfolio data:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <Layout currentPage="portfolio">
        <div className="p-8">
          <div className="animate-pulse space-y-6">
            <div className="h-32 bg-dark-800 rounded-xl" />
            <div className="h-48 bg-dark-800 rounded-xl" />
            <div className="grid grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-48 bg-dark-800 rounded-xl" />
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!summary) {
    return (
      <Layout currentPage="portfolio">
        <div className="p-8">
          <div className="text-center py-16">
            <Wallet className="w-16 h-16 text-dark-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No Portfolio Found</h2>
            <p className="text-dark-600">Create a portfolio to start tracking your trades</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout currentPage="portfolio">
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Portfolio</h1>
            <p className="text-dark-600 mt-1">View your positions and performance</p>
          </div>
        </div>

        <div className="space-y-6">
          <PortfolioHeader summary={summary} currency={currency} />
          <PositionChart positions={summary.positions} currency={currency} />
          
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Position Details</h3>
            <div className="grid grid-cols-2 gap-6">
              {summary.positions.map((position) => (
                <PositionDetail key={position.position_id} position={position} currency={currency} />
              ))}
            </div>
            {summary.positions.length === 0 && (
              <div className="bg-dark-800 rounded-xl p-8 text-center border border-dark-700">
                <Wallet className="w-12 h-12 text-dark-600 mx-auto mb-3" />
                <p className="text-dark-600">No positions yet</p>
                <button className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors">
                  Record Your First Trade
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
