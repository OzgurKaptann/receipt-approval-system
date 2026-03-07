import React from 'react';
import { LayoutDashboard, Receipt, Settings, LogOut } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activePath?: string;
}

export function Layout({ children, activePath = '/' }: LayoutProps) {
  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/receipts', icon: Receipt, label: 'Dekontlar' },
    { path: '/settings', icon: Settings, label: 'Ayarlar' },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 glass-panel border-r border-border flex flex-col justify-between hidden md:flex z-10 transition-all duration-300">
        <div>
          <div className="p-6">
            <h2 className="text-xl font-bold text-gradient-primary tracking-wide">FlowAdmin</h2>
            <p className="text-xs text-muted-foreground mt-1">Receipt Approval System</p>
          </div>
          
          <nav className="mt-6 px-4 space-y-2">
            {navItems.map((item) => {
              const isActive = activePath === item.path;
              return (
                <a
                  key={item.path}
                  href={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                    isActive 
                      ? 'bg-primary/20 text-primary font-medium border border-primary/20 shadow-[0_0_15px_rgba(59,130,246,0.15)]' 
                      : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
                  }`}
                >
                  <item.icon 
                    size={20} 
                    className={`${isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'} transition-colors`} 
                  />
                  <span>{item.label}</span>
                </a>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-border/50">
          <button className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors group">
            <LogOut size={20} className="group-hover:text-destructive transition-colors" />
            <span>Çıkış Yap</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-x-hidden overflow-y-auto bg-background/50 relative">
        {/* Subtle background glow effect */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        <div className="absolute bottom-0 right-1/4 w-[30rem] h-[30rem] bg-indigo-500/5 rounded-full blur-[120px] -z-10 pointer-events-none"></div>
        
        <div className="container mx-auto px-6 py-8 md:px-10 lg:px-12 h-full z-0">
          {children}
        </div>
      </main>
    </div>
  );
}
