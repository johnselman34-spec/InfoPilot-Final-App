import React, { useState } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { DollarSign, TrendingUp, Store, CreditCard, Download, RefreshCw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const RevenuePage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const [exporting, setExporting] = useState(false);
  
  const { data, isLoading } = useQuery({
    queryKey: ["revenue"],
    queryFn: () => axios.get(`${API}/revenue/dashboard`).then(r => r.data),
    enabled: !!user
  });

  if (!user) return <Navigate to="/login" />;

  const exportReport = async (format) => {
    setExporting(true);
    try {
      const response = await axios.get(`${API}/revenue/export?format=${format}`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: format === 'pdf' ? 'application/pdf' : 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `revenue_report_${new Date().toISOString().split('T')[0]}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      showToast(`${format.toUpperCase()} downloaded! 📊`, "success");
    } catch (err) {
      showToast("Export failed", "error");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">Revenue Dashboard</h1>
            <p className="text-white/60">Track your protocol sales and earnings (85% commission)</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => exportReport('csv')} className="bg-slate-700 hover:bg-slate-600" disabled={exporting} data-testid="export-csv-btn">
              <Download className="mr-2" size={16} /> CSV
            </Button>
            <Button onClick={() => exportReport('pdf')} className="btn-gold" disabled={exporting} data-testid="export-pdf-btn">
              <Download className="mr-2" size={16} /> {exporting ? "Exporting..." : "PDF Report"}
            </Button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12"><RefreshCw className="animate-spin mx-auto text-yellow-400" size={48} /></div>
        ) : (
          <>
            <div className="grid md:grid-cols-4 gap-6 mb-8">
              <Card className="card-glass p-6 text-center" data-testid="total-revenue-card">
                <DollarSign className="mx-auto text-green-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">${data?.total_revenue?.toFixed(2) || '0.00'}</p>
                <p className="text-white/60 text-sm">Your Earnings (85%)</p>
              </Card>
              <Card className="card-glass p-6 text-center" data-testid="total-sales-card">
                <TrendingUp className="mx-auto text-blue-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">{data?.total_sales || 0}</p>
                <p className="text-white/60 text-sm">Total Sales</p>
              </Card>
              <Card className="card-glass p-6 text-center">
                <Store className="mx-auto text-purple-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">{data?.top_protocols?.length || 0}</p>
                <p className="text-white/60 text-sm">Products Sold</p>
              </Card>
              <Card className="card-glass p-6 text-center">
                <CreditCard className="mx-auto text-yellow-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">${data?.wallet_balance?.toFixed(2) || '0.00'}</p>
                <p className="text-white/60 text-sm">Pending Payout</p>
              </Card>
            </div>

            {/* Monthly Revenue Chart */}
            {Object.keys(data?.monthly_revenue || {}).length > 0 && (
              <Card className="card-glass p-6 mb-8" data-testid="monthly-revenue-chart">
                <h3 className="text-xl font-bold text-yellow-400 mb-4">Monthly Revenue</h3>
                <div className="grid grid-cols-6 gap-2">
                  {Object.entries(data?.monthly_revenue || {}).slice(-6).map(([month, revenue]) => (
                    <div key={month} className="text-center">
                      <div className="h-24 bg-gradient-to-t from-green-500/30 to-green-500/80 rounded-t-lg flex items-end justify-center relative" style={{ height: `${Math.max(20, (revenue / (data.total_revenue || 1)) * 100)}px` }}>
                        <span className="text-xs text-white font-bold p-1">${revenue.toFixed(0)}</span>
                      </div>
                      <p className="text-white/50 text-xs mt-1">{month.slice(5)}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            <Card className="card-glass p-6">
              <h3 className="text-xl font-bold text-yellow-400 mb-4">Top Selling Protocols</h3>
              {data?.top_protocols?.length === 0 ? (
                <div className="text-center py-8">
                  <Store className="mx-auto text-white/30 mb-4" size={48} />
                  <p className="text-white/60">No sales yet. List your protocols in the marketplace!</p>
                  <Link to="/marketplace"><Button className="btn-gold mt-4">Go to Marketplace</Button></Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {data?.top_protocols?.map((p, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-lg hover:bg-white/10 transition">
                      <div className="flex items-center gap-4">
                        <span className="text-2xl">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                        <div>
                          <p className="text-white font-semibold">{p.name}</p>
                          <p className="text-white/50 text-sm">{p.count} sales</p>
                        </div>
                      </div>
                      <Badge className="bg-green-500/20 text-green-300 text-lg">${p.revenue?.toFixed(2)}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </div>
  );
};

export default RevenuePage;
