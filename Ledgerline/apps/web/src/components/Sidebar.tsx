import Link from 'next/link';
import { LayoutDashboard, TrendingUp, Wallet, Bell, FileText, Settings } from 'lucide-react';

interface SidebarProps {
  currentPage: string;
}

const navItems = [
  { id: 'dashboard', label: '仪表盘', icon: LayoutDashboard },
  { id: 'trade', label: '交易记录', icon: TrendingUp },
  { id: 'portfolio', label: '持仓汇总', icon: Wallet },
  { id: 'notifications', label: '通知', icon: Bell },
  { id: 'reports', label: '报表', icon: FileText },
  { id: 'settings', label: '设置', icon: Settings },
];

export default function Sidebar({ currentPage }: SidebarProps) {
  return (
    <aside className="w-64 bg-dark-800 border-r border-dark-700 min-h-screen p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          Ledgerline
        </h1>
        <p className="text-xs text-dark-600 mt-1">AI Trading Workspace</p>
      </div>
      
      <nav className="flex-1">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <Link
                  href={`/${item.id}`}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors duration-200 ${
                    isActive
                      ? 'bg-primary-500/20 text-primary-400'
                      : 'text-dark-600 hover:bg-dark-700 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      <div className="mt-auto pt-4 border-t border-dark-700">
        <div className="flex items-center gap-3 px-4">
          <div className="w-8 h-8 rounded-full bg-dark-700 flex items-center justify-center">
            <span className="text-xs font-medium">U</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">User</p>
            <p className="text-xs text-dark-600">Premium</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
