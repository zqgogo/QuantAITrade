'use client';

import { useState, useEffect } from 'react';
import { Bell, Check, AlertCircle, TrendingUp, X } from 'lucide-react';
import Layout from '@/components/Layout';
import { tradingApi, Notification, Portfolio } from '@/lib/api';

const notificationIcons = {
  info: Bell,
  alert: AlertCircle,
  trade: TrendingUp,
};

function NotificationItem({ notification, onMarkRead }: { notification: Notification; onMarkRead: (id: number) => void }) {
  const Icon = notificationIcons[notification.type as keyof typeof notificationIcons] || Bell;

  return (
    <div className={`bg-dark-800 rounded-xl p-4 border transition-colors ${
      notification.read ? 'border-dark-700 opacity-60' : 'border-primary-500/30'
    }`}>
      <div className="flex items-start gap-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          notification.type === 'alert' ? 'bg-red-500/20' :
          notification.type === 'trade' ? 'bg-green-500/20' : 'bg-primary-500/20'
        }`}>
          <Icon className={`w-5 h-5 ${
            notification.type === 'alert' ? 'text-red-500' :
            notification.type === 'trade' ? 'text-green-500' : 'text-primary-500'
          }`} />
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-white">{notification.title}</h4>
          <p className="text-sm text-dark-600 mt-1">{notification.message}</p>
          <p className="text-xs text-dark-600 mt-2">
            {new Date(notification.created_at).toLocaleDateString()}
          </p>
        </div>
        {!notification.read && (
          <button
            onClick={() => onMarkRead(notification.id)}
            className="flex items-center gap-2 px-3 py-2 bg-dark-700 text-white rounded-lg hover:bg-dark-600 transition-colors text-sm"
          >
            <Check className="w-4 h-4" />
            Mark Read
          </button>
        )}
      </div>
    </div>
  );
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPortfolios() {
      try {
        const res = await tradingApi.portfolios.list();
        setPortfolios(res.data);
        if (res.data.length > 0) {
          setSelectedPortfolioId(res.data[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch portfolios:', error);
      }
    }
    fetchPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolioId) {
      fetchNotifications();
    }
  }, [selectedPortfolioId]);

  async function fetchNotifications() {
    if (!selectedPortfolioId) return;
    setLoading(true);
    try {
      const res = await tradingApi.notifications.list(selectedPortfolioId);
      setNotifications(res.data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleMarkRead(id: number) {
    try {
      await tradingApi.notifications.markRead(id);
      setNotifications(notifications.map(n => n.id === id ? { ...n, read: true } : n));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }

  const unreadCount = notifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <Layout currentPage="notifications">
        <div className="p-8">
          <div className="animate-pulse space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-24 bg-dark-800 rounded-xl" />
            ))}
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout currentPage="notifications">
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Notifications</h1>
            <p className="text-dark-600 mt-1">
              {unreadCount > 0 ? `${unreadCount} unread notifications` : 'All caught up'}
            </p>
          </div>
          <div className="flex gap-4">
            {portfolios.length > 0 && (
              <select
                value={selectedPortfolioId || ''}
                onChange={(e) => setSelectedPortfolioId(parseInt(e.target.value))}
                className="bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            )}
            <button
              onClick={async () => {
                if (selectedPortfolioId) {
                  await tradingApi.notifications.markAllRead(selectedPortfolioId);
                  setNotifications(notifications.map(n => ({ ...n, read: true })));
                }
              }}
              className="flex items-center gap-2 px-4 py-2 bg-dark-700 text-white rounded-lg hover:bg-dark-600 transition-colors"
            >
              <X className="w-4 h-4" />
              Mark All Read
            </button>
          </div>
        </div>

        {notifications.length > 0 ? (
          <div className="space-y-4">
            {notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkRead={handleMarkRead}
              />
            ))}
          </div>
        ) : (
          <div className="bg-dark-800 rounded-xl p-12 text-center border border-dark-700">
            <Bell className="w-16 h-16 text-dark-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No Notifications</h2>
            <p className="text-dark-600">You're all caught up</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
