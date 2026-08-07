'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Wallet, Clock, ArrowRight } from 'lucide-react';
import Layout from '@/components/Layout';
import { tradingApi, marketApi, PortfolioSummary, PositionAggregate, Transaction } from '@/lib/api';
import { formatCurrency, Currency } from '@/lib/currency';

function StatCard({ title, value, change, changeType, icon: Icon }: { 
  title: string; 
  value: string; 
  change: string; 
  changeType: 'up' | 'down' | 'neutral';
  icon: typeof TrendingUp;
}) {
  return (
    <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            changeType === 'up' ? 'bg-green-500/20' : 
            changeType === 'down' ? 'bg-red-500/20' : 'bg-dark-700'
          }`}>
            <Icon className={`w-5 h-5 ${
              changeType === 'up' ? 'text-green-500' : 
              changeType === 'down' ? 'text-red-500' : 'text-dark-600'
            }`} />
          </div>
          <div>
            <p className="text-sm text-dark-600">{title}</p>
            <p className="text-xl font-bold text-white">{value}</p>
          </div>
        </div>
        <div className={`text-right ${
          changeType === 'up' ? 'text-green-500' : 
          changeType === 'down' ? 'text-red-500' : 'text-dark-600'
        }`}>
          <p className="text-sm font-medium">{change}</p>
          {changeType === 'up' ? <TrendingUp className="w-4 h-4 mx-auto" /> : 
           changeType === 'down' ? <TrendingDown className="w-4 h-4 mx-auto" /> : null}
        </div>
      </div>
    </div>
  );
}

function PositionCard({ position, currency }: { position: PositionAggregate; currency: Currency }) {
  const isProfit = position.pnl_percent !== null && position.pnl_percent >= 0;
  return (
    <div className="bg-dark-800 rounded-lg p-4 border border-dark-700 hover:border-dark-600 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="font-medium text-white">{position.symbol}</p>
          <p className="text-xs text-dark-600">{position.side.toUpperCase()} Position</p>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          position.status === 'open' ? 'bg-green-500/20 text-green-500' : 'bg-dark-700 text-dark-600'
        }`}>
          {position.status === 'open' ? 'Open' : 'Closed'}
        </span>
      </div>
      <div className="grid grid-cols-4 gap-3 text-sm">
        <div>
          <p className="text-dark-600 text-xs">Quantity</p>
          <p className="text-white font-medium">{position.total_quantity}</p>
        </div>
        <div>
          <p className="text-dark-600 text-xs">Avg Price</p>
          <p className="text-white font-medium">{formatCurrency(position.avg_price, currency)}</p>
        </div>
        <div>
          <p className="text-dark-600 text-xs">Current</p>
          <p className="text-white font-medium">
            {position.current_price !== null ? formatCurrency(position.current_price, currency) : '-'}
          </p>
        </div>
        <div>
          <p className="text-dark-600 text-xs">PnL</p>
          <p className={`font-medium ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
            {isProfit ? '+' : ''}{formatCurrency(position.pnl || 0, currency)}
            {position.pnl_percent !== null && position.pnl_percent !== 0 && (
              <span className="text-xs ml-1">({isProfit ? '+' : ''}{position.pnl_percent.toFixed(2)}%)</span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}

function TransactionItem({ transaction }: { transaction: Transaction }) {
  const isBuy = transaction.side === 'buy';
  return (
    <div className="flex items-center justify-between py-3 border-b border-dark-700 last:border-0">
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isBuy ? 'bg-green-500/20' : 'bg-red-500/20'
        }`}>
          <ArrowRight className={`w-4 h-4 ${isBuy ? 'text-green-500' : 'text-red-500'}`} />
        </div>
        <div>
          <p className="font-medium text-white">{transaction.symbol}</p>
          <p className="text-xs text-dark-600">{transaction.type} · {new Date(transaction.created_at).toLocaleDateString()}</p>
        </div>
      </div>
      <div className="text-right">
        <p className={`font-medium ${isBuy ? 'text-green-500' : 'text-red-500'}`}>
          {isBuy ? '+' : '-'}{transaction.amount.toFixed(2)}
        </p>
        <p className="text-xs text-dark-600">@{transaction.price}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [currency, setCurrency] = useState<Currency>('USD');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [summaryRes, transactionsRes, portfolioRes] = await Promise.all([
          tradingApi.portfolios.summary(1),
          tradingApi.transactions.list(),
          tradingApi.portfolios.get(1),
        ]);

        const summaryData = summaryRes.data;
        const openPositions = summaryData.positions.filter(p => p.status === 'open');
        
        const priceMap: { [key: string]: number } = {};
        await Promise.all(openPositions.map(async (p: PositionAggregate) => {
          try {
            const priceRes = await marketApi.price(p.market, p.symbol);
            priceMap[`${p.market}:${p.symbol}`] = priceRes.data.price;
          } catch {}
        }));

        let finalSummary = summaryData;
        if (Object.keys(priceMap).length > 0) {
          const priceSummaryRes = await tradingApi.portfolios.summary(1, priceMap);
          finalSummary = priceSummaryRes.data;
        }

        setSummary(finalSummary);
        setTransactions(transactionsRes.data.slice(0, 5));
        setCurrency((portfolioRes.data.currency || 'USD') as Currency);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Layout currentPage="dashboard">
        <div className="p-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-dark-700 rounded w-48" />
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-dark-800 rounded-xl" />
              ))}
            </div>
            <div className="grid grid-cols-3 gap-6">
              <div className="h-80 bg-dark-800 rounded-xl col-span-2" />
              <div className="h-80 bg-dark-800 rounded-xl" />
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  const stats: { title: string; value: string; change: string; changeType: 'up' | 'down' | 'neutral'; icon: typeof Wallet }[] = [
    { title: 'Total Balance', value: formatCurrency(summary?.total_value || 0, currency), change: '+5.2%', changeType: 'up', icon: Wallet },
    { title: 'Open Positions', value: `${summary?.positions.filter(p => p.status === 'open').length || 0}`, change: '+2', changeType: 'up', icon: TrendingUp },
    { title: 'Total PnL', value: formatCurrency(summary?.total_pnl || 0, currency), change: `${(summary?.total_pnl_percent || 0).toFixed(2)}%`, changeType: (summary?.total_pnl_percent || 0) >= 0 ? 'up' : 'down', icon: TrendingUp },
    { title: 'Last Trade', value: '-', change: '-', changeType: 'neutral', icon: Clock },
  ];

  return (
    <Layout currentPage="dashboard">
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-dark-600 mt-1">Welcome back, here is your trading overview</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-dark-600">Today</p>
            <p className="text-lg font-medium text-white">{new Date().toLocaleDateString()}</p>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          {stats.map((stat, index) => (
            <StatCard key={index} {...stat} />
          ))}
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Open Positions</h2>
              <button className="text-sm text-primary-500 hover:text-primary-400">View All</button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {summary?.positions.filter(p => p.status === 'open').map((position) => (
                <PositionCard key={position.position_id} position={position} currency={currency} />
              ))}
              {(!summary || summary.positions.filter(p => p.status === 'open').length === 0) && (
                <div className="col-span-2 bg-dark-800 rounded-xl p-8 text-center border border-dark-700">
                  <p className="text-dark-600">No open positions</p>
                  <button className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors">
                    Open New Position
                  </button>
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Recent Trades</h2>
              <button className="text-sm text-primary-500 hover:text-primary-400">View All</button>
            </div>
            <div className="bg-dark-800 rounded-xl p-4 border border-dark-700">
              {transactions.length > 0 ? (
                transactions.map((transaction) => (
                  <TransactionItem key={transaction.id} transaction={transaction} />
                ))
              ) : (
                <p className="text-dark-600 text-center py-8">No recent trades</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
