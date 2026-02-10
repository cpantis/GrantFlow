import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useFirm } from '@/contexts/FirmContext';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Building2, FolderKanban, FileText, Users, ArrowUpRight, Clock, TrendingUp, AlertTriangle, Mail, CheckCircle, Bot, Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AiMessage } from '@/components/shared/AiMessage';

const STATE_COLORS = {
  draft: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/20',
  pre_eligibil: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  blocat: 'bg-red-500/15 text-red-400 border-red-500/20',
  conform: 'bg-green-500/15 text-green-400 border-green-500/20',
  depus: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  aprobat: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  in_implementare: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
};

export function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [projects, setProjects] = useState([]);
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const { activeFirm } = useFirm();

  useEffect(() => {
    const load = async () => {
      try {
        const params = activeFirm ? `?organizatie_id=${activeFirm.id}` : '';
        const [pRes, oRes, aRes] = await Promise.all([
          api.get(`/projects${params}`),
          api.get('/organizations'),
          api.get('/admin/dashboard').catch(() => ({ data: null }))
        ]);
        setProjects(pRes.data || []);
        setOrgs(oRes.data || []);
        if (aRes.data) setStats(aRes.data.stats);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, [activeFirm]);

  const byState = projects.reduce((acc, p) => { acc[p.stare] = (acc[p.stare] || 0) + 1; return acc; }, {});

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  const resendVerification = async () => {
    try {
      await api.post('/auth/resend-verification');
    } catch (e) { console.error(e); }
  };

  return (
    <div data-testid="dashboard-page" className="space-y-8">
      {user && false && !user.email_verified && (
        <div className="p-4 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-between" data-testid="verify-email-banner">
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-amber-400" />
            <span className="text-sm">Verificați adresa de email pentru a activa complet contul.</span>
          </div>
          <Button variant="outline" size="sm" onClick={resendVerification} data-testid="resend-verification-btn">
            Retrimite email
          </Button>
        </div>
      )}
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Bun venit, {user?.prenume}</h1>
        <p className="text-muted-foreground mt-1">
          {activeFirm ? <><span className="text-primary font-medium">{activeFirm.denumire}</span> &middot; Panou de control</> : 'Panou de control GrantFlow'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border-border hover:border-primary/50 transition-colors duration-300">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <Building2 className="w-6 h-6 text-primary" />
            </div>
            <div>
              <p className="text-base text-muted-foreground">Firme</p>
              <p className="text-3xl font-bold" data-testid="stat-orgs">{orgs.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border hover:border-primary/50 transition-colors duration-300">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <FolderKanban className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <p className="text-base text-muted-foreground">Proiecte</p>
              <p className="text-3xl font-bold" data-testid="stat-projects">{projects.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border hover:border-primary/50 transition-colors duration-300">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <p className="text-base text-muted-foreground">Conforme</p>
              <p className="text-3xl font-bold" data-testid="stat-conform">{byState.conform || 0}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border hover:border-primary/50 transition-colors duration-300">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-red-500/10 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <p className="text-base text-muted-foreground">Blocate</p>
              <p className="text-3xl font-bold" data-testid="stat-blocked">{byState.blocat || 0}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl font-bold">Proiecte recente</h2>
            <Link to="/projects" className="text-sm text-primary hover:underline flex items-center gap-1" data-testid="view-all-projects">
              Vezi toate <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          {projects.length === 0 ? (
            <Card className="bg-card border-border"><CardContent className="p-10 text-center text-muted-foreground">
              Niciun proiect încă. <Link to="/projects" className="text-primary hover:underline font-medium">Creează primul proiect</Link>
            </CardContent></Card>
          ) : (
            <div className="space-y-3">
              {projects.slice(0, 5).map((p) => (
                <Link key={p.id} to={`/projects/${p.id}`} data-testid={`project-card-${p.id}`}>
                  <Card className="bg-card border-border hover:border-primary/30 transition-colors duration-200">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div className="space-y-1">
                        <p className="font-semibold text-[15px]">{p.titlu}</p>
                        <p className="text-sm text-muted-foreground">{p.organizatie_denumire} &middot; {p.program_finantare}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={`rounded-full px-2.5 py-0.5 text-xs font-medium border ${STATE_COLORS[p.stare] || STATE_COLORS.draft}`}>
                          {p.stare_label}
                        </Badge>
                        <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <h2 className="font-heading text-xl font-bold">Firme</h2>
          {orgs.length === 0 ? (
            <Card className="bg-card border-border"><CardContent className="p-6 text-center text-muted-foreground">
              <Link to="/organizations" className="text-primary hover:underline">Adaugă prima firmă</Link>
            </CardContent></Card>
          ) : (
            <div className="space-y-3">
              {orgs.slice(0, 5).map((o) => (
                <Link key={o.id} to={`/organizations/${o.id}`} data-testid={`org-card-${o.id}`}>
                  <Card className="bg-card border-border hover:border-primary/30 transition-colors duration-200">
                    <CardContent className="p-4">
                      <p className="font-medium text-sm">{o.denumire}</p>
                      <p className="text-xs text-muted-foreground mt-1">CUI: {o.cui} &middot; {o.judet}</p>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
