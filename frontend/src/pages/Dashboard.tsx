import { useEffect, useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { fetchApi } from '@/services/api';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { 
  TrendingUp, 
  DollarSign, 
  FileCheck, 
  FileX, 
  Files,
  Activity
} from 'lucide-react';

interface DashboardMetrics {
  total_uploaded: number;
  total_approved: number;
  total_failed: number;
  total_try_volume: number;
  total_usd_volume: number;
  success_rate: number;
}

interface DailyInvestment {
  date: string;
  amount_try: number;
  amount_usd: number;
  count: number;
}

export function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [dailyData, setDailyData] = useState<DailyInvestment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const [metricsRes, dailyRes] = await Promise.all([
          fetchApi('/documents/metrics'),
          fetchApi('/documents/daily-investments')
        ]);
        setMetrics(metricsRes);
        // Reverse array to show oldest to newest on the chart
        setDailyData(dailyRes.slice().reverse());
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) {
    return (
      <Layout activePath="/">
        <div className="flex items-center justify-center h-[80vh]">
          <div className="animate-pulse flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-muted-foreground">Veriler Yükleniyor...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout activePath="/">
        <div className="glass p-6 rounded-xl border-destructive/50 bg-destructive/10 text-center">
          <p className="text-destructive font-medium">Bağlantı Hatası: {error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout activePath="/">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Genel Bakış</h1>
        <p className="text-muted-foreground">Sisteme yüklenen tüm dekontların onay performans ve hacim analizleri.</p>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        <div className="glass p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-all duration-500"></div>
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">Toplam Yatırım (USD)</p>
              <h3 className="text-3xl font-bold flex items-center">
                <span className="text-primary mr-1">$</span>
                {metrics?.total_usd_volume.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h3>
            </div>
            <div className="p-3 bg-primary/20 rounded-lg text-primary">
              <DollarSign size={24} />
            </div>
          </div>
          <div className="flex items-center text-sm">
            <TrendingUp size={16} className="text-success mr-1" />
            <span className="text-success font-medium">TRY: ₺{metrics?.total_try_volume.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
        </div>

        <div className="glass p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-all"></div>
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">Toplam Eklenen</p>
              <h3 className="text-3xl font-bold">{metrics?.total_uploaded}</h3>
            </div>
            <div className="p-3 bg-white/10 rounded-lg text-foreground">
              <Files size={24} />
            </div>
          </div>
        </div>

        <div className="glass p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-success/10 rounded-full blur-2xl group-hover:bg-success/20 transition-all"></div>
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">Onaylanan İşlem</p>
              <h3 className="text-3xl font-bold text-success">{metrics?.total_approved}</h3>
            </div>
            <div className="p-3 bg-success/20 rounded-lg text-success">
              <FileCheck size={24} />
            </div>
          </div>
          <div className="flex items-center text-sm">
            <span className="text-muted-foreground">Başarı Oranı: </span>
            <span className="text-foreground ml-1 font-medium">{metrics?.success_rate}%</span>
          </div>
        </div>

        <div className="glass p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-destructive/10 rounded-full blur-2xl group-hover:bg-destructive/20 transition-all"></div>
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">Başarısız/Reddedilen</p>
              <h3 className="text-3xl font-bold text-destructive">{metrics?.total_failed}</h3>
            </div>
            <div className="p-3 bg-destructive/20 rounded-lg text-destructive">
              <FileX size={24} />
            </div>
          </div>
        </div>

      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main Chart */}
        <div className="lg:col-span-2 glass p-6 rounded-xl">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold flex items-center">
              <Activity className="mr-2 text-primary" size={20} />
              Günlük Yatırım Hacim (Son 30 Gün)
            </h3>
          </div>
          <div className="h-80 w-full">
            {dailyData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dailyData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    stroke="#a1a1aa" 
                    fontSize={12} 
                    tickFormatter={(val) => new Date(val).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
                  />
                  <YAxis 
                    stroke="#a1a1aa" 
                    fontSize={12} 
                    tickFormatter={(val) => `$${val > 1000 ? (val/1000).toFixed(1) + 'k' : val}`}
                  />
                  <Tooltip 
                    cursor={{fill: '#27272a', opacity: 0.4}}
                    contentStyle={{ backgroundColor: '#121214', borderColor: '#27272a', borderRadius: '8px' }}
                    labelFormatter={(label) => new Date(label).toLocaleDateString('tr-TR')}
                  />
                  <Bar dataKey="amount_usd" name="Hacim (USD)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground line-dash">
                Henüz yatırım verisi bulunmuyor
              </div>
            )}
          </div>
        </div>

        {/* Info Box */}
        <div className="glass rounded-xl p-6 flex flex-col">
          <h3 className="text-lg font-bold mb-6">Sistem Durumu</h3>
          <div className="space-y-6 flex-1">
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-success mr-3 animate-pulse"></div>
              <div>
                <p className="font-medium">Backend API</p>
                <p className="text-sm text-foreground/60">Bağlantı Kuruldu</p>
              </div>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-success mr-3"></div>
              <div>
                <p className="font-medium">Slack Tüneli</p>
                <p className="text-sm text-foreground/60">Hazır</p>
              </div>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-success mr-3"></div>
              <div>
                <p className="font-medium">Telegram Bodu</p>
                <p className="text-sm text-foreground/60">Hazır</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-border">
            <p className="text-sm text-muted-foreground italic mb-2">
              Kritik Slack Komutu Eklendi:
            </p>
            <code className="block bg-black/40 p-3 rounded-md text-primary font-mono text-sm border border-white/5">
              /yatirim gg-aa-yyyy
            </code>
          </div>
        </div>

      </div>
    </Layout>
  );
}
