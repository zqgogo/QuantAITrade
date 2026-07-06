import { Settings, Bell, Shield, Palette, Database } from 'lucide-react';
import Layout from '@/components/Layout';

export default function SettingsPage() {
  return (
    <Layout currentPage="settings">
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Settings</h1>
            <p className="text-dark-600 mt-1">Configure your trading workspace</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 space-y-6">
            <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
                  <Bell className="w-5 h-5 text-primary-500" />
                </div>
                <h3 className="font-semibold text-white">Notifications</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">Trade Alerts</p>
                    <p className="text-sm text-dark-600">Receive notifications for trade executions</p>
                  </div>
                  <button className="w-12 h-6 bg-primary-500 rounded-full relative">
                    <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">Price Alerts</p>
                    <p className="text-sm text-dark-600">Get notified when prices hit your targets</p>
                  </div>
                  <button className="w-12 h-6 bg-dark-700 rounded-full relative">
                    <span className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full" />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">Daily Summary</p>
                    <p className="text-sm text-dark-600">Receive daily performance summary</p>
                  </div>
                  <button className="w-12 h-6 bg-primary-500 rounded-full relative">
                    <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                  </button>
                </div>
              </div>
            </div>

            <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <Palette className="w-5 h-5 text-green-500" />
                </div>
                <h3 className="font-semibold text-white">Appearance</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-dark-600 mb-3">Theme</p>
                  <div className="flex gap-3">
                    <button className="flex-1 py-3 bg-dark-700 border border-primary-500 rounded-lg text-white font-medium">
                      Dark
                    </button>
                    <button className="flex-1 py-3 bg-dark-700 border border-dark-600 rounded-lg text-dark-600 font-medium hover:text-white">
                      Light
                    </button>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-dark-600 mb-3">Accent Color</p>
                  <div className="flex gap-3">
                    {['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500', 'bg-pink-500'].map((color, index) => (
                      <button key={index} className={`w-10 h-10 rounded-full ${color} ${index === 0 ? 'ring-2 ring-white ring-offset-2 ring-offset-dark-800' : ''}`} />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-red-500" />
                </div>
                <h3 className="font-semibold text-white">Security</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">API Key</p>
                    <p className="text-sm text-dark-600">Your current API key</p>
                  </div>
                  <p className="font-mono text-sm text-dark-600">***-****-***</p>
                </div>
                <button className="w-full py-2 bg-dark-700 text-white rounded-lg hover:bg-dark-600 transition-colors text-sm">
                  Regenerate API Key
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                  <Database className="w-5 h-5 text-yellow-500" />
                </div>
                <h3 className="font-semibold text-white">Data</h3>
              </div>
              <button className="w-full py-2 bg-dark-700 text-white rounded-lg hover:bg-dark-600 transition-colors text-sm mb-3">
                Export All Data
              </button>
              <button className="w-full py-2 bg-red-500/20 text-red-500 rounded-lg hover:bg-red-500/30 transition-colors text-sm">
                Delete All Data
              </button>
            </div>

            <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
                  <Settings className="w-5 h-5 text-primary-500" />
                </div>
                <h3 className="font-semibold text-white">About</h3>
              </div>
              <div className="space-y-2 text-sm">
                <p className="text-dark-600">Version</p>
                <p className="text-white">0.1.0</p>
                <p className="text-dark-600 mt-4">Built with</p>
                <p className="text-white">Next.js + FastAPI</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
