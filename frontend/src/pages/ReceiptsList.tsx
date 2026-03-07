import { useEffect, useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { fetchApi } from '@/services/api';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import { FileText, Search, Filter, Eye, RefreshCw, FileImage } from 'lucide-react';

interface Document {
  id: string;
  original_file_name: string;
  status: string;
  sender_name: string | null;
  amount_try: number | null;
  created_at: string;
}

interface PaginatedData {
  items: Document[];
  total: number;
}

export function ReceiptsList() {
  const [data, setData] = useState<PaginatedData>({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  
  const loadDocuments = async () => {
    try {
      setLoading(true);
      const endpoint = statusFilter ? `/documents?status=${statusFilter}` : '/documents';
      const result = await fetchApi(endpoint);
      setData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [statusFilter]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'UPLOADED':
        return <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold border border-blue-500/20">Yüklendi (OCR)</span>;
      case 'TG_PENDING':
        return <span className="px-3 py-1 rounded-full bg-yellow-500/10 text-yellow-400 text-xs font-semibold border border-yellow-500/20">Telegram Bekliyor</span>;
      case 'SLACK_PENDING':
        return <span className="px-3 py-1 rounded-full bg-orange-500/10 text-orange-400 text-xs font-semibold border border-orange-500/20">Slack Bekliyor</span>;
      case 'SLACK_APPROVED':
        return <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">Onaylandı</span>;
      case 'DEPOSIT_SUCCESS':
        return <span className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-xs font-semibold border border-green-500/20">Yatırım Başarılı</span>;
      default:
        if (status.includes('FAILED') || status.includes('REJECTED')) {
           return <span className="px-3 py-1 rounded-full bg-red-500/10 text-red-400 text-xs font-semibold border border-red-500/20">Red/Hata</span>;
        }
        return <span className="px-3 py-1 rounded-full bg-gray-500/10 text-gray-400 text-xs font-semibold border border-gray-500/20">{status}</span>;
    }
  };

  return (
    <Layout activePath="/receipts">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <FileText className="mr-3 text-primary" />
            Dekont Yönetimi
          </h1>
          <p className="text-muted-foreground">Sisteme yüklenen tüm belge kayıtları ve işlem durumları.</p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            <input 
              type="text" 
              placeholder="Gönderen vs..." 
              className="w-full bg-input/50 border border-border rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <div className="relative">
            <select 
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="appearance-none bg-input/50 border border-border rounded-lg pl-10 pr-8 py-2 text-sm focus:outline-none focus:border-primary transition-colors cursor-pointer"
            >
              <option value="">Tüm Durumlar</option>
              <option value="UPLOADED">Sadece Yüklenenler</option>
              <option value="TG_PENDING">Telegram PENDING</option>
              <option value="SLACK_PENDING">Slack PENDING</option>
              <option value="DEPOSIT_SUCCESS">Başarılı İşlemler</option>
            </select>
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
          </div>
          <button 
            onClick={loadDocuments}
            className="p-2 bg-input/50 border border-border rounded-lg hover:bg-input transition-colors text-muted-foreground hover:text-foreground"
          >
            <RefreshCw size={18} className={loading ? "animate-spin text-primary" : ""} />
          </button>
        </div>
      </div>

      <div className="glass rounded-xl overflow-hidden border border-border/50">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-black/20 text-muted-foreground border-b border-border/50">
              <tr>
                <th className="px-6 py-4 font-medium">Dosya</th>
                <th className="px-6 py-4 font-medium">Gönderen (OCR)</th>
                <th className="px-6 py-4 font-medium">Tutar (TRY)</th>
                <th className="px-6 py-4 font-medium">Tarih</th>
                <th className="px-6 py-4 font-medium">Durum</th>
                <th className="px-6 py-4 font-medium text-right">İşlem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    Veriler yükleniyor...
                  </td>
                </tr>
              ) : data.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground flex flex-col items-center">
                    <FileImage size={48} className="mb-4 text-border" />
                    Kriterlere uygun dekont bulunamadı
                  </td>
                </tr>
              ) : (
                data.items.map((doc) => (
                  <tr key={doc.id} className="hover:bg-white/5 transition-colors group">
                    <td className="px-6 py-4 font-medium text-foreground max-w-[200px] truncate" title={doc.original_file_name}>
                      {doc.original_file_name}
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">
                      {doc.sender_name || <span className="text-border italic">Bekleniyor...</span>}
                    </td>
                    <td className="px-6 py-4 font-medium">
                      {doc.amount_try ? `₺${doc.amount_try.toLocaleString('tr-TR')}` : '-'}
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">
                      {format(new Date(doc.created_at), 'd MMM yyyy HH:mm', { locale: tr })}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(doc.status)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-lg transition-colors inline-flex group-hover:opacity-100 opacity-60">
                        <Eye size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Info */}
        {!loading && data.items.length > 0 && (
          <div className="px-6 py-4 border-t border-border/50 bg-black/10 flex justify-between items-center text-sm text-muted-foreground">
            <div>Toplam <span className="text-foreground font-medium">{data.total}</span> kayıttan <span className="text-foreground font-medium">{data.items.length}</span> tanesi gösteriliyor.</div>
            <div className="flex gap-2">
              <button disabled className="px-3 py-1 bg-input/50 border border-border rounded-md opacity-50 cursor-not-allowed">Önceki</button>
              <button disabled className="px-3 py-1 bg-input/50 border border-border rounded-md opacity-50 cursor-not-allowed">Sonraki</button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
