import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard, Building2, FolderKanban, FileText, Shield,
  Users, Settings, LogOut, ChevronLeft, ChevronRight, Bot, Menu
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const navItems = [
  { path: '/dashboard', label: 'Panou', icon: LayoutDashboard },
  { path: '/organizations', label: 'Organizații', icon: Building2 },
  { path: '/projects', label: 'Proiecte', icon: FolderKanban },
  { path: '/documents', label: 'Documente', icon: FileText },
  { path: '/compliance', label: 'Conformitate', icon: Shield },
  { path: '/marketplace', label: 'Specialiști', icon: Users },
  { path: '/admin', label: 'Admin', icon: Settings },
];

export function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        data-testid="sidebar"
        className={`fixed left-0 top-0 h-screen bg-card/50 backdrop-blur-xl border-r border-border flex flex-col z-40 transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}
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

        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            const Icon = item.icon;
            const btn = (
              <Link
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.path.slice(1)}`}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors duration-200 ${
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
            <div className="mb-2 px-2 text-xs text-muted-foreground truncate">
              {user.prenume} {user.nume}
            </div>
          )}
          <Button
            variant="ghost"
            className={`w-full text-destructive hover:text-destructive hover:bg-destructive/10 ${collapsed ? 'px-0 justify-center' : 'justify-start'}`}
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
