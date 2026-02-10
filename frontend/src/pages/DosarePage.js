import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { useFirm } from '@/contexts/FirmContext';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, FolderKanban, ArrowUpRight, Calendar, Building2, Search } from 'lucide-react';

const STATUS_COLORS = {
  draft: 'bg-zinc-100 text-zinc-600 border-zinc-200', call_selected: 'bg-blue-50 text-blue-600 border-blue-200',
  guide_ready: 'bg-cyan-50 text-cyan-600 border-cyan-200', preeligibility: 'bg-violet-50 text-violet-600 border-violet-200',
  data_collection: 'bg-indigo-50 text-indigo-600 border-indigo-200', document_collection: 'bg-sky-50 text-sky-600 border-sky-200',
  writing: 'bg-amber-50 text-amber-600 border-amber-200', validation: 'bg-orange-50 text-orange-600 border-orange-200',
  ready_for_submission: 'bg-green-50 text-green-600 border-green-200', submitted: 'bg-emerald-50 text-emerald-600 border-emerald-200',
  contracting: 'bg-teal-50 text-teal-600 border-teal-200', implementation: 'bg-purple-50 text-purple-600 border-purple-200',
  monitoring: 'bg-pink-50 text-pink-600 border-pink-200',
};

export function DosarePage() {
  const { activeFirm } = useFirm();
  const [applications, setApplications] = useState([]);
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [selectedCall, setSelectedCall] = useState(null);
  const [title, setTitle] = useState('');
  const [creating, setCreating] = useState(false);
  const [searchQ, setSearchQ] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const params = activeFirm ? `?company_id=${activeFirm.id}` : '';
        const [aRes, cRes] = await Promise.all([
          api.get(`/v2/applications${params}`),
          api.get('/v2/calls?status=activ')
        ]);
        setApplications(aRes.data || []);
        setCalls(cRes.data || []);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, [activeFirm]);

  const handleCreate = async () => {
    if (!selectedCall || !title || !activeFirm) return;
    setCreating(true);
    try {
      await api.post('/v2/applications', { company_id: activeFirm.id, call_id: selectedCall.id, title });
      setOpen(false); setTitle(''); setSelectedCall(null);
      const res = await api.get(`/v2/applications?company_id=${activeFirm.id}`);
      setApplications(res.data || []);
    } catch (e) { console.error(e); }
    setCreating(false);
  };

  const filteredCalls = calls.filter(c => !searchQ || c.name.toLowerCase().includes(searchQ.toLowerCase()) || c.program_name?.toLowerCase().includes(searchQ.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="dosare-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight">Dosare</h1>
          <p className="text-muted-foreground mt-1">
            {activeFirm ? <><span className="text-primary font-medium">{activeFirm.denumire}</span> &middot; CUI: {activeFirm.cui}</> : 'Selectează o firmă'}
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button disabled={!activeFirm} data-testid="create-dosar-btn"><Plus className="w-4 h-4 mr-2" />Dosar nou</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Dosar nou – Selectează sesiunea</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <Input placeholder="Caută sesiune / program..." value={searchQ} onChange={(e) => setSearchQ(e.target.value)} data-testid="search-calls" />
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {filteredCalls.map(c => (
                  <div key={c.id} onClick={() => setSelectedCall(c)} className={`p-4 rounded-lg border cursor-pointer transition-all ${selectedCall?.id === c.id ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/30'}`} data-testid={`call-option-${c.id}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{c.name}</p>
                        <p className="text-sm text-muted-foreground">{c.program_name} &middot; {c.measure_code} &middot; {c.region}</p>
                      </div>
                      <Badge className="rounded-full text-xs bg-green-50 text-green-600 border-green-200">{c.status}</Badge>
                    </div>
                    <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                      <span><Calendar className="w-3 h-3 inline mr-1" />{c.start_date} → {c.end_date}</span>
                      <span>Buget: {c.budget?.toLocaleString()} RON</span>
                      <span>{c.value_min?.toLocaleString()} – {c.value_max?.toLocaleString()} RON</span>
                    </div>
                  </div>
                ))}
              </div>
              {selectedCall && (
                <div className="space-y-2 pt-2 border-t">
                  <p className="text-sm font-medium">Sesiune selectată: <span className="text-primary">{selectedCall.name}</span></p>
                  <Input placeholder="Titlu dosar (ex: Digitalizare firmă 2026)" value={title} onChange={(e) => setTitle(e.target.value)} data-testid="dosar-title-input" />
                  <Button className="w-full" onClick={handleCreate} disabled={creating || !title} data-testid="create-dosar-submit">
                    {creating ? 'Se creează...' : 'Creează dosarul'}
                  </Button>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {applications.length === 0 ? (
        <Card className="bg-card border-border"><CardContent className="p-14 text-center">
          <FolderKanban className="w-14 h-14 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">Niciun dosar</h3>
          <p className="text-base text-muted-foreground">Creează primul dosar selectând o sesiune de finanțare</p>
        </CardContent></Card>
      ) : (
        <div className="space-y-3">
          {applications.map(a => (
            <Link key={a.id} to={`/dosare/${a.id}`} data-testid={`dosar-item-${a.id}`}>
              <Card className="bg-card border-border hover:border-primary/30 transition-colors">
                <CardContent className="p-5 flex items-center justify-between">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-3">
                      <p className="font-semibold text-[15px]">{a.title}</p>
                      <Badge className={`rounded-full text-xs border ${STATUS_COLORS[a.status] || STATUS_COLORS.draft}`}>{a.status_label}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{a.company_name} &middot; {a.program_name} &middot; {a.call_name}</p>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
