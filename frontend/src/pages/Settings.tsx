import { Layout } from '@/components/layout/Layout';
import { Settings as SettingsIcon, Database, HardDrive, ShieldCheck } from 'lucide-react';

export function Settings() {
  return (
    <Layout activePath="/settings">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 flex items-center">
          <SettingsIcon className="mr-3 text-primary" />
          Sistem Ayarları
        </h1>
        <p className="text-muted-foreground">Bağlantı durumları ve ortam konfigürasyon özetleri.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Core System */}
        <div className="glass p-6 rounded-xl border border-border/50">
          <h3 className="text-lg font-bold mb-6 flex items-center border-b border-border/50 pb-4">
            <HardDrive className="mr-2 text-primary" size={20} />
            Altyapı Durumu
          </h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center bg-black/20 p-4 rounded-lg border border-white/5">
              <div>
                <p className="font-medium">Backend API URL</p>
                <p className="text-sm text-muted-foreground mt-1 text-mono hidden md:block">
                  {import.meta.env.VITE_API_URL || "http://localhost:8000"}
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-medium border border-success/20">Aktif</span>
            </div>

            <div className="flex justify-between items-center bg-black/20 p-4 rounded-lg border border-white/5">
              <div>
                <p className="font-medium">S3 Storage (AWS)</p>
                <p className="text-sm text-muted-foreground mt-1">Belge Saklama Alanı</p>
              </div>
              <span className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-medium border border-success/20">Bağlı</span>
            </div>

            <div className="flex justify-between items-center bg-black/20 p-4 rounded-lg border border-white/5">
              <div>
                <p className="font-medium">Celery Worker & Redis</p>
                <p className="text-sm text-muted-foreground mt-1">Asenkron Kuyruk Yöneticisi</p>
              </div>
              <span className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-medium border border-success/20">Çalışıyor</span>
            </div>
          </div>
        </div>

        {/* Security / Integrations */}
        <div className="glass p-6 rounded-xl border border-border/50">
          <h3 className="text-lg font-bold mb-6 flex items-center border-b border-border/50 pb-4">
            <ShieldCheck className="mr-2 text-primary" size={20} />
            Güvenlik & Entegrasyonlar
          </h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400"><Database size={20} /></div>
                <div>
                  <p className="font-medium">Slack Tüneli & Signature</p>
                  <p className="text-xs text-muted-foreground">HMAC-SHA256 Doğrulaması</p>
                </div>
              </div>
              <span className="text-success text-sm font-medium">Devrede</span>
            </div>

            <div className="flex justify-between items-center py-2 border-t border-border/30">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-cyan-500/20 rounded-lg text-cyan-400"><Database size={20} /></div>
                <div>
                  <p className="font-medium">Telegram Bot Token Check</p>
                  <p className="text-xs text-muted-foreground">X-Telegram-Bot-Api-Secret-Token</p>
                </div>
              </div>
              <span className="text-success text-sm font-medium">Devrede</span>
            </div>

             <div className="flex justify-between items-center py-2 border-t border-border/30">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg text-orange-400"><Database size={20} /></div>
                <div>
                  <p className="font-medium">API Rate Limiting (SlowAPI)</p>
                  <p className="text-xs text-muted-foreground">5 Req/Min per User</p>
                </div>
              </div>
              <span className="text-success text-sm font-medium">Devrede</span>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-border/50">
            <button className="w-full py-2.5 bg-primary/20 hover:bg-primary/30 text-primary font-medium rounded-lg border border-primary/30 transition-colors">
              Sunucu Sağlık Testini Çalıştır
            </button>
          </div>
        </div>

      </div>
    </Layout>
  );
}
