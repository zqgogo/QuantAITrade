'use client';

import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Calendar, FileText, Download, ArrowUpRight, ArrowDownRight, AlertTriangle } from 'lucide-react';
import { tradingApi, type ReportStatsResponse } from '@/lib/api';

type Period = 'week' | 'month' | 'all';

const periodLabels: Record<Period, string> = {
  week: 'This Week',
  month: 'This Month',
  all: 'All Time',
};

function formatMoney(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(n);
}

function formatDate(d: string): string {
  const date = new Date(d + 'T00:00:00');
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

export default function ReportsPage() {
  const [period, setPeriod] = useState<Period>('week');
  const [data, setData] = useState<ReportStatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    tradingApi.reports.stats(period)
      .then(res => { if (!cancelled) setData(res.data); })
      .catch(err => {
        if (!cancelled) {
          setData(null);
          setError(err?.response?.data?.detail || err?.message || 'Failed to load report stats');
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [period]);

  const pnlPositive = (data?.realized_pnl ?? 0) >= 0;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Trading Reports</h1>
        <p className="text-dark-600">Review your trading performance across different periods</p>
      </div>

      {/* Period Tabs */}
      <div className="flex gap-2 mb-6">
        {(['week', 'month', 'all'] as Period[]).map(p => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              period === p
                ? 'bg-primary-500 text-white'
                : 'bg-dark-800 text-dark-500 hover:text-white border border-dark-700'
            }`}
          >
            {periodLabels[p]}
          </button>
        ))}
      </div>

      {loading && !data && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
        </div>
      )}

      {error && !loading && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4 mb-6">
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-500 mb-0.5">Failed to load report stats</p>
            <p className="text-sm text-dark-500">{error}</p>
          </div>
        </div>
      )}

      {data && (
        <>
          {/* Period info */}
          <div className="flex items-center gap-2 text-dark-600 mb-6 text-sm">
            <Calendar className="w-4 h-4" />
            <span>{data.start_date} — {data.end_date}</span>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              icon={<BarChart3 className="w-5 h-5" />}
              label="Total Trades"
              value={data.total_trades.toString()}
              accent="text-primary-500"
            />
            <StatCard
              icon={<ArrowUpRight className="w-5 h-5" />}
              label="Total Buy"
              value={formatMoney(data.total_buy)}
              accent="text-green-500"
            />
            <StatCard
              icon={<ArrowDownRight className="w-5 h-5" />}
              label="Total Sell"
              value={formatMoney(data.total_sell)}
              accent="text-red-500"
            />
            <StatCard
              icon={<FileText className="w-5 h-5" />}
              label="Fees"
              value={formatMoney(data.total_fee)}
              accent="text-yellow-500"
            />
          </div>

          {/* PnL Highlight */}
          <div className={`rounded-xl p-6 mb-8 border ${pnlPositive ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-500 text-sm mb-1">Realized P&L</p>
                <p className={`text-3xl font-bold ${pnlPositive ? 'text-green-500' : 'text-red-500'}`}>
                  {pnlPositive ? '+' : ''}{formatMoney(data.realized_pnl)}
                </p>
              </div>
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${pnlPositive ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                {pnlPositive ? <TrendingUp className="w-7 h-7 text-green-500" /> : <TrendingDown className="w-7 h-7 text-red-500" />}
              </div>
            </div>
          </div>

          {/* Daily Table */}
          <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-dark-700 flex items-center justify-between">
              <h3 className="font-semibold text-white">Daily Breakdown</h3>
              <button className="flex items-center gap-2 px-3 py-1.5 text-xs bg-dark-700 hover:bg-dark-600 text-dark-300 rounded-lg transition-colors">
                <Download className="w-3.5 h-3.5" />
                Export CSV
              </button>
            </div>
            {data.daily.length === 0 ? (
              <div className="py-16 text-center">
                <FileText className="w-12 h-12 text-dark-700 mx-auto mb-3" />
                <p className="text-dark-600">No trading activity in this period</p>
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-dark-600 border-b border-dark-700">
                    <th className="px-6 py-3 font-medium">Date</th>
                    <th className="px-6 py-3 font-medium text-right">Trades</th>
                    <th className="px-6 py-3 font-medium text-right">Buy</th>
                    <th className="px-6 py-3 font-medium text-right">Sell</th>
                    <th className="px-6 py-3 font-medium text-right">Fees</th>
                    <th className="px-6 py-3 font-medium text-right">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {data.daily.map(row => {
                    const pnlPositive = row.pnl >= 0;
                    return (
                      <tr key={row.date} className="border-b border-dark-700/50 hover:bg-dark-700/30">
                        <td className="px-6 py-3 text-sm text-white">{formatDate(row.date)}</td>
                        <td className="px-6 py-3 text-sm text-white text-right">{row.trades}</td>
                        <td className="px-6 py-3 text-sm text-green-500 text-right">{formatMoney(row.buy)}</td>
                        <td className="px-6 py-3 text-sm text-red-500 text-right">{formatMoney(row.sell)}</td>
                        <td className="px-6 py-3 text-sm text-yellow-500 text-right">{formatMoney(row.fee)}</td>
                        <td className={`px-6 py-3 text-sm text-right font-medium ${pnlPositive ? 'text-green-500' : 'text-red-500'}`}>
                          {pnlPositive ? '+' : ''}{formatMoney(row.pnl)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, accent }: { icon: React.ReactNode; label: string; value: string; accent: string }) {
  return (
    <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-9 h-9 rounded-lg bg-dark-700 flex items-center justify-center ${accent}`}>{icon}</div>
        <span className="text-sm text-dark-500">{label}</span>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
    </div>
  );
}
