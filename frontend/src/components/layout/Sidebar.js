import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useFirm } from '@/contexts/FirmContext';
import {
  LayoutDashboard, Building2, FolderKanban, FileText,
  Settings, LogOut, ChevronLeft, ChevronRight, Bot, ChevronsUpDown, Check
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

const navItems = [
  { path: '/dashboard', label: 'Panou', icon: LayoutDashboard },
  { path: '/organizations', label: 'Firme', icon: Building2 },
  { path: '/dosare', label: 'Dosare', icon: FolderKanban },
  { path: '/documents', label: 'Documente', icon: FileText },
  { path: '/agents', label: 'Agenți AI', icon: Bot },
  { path: '/admin', label: 'Admin', icon: Settings },
];

export function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { firms, activeFirm, selectFirm } = useFirm();
  const [firmPopoverOpen, setFirmPopoverOpen] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        data-testid="sidebar"
        className={`fixed left-0 top-0 h-screen bg-white border-r border-border flex flex-col z-40 transition-all duration-300 shadow-sm ${collapsed ? 'w-16' : 'w-64'}`}
      >
        <div className="h-16 flex items-center px-4 border-b border-border gap-2">
          <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-primary-foreground" />
          </div>
          {!collapsed && <span className="font-heading text-lg font-bold tracking-tight">GrantFlow</span>}
          <Button variant="ghost" size="icon" className="ml-auto h-8 w-8" onClick={onToggle} data-testid="sidebar-toggle">
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
        </div>

        {/* Firm Selector */}
        {!collapsed && firms.length > 0 && (
          <div className="px-3 py-3 border-b border-border">
            <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-1.5 px-1">Firmă activă</p>
            <Popover open={firmPopoverOpen} onOpenChange={setFirmPopoverOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-between h-auto py-2 px-3 text-left"
                  data-testid="firm-selector"
                >
                  <div className="truncate">
                    <p className="text-sm font-semibold truncate">{activeFirm?.denumire || 'Selectează firma'}</p>
                    {activeFirm?.cui && <p className="text-[11px] text-muted-foreground">CUI: {activeFirm.cui}</p>}
                  </div>
                  <ChevronsUpDown className="w-4 h-4 text-muted-foreground flex-shrink-0 ml-2" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-56 p-1" align="start">
                {firms.map((f) => (
                  <button
                    key={f.id}
                    className={`w-full text-left px-3 py-2 rounded-md text-sm hover:bg-accent flex items-center gap-2 ${activeFirm?.id === f.id ? 'bg-accent' : ''}`}
                    onClick={() => { selectFirm(f); setFirmPopoverOpen(false); }}
                    data-testid={`firm-option-${f.id}`}
                  >
                    <div className="flex-1 truncate">
                      <p className="font-medium truncate">{f.denumire}</p>
                      <p className="text-[11px] text-muted-foreground">CUI: {f.cui}</p>
                    </div>
                    {activeFirm?.id === f.id && <Check className="w-4 h-4 text-primary flex-shrink-0" />}
                  </button>
                ))}
              </PopoverContent>
            </Popover>
          </div>
        )}

        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            const Icon = item.icon;
            const btn = (
              <Link
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.path.slice(1)}`}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-[15px] font-medium transition-colors duration-200 ${
                  isActive
                    ? 'bg-primary/10 text-primary border border-primary/20'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                } ${collapsed ? 'justify-center' : ''}`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
            if (collapsed) {
              return (
                <Tooltip key={item.path}>
                  <TooltipTrigger asChild>{btn}</TooltipTrigger>
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              );
            }
            return btn;
          })}
        </nav>

        <div className="p-3 border-t border-border">
          {!collapsed && user && (
            <div className="mb-2 px-2 text-sm text-muted-foreground truncate">
              {user.prenume} {user.nume}
            </div>
          )}
          <Button
            variant="ghost"
            className={`w-full text-destructive hover:text-destructive hover:bg-destructive/10 text-[15px] ${collapsed ? 'px-0 justify-center' : 'justify-start'}`}
            onClick={handleLogout}
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            {!collapsed && <span className="ml-2">Deconectare</span>}
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
