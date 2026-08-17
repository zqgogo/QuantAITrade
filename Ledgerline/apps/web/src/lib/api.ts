import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || 'dev-secret-key',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface Workspace {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface Portfolio {
  id: number;
  workspace_id: number;
  name: string;
  currency: string;
  description: string;
  created_at: string;
}

export interface Transaction {
  id: number;
  portfolio_id: number;
  position_id: number | null;
  market: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'open' | 'add' | 'reduce' | 'close';
  quantity: number;
  price: number;
  amount: number;
  fee: number;
  created_at: string;
}

export interface Position {
  id: number;
  portfolio_id: number;
  market: string;
  symbol: string;
  side: 'buy' | 'sell';
  status: 'open' | 'closed';
  opened_at: string;
  closed_at: string | null;
  created_at: string;
}

export interface PositionAggregate {
  position_id: number;
  portfolio_id: number;
  market: string;
  symbol: string;
  side: 'buy' | 'sell';
  status: 'open' | 'closed';
  total_quantity: number;
  avg_price: number;
  total_amount: number;
  total_fee: number;
  currency: string;
  current_price: number | null;
  pnl: number | null;
  pnl_percent: number | null;
  opened_at: string;
  closed_at: string | null;
}

export interface PortfolioSummary {
  portfolio_id: number;
  portfolio_name: string;
  currency: string;
  total_pnl: number;
  total_pnl_percent: number;
  total_value: number;
  positions: PositionAggregate[];
}

export interface WatchlistItem {
  id: number;
  portfolio_id: number;
  market: string;
  symbol: string;
  alias: string | null;
  created_at: string;
}

export interface Notification {
  id: number;
  portfolio_id: number;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  session_id?: number;
  workspace_id?: number;
  include_context?: boolean;
  model?: string;
}

export interface ChatResponse {
  content: string;
  timestamp: string;
  model: string;
  runtime: string;
  context_used: boolean;
  session_id?: number;
}

export interface ChatSessionResponse {
  id: number;
  title: string;
  workspace_id: number | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatSessionDetail {
  id: number;
  title: string;
  workspace_id: number | null;
  created_at: string;
  updated_at: string;
  messages: { id: number; role: string; content: string; created_at: string }[];
}

export interface AiStatusResponse {
  module: string;
  status: string;
  llm_provider: string;
  embedding_provider: string;
  embedding_model: string;
  agent_runtime: string;
  available_models: string[];
}

export interface TradeRecordRequest {
  portfolio_id: number;
  market: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'open' | 'add' | 'reduce' | 'close';
  quantity: number;
  price: number;
  fee?: number;
}

export const aiApi = {
  status: () => api.get<AiStatusResponse>('/ai/status'),
  chat: (data: ChatRequest) => api.post<ChatResponse>('/ai/chat', data),
  sessions: {
    list: () => api.get<{ sessions: ChatSessionResponse[] }>('/ai/sessions'),
    create: (title: string) => api.post<ChatSessionResponse>('/ai/sessions', { title }),
    get: (id: number) => api.get<ChatSessionDetail>(`/ai/sessions/${id}`),
    delete: (id: number) => api.delete(`/ai/sessions/${id}`),
  },
  chatSignal: (params: { strategy: string; symbol: string; market: string; interval: string }) => 
    api.post<ChatResponse>('/ai/chat/signal', null, { params }),
  chatPortfolio: () => api.post<ChatResponse>('/ai/chat/portfolio'),
  context: () => api.get<AiContext>('/ai/context'),
};

export interface AiContext {
  positions_count: number;
  total_value: number;
  recent_trades_count: number;
  watchlist_count: number;
}

export const tradingApi = {
  workspaces: {
    list: () => api.get<Workspace[]>('/trading/workspaces'),
    create: (data: { name: string; description?: string }) => api.post<Workspace>('/trading/workspaces', data),
    get: (id: number) => api.get<Workspace>(`/trading/workspaces/${id}`),
  },
  portfolios: {
    list: (workspaceId?: number) => api.get<Portfolio[]>('/trading/portfolios', { params: { workspace_id: workspaceId } }),
    create: (data: { workspace_id: number; name: string; description?: string }) => api.post<Portfolio>('/trading/portfolios', data),
    get: (id: number) => api.get<Portfolio>(`/trading/portfolios/${id}`),
    summary: (id: number, currentPrices?: { [key: string]: number }) => 
      api.get<PortfolioSummary>(`/trading/portfolios/${id}/summary`, { params: { current_prices: JSON.stringify(currentPrices || {}) } }),
  },
  transactions: {
    list: (portfolioId?: number) => api.get<Transaction[]>('/trading/transactions', { params: { portfolio_id: portfolioId } }),
    record: (data: TradeRecordRequest) => api.post<Transaction>('/trading/transactions', data),
  },
  positions: {
    get: (id: number, currentPrice?: number) => 
      api.get<PositionAggregate>(`/trading/positions/${id}`, { params: { current_price: currentPrice } }),
  },
  watchlist: {
    list: (portfolioId: number) => api.get<WatchlistItem[]>(`/trading/portfolios/${portfolioId}/watchlist`),
    add: (data: { portfolio_id: number; market: string; symbol: string; alias?: string }) => api.post<WatchlistItem>('/trading/watchlist', data),
    update: (id: number, data: { alias?: string; alert_price_high?: number; alert_price_low?: number }) => api.put<WatchlistItem>(`/trading/watchlist/${id}`, data),
    remove: (id: number) => api.delete(`/trading/watchlist/${id}`),
  },
  notifications: {
    list: (portfolioId: number) => api.get<Notification[]>(`/trading/portfolios/${portfolioId}/notifications`),
    markRead: (id: number) => api.put(`/trading/notifications/${id}/read`),
    markAllRead: (portfolioId: number) => api.put(`/trading/portfolios/${portfolioId}/notifications/read-all`),
  },
  reports: {
    stats: (period: 'week' | 'month' | 'all') =>
      api.get<ReportStatsResponse>('/trading/reports/stats', { params: { period } }),
  },
};

export interface DailyReportRow {
  date: string;
  trades: number;
  buy: number;
  sell: number;
  fee: number;
  pnl: number;
}

export interface ReportStatsResponse {
  period: string;
  start_date: string;
  end_date: string;
  total_trades: number;
  total_buy: number;
  total_sell: number;
  total_fee: number;
  realized_pnl: number;
  net_volume: number;
  daily: DailyReportRow[];
}

export const marketApi = {
  price: (market: string, symbol: string) => api.get<{ market: string; symbol: string; price: number; timestamp: string }>('/market/price', { params: { market, symbol } }),
};

export default api;
