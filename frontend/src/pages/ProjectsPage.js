import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Plus, FolderKanban, ArrowUpRight, Filter } from 'lucide-react';

const STATE_COLORS = {
  draft: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/20',
  pre_eligibil: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  blocat: 'bg-red-500/15 text-red-400 border-red-500/20',
  conform: 'bg-green-500/15 text-green-400 border-green-500/20',
  depus: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  aprobat: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  respins: 'bg-red-500/15 text-red-400 border-red-500/20',
  in_implementare: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
  suspendat: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
  finalizat: 'bg-teal-500/15 text-teal-400 border-teal-500/20',
  audit_post: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  arhivat: 'bg-zinc-500/15 text-zinc-500 border-zinc-500/20',
};

const PROGRAMS = ['PNRR', 'POIM', 'POC', 'POCA', 'AFIR', 'POR', 'Horizon Europe', 'Digital Europe', 'Altele'];

export function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ titlu: '', organizatie_id: '', program_finantare: '', descriere: '', buget_estimat: '' });
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [pRes, oRes] = await Promise.all([api.get('/projects'), api.get('/organizations')]);
      setProjects(pRes.data || []);
      setOrgs(oRes.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    setAdding(true);
    try {
      await api.post('/projects', {
        ...form,
        buget_estimat: parseFloat(form.buget_estimat) || 0
      });
      setForm({ titlu: '', organizatie_id: '', program_finantare: '', descriere: '', buget_estimat: '' });
      setOpen(false);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la creare');
    }
    setAdding(false);
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="projects-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight">Proiecte</h1>
          <p className="text-muted-foreground mt-1">Gestionează dosarele de finanțare</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="create-project-btn" disabled={orgs.length === 0}>
              <Plus className="w-4 h-4 mr-2" />Proiect nou
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader><DialogTitle>Crează proiect nou</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              {error && <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm">{error}</div>}
              <div className="space-y-2">
                <Label>Titlu proiect</Label>
                <Input value={form.titlu} onChange={(e) => setForm({ ...form, titlu: e.target.value })} required data-testid="project-title-input" />
              </div>
              <div className="space-y-2">
                <Label>Firmă</Label>
                <Select value={form.organizatie_id} onValueChange={(v) => setForm({ ...form, organizatie_id: v })}>
                  <SelectTrigger data-testid="project-org-select"><SelectValue placeholder="Selectează firma" /></SelectTrigger>
                  <SelectContent>{orgs.map((o) => <SelectItem key={o.id} value={o.id}>{o.denumire}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Program de finanțare</Label>
                <Select value={form.program_finantare} onValueChange={(v) => setForm({ ...form, program_finantare: v })}>
                  <SelectTrigger data-testid="project-program-select"><SelectValue placeholder="Selectează programul" /></SelectTrigger>
                  <SelectContent>{PROGRAMS.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Buget estimat (RON)</Label>
                <Input type="number" value={form.buget_estimat} onChange={(e) => setForm({ ...form, buget_estimat: e.target.value })} data-testid="project-budget-input" />
              </div>
              <div className="space-y-2">
                <Label>Descriere</Label>
                <Textarea value={form.descriere} onChange={(e) => setForm({ ...form, descriere: e.target.value })} rows={3} data-testid="project-desc-input" />
              </div>
              <Button type="submit" className="w-full" disabled={adding} data-testid="project-submit-btn">
                {adding ? 'Se creează...' : 'Creează proiect'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {projects.length === 0 ? (
        <Card className="bg-card border-border">
          <CardContent className="p-12 text-center">
            <FolderKanban className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Niciun proiect</h3>
            <p className="text-muted-foreground">{orgs.length === 0 ? 'Adaugă mai întâi o organizație' : 'Creează primul proiect de finanțare'}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {projects.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`} data-testid={`project-item-${p.id}`}>
              <Card className="bg-card border-border hover:border-primary/30 transition-colors duration-200">
                <CardContent className="p-5 flex items-center justify-between">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-3">
                      <p className="font-medium">{p.titlu}</p>
                      <Badge className={`rounded-full px-2.5 py-0.5 text-xs font-medium border ${STATE_COLORS[p.stare] || STATE_COLORS.draft}`}>
                        {p.stare_label}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{p.organizatie_denumire}</span>
                      <span>{p.program_finantare}</span>
                      {p.buget_estimat > 0 && <span>{p.buget_estimat?.toLocaleString()} RON</span>}
                    </div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
