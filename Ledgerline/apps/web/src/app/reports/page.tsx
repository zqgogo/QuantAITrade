import { FileText, Calendar, Download } from 'lucide-react';
import Layout from '@/components/Layout';

export default function ReportsPage() {
  return (
    <Layout currentPage="reports">
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Reports</h1>
            <p className="text-dark-600 mt-1">Generate and export trading reports</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-lg bg-primary-500/20 flex items-center justify-center">
                <FileText className="w-6 h-6 text-primary-500" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Weekly Report</h3>
                <p className="text-sm text-dark-600">Summary of weekly trading activity</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-dark-600">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">Last 7 days</span>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors text-sm">
                <Download className="w-4 h-4" />
                Generate
              </button>
            </div>
          </div>

          <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
                <FileText className="w-6 h-6 text-green-500" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Monthly Report</h3>
                <p className="text-sm text-dark-600">Detailed monthly performance analysis</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-dark-600">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">Last 30 days</span>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors text-sm">
                <Download className="w-4 h-4" />
                Generate
              </button>
            </div>
          </div>

          <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <FileText className="w-6 h-6 text-yellow-500" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Profit & Loss Report</h3>
                <p className="text-sm text-dark-600">Track your overall PnL performance</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-dark-600">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">All time</span>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors text-sm">
                <Download className="w-4 h-4" />
                Generate
              </button>
            </div>
          </div>

          <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <FileText className="w-6 h-6 text-purple-500" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Trade History</h3>
                <p className="text-sm text-dark-600">Complete export of all trades</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-dark-600">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">All time</span>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors text-sm">
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
