import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { useFirm } from '@/contexts/FirmContext';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, FolderKanban, ArrowUpRight, Calendar, Bot, Loader2, Link2, X } from 'lucide-react';

const STATUS_COLORS = {
  draft:'bg-zinc-100 text-zinc-600', call_selected:'bg-blue-50 text-blue-600', guide_ready:'bg-cyan-50 text-cyan-600',
  preeligibility:'bg-violet-50 text-violet-600', data_collection:'bg-indigo-50 text-indigo-600', document_collection:'bg-sky-50 text-sky-600',
  writing:'bg-amber-50 text-amber-600', validation:'bg-orange-50 text-orange-600', ready_for_submission:'bg-green-50 text-green-600',
  submitted:'bg-emerald-50 text-emerald-600', contracting:'bg-teal-50 text-teal-600', implementation:'bg-purple-50 text-purple-600',
  monitoring:'bg-pink-50 text-pink-600',
};

export function DosarePage() {
  const { activeFirm } = useFirm();
  const [applications, setApplications] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [generatingDesc, setGeneratingDesc] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedProgram, setSelectedProgram] = useState('');
  const [selectedMeasure, setSelectedMeasure] = useState('');
  const [selectedCall, setSelectedCall] = useState('');
  const [useCustom, setUseCustom] = useState(false);
  const [customProgram, setCustomProgram] = useState('');
  const [customMeasure, setCustomMeasure] = useState('');
  const [customSession, setCustomSession] = useState('');
  const [customLinks, setCustomLinks] = useState([]);
  const [newLink, setNewLink] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const params = activeFirm ? `?company_id=${activeFirm.id}` : '';
        const [aRes, pRes] = await Promise.all([
          api.get(`/v2/applications${params}`),
          api.get('/v2/programs')
        ]);
        setApplications(aRes.data || []);
        setPrograms(pRes.data || []);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, [activeFirm]);

  const currentProgram = programs.find(p => p.id === selectedProgram);
  const currentMeasures = currentProgram?.measures || [];
  const currentMeasure = currentMeasures.find(m => m.id === selectedMeasure);
  const currentCalls = currentMeasure?.calls || [];
  const currentCall = currentCalls.find(c => c.id === selectedCall);

  const generateDescription = async () => {
    if (!title) return;
    setGeneratingDesc(true);
    try {
      const res = await api.post('/v2/applications/generate-description', {
        title, call_id: selectedCall || null, custom_session: customSession || null
      });
      setDescription(res.data.description || '');
    } catch (e) { console.error(e); }
    setGeneratingDesc(false);
  };

  const addLink = () => {
    if (!newLink.trim()) return;
    setCustomLinks([...customLinks, newLink.trim()]);
    setNewLink('');
  };

  const handleCreate = async () => {
    if (!title || !activeFirm) return;
    setCreating(true);
    try {
      const body = {
        company_id: activeFirm.id, title, description,
        call_id: useCustom ? null : (selectedCall || null),
        custom_program: useCustom ? customProgram : null,
        custom_measure: useCustom ? customMeasure : null,
        custom_session: useCustom ? customSession : null,
        custom_links: customLinks.length > 0 ? customLinks : []
      };
      await api.post('/v2/applications', body);
      setOpen(false);
      resetForm();
      const res = await api.get(`/v2/applications?company_id=${activeFirm.id}`);
      setApplications(res.data || []);
    } catch (e) { console.error(e); }
    setCreating(false);
  };

  const resetForm = () => {
    setTitle(''); setDescription(''); setSelectedProgram(''); setSelectedMeasure('');
    setSelectedCall(''); setUseCustom(false); setCustomProgram(''); setCustomMeasure('');
    setCustomSession(''); setCustomLinks([]); setNewLink('');
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="dosare-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight">Proiecte</h1>
          <p className="text-muted-foreground mt-1">
            {activeFirm ? <><span className="text-primary font-medium">{activeFirm.denumire}</span> &middot; CUI: {activeFirm.cui}</> : 'Selectează o firmă'}
          </p>
        </div>
        <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetForm(); }}>
          <DialogTrigger asChild>
            <Button disabled={!activeFirm} data-testid="create-project-btn"><Plus className="w-4 h-4 mr-2" />Creează proiect nou</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Creează proiect nou</DialogTitle></DialogHeader>
            <div className="space-y-5">
              {/* Title */}
              <div className="space-y-2">
                <Label className="text-[15px] font-semibold">Titlu proiect *</Label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="ex: Digitalizare IMM 2026" data-testid="project-title" />
              </div>

              {/* Program/Measure/Session selection */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-[15px] font-semibold">Program → Măsură → Sesiune</Label>
                  <Button variant="ghost" size="sm" onClick={() => setUseCustom(!useCustom)} data-testid="toggle-custom">
                    {useCustom ? 'Selectează din listă' : 'Nu găsesc în listă'}
                  </Button>
                </div>

                {!useCustom ? (
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Program</Label>
                      <Select value={selectedProgram} onValueChange={(v) => { setSelectedProgram(v); setSelectedMeasure(''); setSelectedCall(''); }}>
                        <SelectTrigger data-testid="sel-program"><SelectValue placeholder="Program" /></SelectTrigger>
                        <SelectContent>{programs.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Măsură</Label>
                      <Select value={selectedMeasure} onValueChange={(v) => { setSelectedMeasure(v); setSelectedCall(''); }} disabled={!selectedProgram}>
                        <SelectTrigger data-testid="sel-measure"><SelectValue placeholder="Măsură" /></SelectTrigger>
                        <SelectContent>{currentMeasures.map(m => <SelectItem key={m.id} value={m.id}>{m.code} – {m.name}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Sesiune</Label>
                      <Select value={selectedCall} onValueChange={setSelectedCall} disabled={!selectedMeasure}>
                        <SelectTrigger data-testid="sel-call"><SelectValue placeholder="Sesiune" /></SelectTrigger>
                        <SelectContent>{currentCalls.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3 p-4 rounded-lg bg-secondary/30 border border-border">
                    <p className="text-sm text-muted-foreground">Completează manual dacă sesiunea nu e în lista predefinită. Agentul Colector va extrage datele din link-urile furnizate.</p>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="space-y-1.5"><Label className="text-xs">Program</Label><Input value={customProgram} onChange={(e) => setCustomProgram(e.target.value)} placeholder="ex: PNRR" data-testid="custom-program" /></div>
                      <div className="space-y-1.5"><Label className="text-xs">Măsură</Label><Input value={customMeasure} onChange={(e) => setCustomMeasure(e.target.value)} placeholder="ex: C10-I1" data-testid="custom-measure" /></div>
                      <div className="space-y-1.5"><Label className="text-xs">Sesiune</Label><Input value={customSession} onChange={(e) => setCustomSession(e.target.value)} placeholder="ex: Apel 2026" data-testid="custom-session" /></div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs flex items-center gap-1"><Link2 className="w-3 h-3" />Link-uri sursă (ghid, apel, fonduri.eu)</Label>
                      <div className="flex gap-2">
                        <Input value={newLink} onChange={(e) => setNewLink(e.target.value)} placeholder="https://..." onKeyDown={(e) => e.key === 'Enter' && addLink()} data-testid="custom-link-input" />
                        <Button size="sm" variant="outline" onClick={addLink} disabled={!newLink.trim()}><Plus className="w-3 h-3" /></Button>
                      </div>
                      {customLinks.length > 0 && (
                        <div className="space-y-1">{customLinks.map((l, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm bg-white rounded px-2 py-1 border">
                            <Link2 className="w-3 h-3 text-primary flex-shrink-0" />
                            <span className="truncate flex-1">{l}</span>
                            <button onClick={() => setCustomLinks(customLinks.filter((_, j) => j !== i))}><X className="w-3 h-3 text-muted-foreground" /></button>
                          </div>
                        ))}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Session info */}
              {currentCall && (
                <Card className="bg-primary/5 border-primary/20"><CardContent className="p-4 grid grid-cols-3 gap-3 text-sm">
                  <div><p className="text-muted-foreground text-xs">Buget</p><p className="font-bold">{currentCall.budget?.toLocaleString()} RON</p></div>
                  <div><p className="text-muted-foreground text-xs">Valoare proiect</p><p className="font-medium">{currentCall.value_min?.toLocaleString()} – {currentCall.value_max?.toLocaleString()} RON</p></div>
                  <div><p className="text-muted-foreground text-xs">Perioadă</p><p className="font-medium">{currentCall.start_date} → {currentCall.end_date}</p></div>
                </CardContent></Card>
              )}

              {/* Description */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-[15px] font-semibold">Descriere proiect</Label>
                  <Button variant="ghost" size="sm" onClick={generateDescription} disabled={generatingDesc || !title} data-testid="gen-description-btn">
                    {generatingDesc ? <><Loader2 className="w-3 h-3 mr-1 animate-spin" />Se generează...</> : <><Bot className="w-3 h-3 mr-1" />Generează cu AI</>}
                  </Button>
                </div>
                <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="Descriere scurtă a proiectului..." data-testid="project-description" />
              </div>

              <Button className="w-full" onClick={handleCreate} disabled={creating || !title} data-testid="create-submit-btn">
                {creating ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se creează...</> : 'Creează proiectul'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {applications.length === 0 ? (
        <Card className="bg-card border-border"><CardContent className="p-14 text-center">
          <FolderKanban className="w-14 h-14 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">Niciun proiect</h3>
          <p className="text-base text-muted-foreground">Creează primul proiect selectând o sesiune de finanțare</p>
        </CardContent></Card>
      ) : (
        <div className="space-y-3">
          {applications.map(a => (
            <Link key={a.id} to={`/dosare/${a.id}`} data-testid={`project-item-${a.id}`}>
              <Card className="bg-card border-border hover:border-primary/30 transition-colors">
                <CardContent className="p-5 flex items-center justify-between">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-3">
                      <p className="font-semibold text-[15px]">{a.title}</p>
                      <Badge className={`rounded-full text-xs border ${STATUS_COLORS[a.status] || STATUS_COLORS.draft}`}>{a.status_label}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{a.company_name} &middot; {a.program_name} &middot; {a.call_name}</p>
                    {a.description && <p className="text-sm text-muted-foreground line-clamp-1">{a.description}</p>}
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
