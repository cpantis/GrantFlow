import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { AiMessage } from '@/components/shared/AiMessage';
import {
  ArrowLeft, FileText, Upload, Search, Settings, BookOpen,
  FolderOpen, Bot, Shield, MapPin, ShoppingCart, Plus, Loader2, CheckCircle, Package
} from 'lucide-react';

export function ProjectWritingPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [projectTypes, setProjectTypes] = useState([]);
  const [legislation, setLegislation] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [sicapResults, setSicapResults] = useState([]);
  const [afirResults, setAfirResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [generating, setGenerating] = useState(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalReport, setEvalReport] = useState(null);

  // Config form
  const [config, setConfig] = useState({ tip_proiect: '', locatie_implementare: '', judet_implementare: '', tema_proiect: '' });
  const [selectedProgram, setSelectedProgram] = useState('');
  const [selectedMasura, setSelectedMasura] = useState('');
  const [selectedSesiune, setSelectedSesiune] = useState('');
  const [achizitii, setAchizitii] = useState([]);
  const [newAchizitie, setNewAchizitie] = useState({ descriere: '', cpv: '', cantitate: 1, pret_unitar: 0 });

  useEffect(() => {
    const load = async () => {
      try {
        const [pRes, progsRes, templRes, typesRes, legRes, draftsRes] = await Promise.all([
          api.get(`/projects/${id}`),
          api.get('/v2/programs'),
          api.get('/v2/templates'),
          api.get('/v2/calls').then(r => ({data: []})).catch(() => ({ data: [] })),
          api.get(`/v2/applications/${id}`).then(r => ({data: r.data?.guide_assets || []})).catch(() => ({ data: [] })),
          api.get(`/v2/applications/${id}/drafts`).catch(() => ({ data: [] })),
        ]);
        setProject(pRes.data);
        setPrograms(progsRes.data || []);
        setTemplates(templRes.data || []);
        setProjectTypes(typesRes.data || []);
        setLegislation(legRes.data || []);
        setDrafts(draftsRes.data || []);
        if (pRes.data?.tip_proiect) setConfig(c => ({ ...c, tip_proiect: pRes.data.tip_proiect }));
        if (pRes.data?.locatie_implementare) setConfig(c => ({ ...c, locatie_implementare: pRes.data.locatie_implementare }));
        if (pRes.data?.tema_proiect) setConfig(c => ({ ...c, tema_proiect: pRes.data.tema_proiect }));
        if (pRes.data?.achizitii) setAchizitii(pRes.data.achizitii);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, [id]);

  const saveConfig = async () => {
    const body = { project_id: id, ...config };
    if (selectedSesiune) body.sesiune_id = selectedSesiune;
    if (achizitii.length > 0) body.achizitii = achizitii;
    try {
      const res = await api.put(`/v2/applications/${id}`, body);
      setProject(res.data);
    } catch (e) { console.error(e); }
  };

  const searchSicap = async () => {
    if (searchQuery.length < 2) return;
    try {
      const [s, a] = await Promise.all([
        api.get(`/v2/sicap/search?q=${encodeURIComponent(searchQuery)}`),
        api.get(`/v2/afir/preturi?q=${encodeURIComponent(searchQuery)}`)
      ]);
      setSicapResults(s.data || []);
      setAfirResults(a.data || []);
    } catch (e) { console.error(e); }
  };

  const addAchizitie = (item) => {
    const a = { id: Date.now().toString(), descriere: item?.descriere || newAchizitie.descriere, cpv: item?.cod || newAchizitie.cpv, cantitate: newAchizitie.cantitate || 1, pret_unitar: item?.pret_referinta_min || newAchizitie.pret_unitar, total: (newAchizitie.cantitate || 1) * (item?.pret_referinta_min || newAchizitie.pret_unitar) };
    setAchizitii([...achizitii, a]);
    setNewAchizitie({ descriere: '', cpv: '', cantitate: 1, pret_unitar: 0 });
  };

  const generateDraft = async (templateId) => {
    setGenerating(templateId);
    try {
      const res = await api.post(`/v2/applications/${id}/drafts/generate`, { template_id: templateId });
      setDrafts([...drafts, res.data]);
    } catch (e) { console.error(e); }
    setGenerating(null);
  };

  const evaluateConformity = async () => {
    setEvaluating(true);
    try {
      const res = await api.post(`/v2/applications/${id}/evaluate`);
      setEvalReport(res.data);
    } catch (e) { console.error(e); }
    setEvaluating(false);
  };

  const currentProgram = programs.find(p => p.id === selectedProgram);
  const currentMasuri = currentProgram?.masuri || [];
  const currentMasura = currentMasuri.find(m => m.id === selectedMasura);
  const currentSesiuni = currentMasura?.sesiuni || [];

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;
  if (!project) return <div className="text-center text-muted-foreground">Proiectul nu a fost găsit</div>;

  return (
    <div data-testid="project-writing-page" className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to={`/projects/${id}`}><Button variant="ghost" size="icon"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div>
          <h1 className="font-heading text-2xl font-bold tracking-tight">Scriere proiect: {project.titlu}</h1>
          <p className="text-muted-foreground">{project.organizatie_denumire}</p>
        </div>
      </div>

      <Tabs defaultValue="program" className="space-y-4">
        <TabsList className="bg-muted flex-wrap h-auto py-1">
          <TabsTrigger value="program" data-testid="tab-program"><FolderOpen className="w-4 h-4 mr-1" />Program</TabsTrigger>
          <TabsTrigger value="config" data-testid="tab-config"><Settings className="w-4 h-4 mr-1" />Configurare</TabsTrigger>
          <TabsTrigger value="legislation" data-testid="tab-legislation"><BookOpen className="w-4 h-4 mr-1" />Legislație</TabsTrigger>
          <TabsTrigger value="achizitii" data-testid="tab-achizitii"><ShoppingCart className="w-4 h-4 mr-1" />Achiziții</TabsTrigger>
          <TabsTrigger value="drafturi" data-testid="tab-drafturi"><FileText className="w-4 h-4 mr-1" />Drafturi</TabsTrigger>
          <TabsTrigger value="evaluare" data-testid="tab-evaluare"><Shield className="w-4 h-4 mr-1" />Evaluare</TabsTrigger>
        </TabsList>

        {/* PROGRAM SELECTION */}
        <TabsContent value="program" className="space-y-4">
          <h2 className="font-heading text-lg font-bold">Selectare Program → Măsură → Sesiune</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Program de finanțare</Label>
              <Select value={selectedProgram} onValueChange={(v) => { setSelectedProgram(v); setSelectedMasura(''); setSelectedSesiune(''); }}>
                <SelectTrigger data-testid="select-program"><SelectValue placeholder="Selectează programul" /></SelectTrigger>
                <SelectContent>{programs.map(p => <SelectItem key={p.id} value={p.id}>{p.denumire}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Măsură</Label>
              <Select value={selectedMasura} onValueChange={(v) => { setSelectedMasura(v); setSelectedSesiune(''); }} disabled={!selectedProgram}>
                <SelectTrigger data-testid="select-masura"><SelectValue placeholder="Selectează măsura" /></SelectTrigger>
                <SelectContent>{currentMasuri.map(m => <SelectItem key={m.id} value={m.id}>{m.cod} - {m.denumire}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Sesiune</Label>
              <Select value={selectedSesiune} onValueChange={setSelectedSesiune} disabled={!selectedMasura}>
                <SelectTrigger data-testid="select-sesiune"><SelectValue placeholder="Selectează sesiunea" /></SelectTrigger>
                <SelectContent>{currentSesiuni.map(s => <SelectItem key={s.id} value={s.id}>{s.denumire} ({s.status})</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          {selectedSesiune && (() => {
            const ses = currentSesiuni.find(s => s.id === selectedSesiune);
            return ses ? (
              <Card className="bg-card border-border"><CardContent className="p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div><p className="text-sm text-muted-foreground">Buget disponibil</p><p className="font-bold text-lg">{ses.buget_disponibil?.toLocaleString()} RON</p></div>
                <div><p className="text-sm text-muted-foreground">Valoare min-max</p><p className="font-bold">{ses.valoare_min?.toLocaleString()} - {ses.valoare_max?.toLocaleString()} RON</p></div>
                <div><p className="text-sm text-muted-foreground">Perioadă</p><p className="font-medium">{ses.data_start} → {ses.data_sfarsit}</p></div>
                <div><p className="text-sm text-muted-foreground">Beneficiari</p><div className="flex flex-wrap gap-1 mt-1">{ses.tip_beneficiari?.map((b, i) => <Badge key={i} variant="secondary" className="text-xs">{b}</Badge>)}</div></div>
              </CardContent></Card>
            ) : null;
          })()}
          <Button onClick={saveConfig} data-testid="save-program-btn">Salvează selecția</Button>
        </TabsContent>

        {/* CONFIG */}
        <TabsContent value="config" className="space-y-4">
          <h2 className="font-heading text-lg font-bold">Configurare proiect</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Tip proiect</Label>
              <Select value={config.tip_proiect} onValueChange={(v) => setConfig({ ...config, tip_proiect: v })}>
                <SelectTrigger data-testid="select-tip-proiect"><SelectValue placeholder="Selectează tipul" /></SelectTrigger>
                <SelectContent>{projectTypes.map(t => <SelectItem key={t.id} value={t.id}>{t.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Județ implementare</Label>
              <Input value={config.judet_implementare} onChange={(e) => setConfig({ ...config, judet_implementare: e.target.value })} placeholder="ex: București" data-testid="input-judet" />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Locație implementare (adresă)</Label>
              <Input value={config.locatie_implementare} onChange={(e) => setConfig({ ...config, locatie_implementare: e.target.value })} placeholder="Adresa completă" data-testid="input-locatie" />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Tema proiectului (descriere)</Label>
              <Textarea value={config.tema_proiect} onChange={(e) => setConfig({ ...config, tema_proiect: e.target.value })} rows={4} placeholder="Descrieți tema și obiectivele proiectului..." data-testid="input-tema" />
            </div>
          </div>
          <Button onClick={saveConfig} data-testid="save-config-btn">Salvează configurarea</Button>
        </TabsContent>

        {/* LEGISLATION */}
        <TabsContent value="legislation" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-lg font-bold">Legislație & Ghiduri</h2>
          </div>
          <Card className="bg-card border-border"><CardContent className="p-5 space-y-3">
            <p className="text-sm text-muted-foreground">Încarcă ghidul solicitantului și procedura de evaluare pentru sesiunea selectată.</p>
            <input type="file" id="leg-file" className="hidden" onChange={async (e) => {
              if (!e.target.files[0]) return;
              const fd = new FormData();
              fd.append('file', e.target.files[0]);
              fd.append('project_id', id);
              fd.append('titlu', e.target.files[0].name);
              fd.append('tip', 'ghid');
              try {
                const res = await api.post(`/v2/applications/${id}/guide`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
                setLegislation([...legislation, res.data]);
              } catch (err) { console.error(err); }
            }} />
            <Button variant="outline" onClick={() => document.getElementById('leg-file').click()} data-testid="upload-legislation-btn">
              <Upload className="w-4 h-4 mr-2" />Încarcă document legislativ
            </Button>
          </CardContent></Card>
          {legislation.length > 0 && (
            <div className="space-y-2">
              {legislation.map(l => (
                <Card key={l.id} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BookOpen className="w-5 h-5 text-primary" />
                    <div><p className="font-medium">{l.titlu || l.filename}</p><p className="text-sm text-muted-foreground">{l.tip}</p></div>
                  </div>
                  <Badge variant="secondary">{l.tip}</Badge>
                </CardContent></Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ACHIZITII / PROCUREMENT SEARCH */}
        <TabsContent value="achizitii" className="space-y-4">
          <h2 className="font-heading text-lg font-bold">Achiziții proiect (SICAP / AFIR)</h2>
          <Card className="bg-card border-border"><CardContent className="p-5 space-y-4">
            <div className="flex gap-2">
              <Input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Caută echipamente, servicii, materiale..." className="flex-1" onKeyDown={(e) => e.key === 'Enter' && searchSicap()} data-testid="search-achizitii" />
              <Button onClick={searchSicap} data-testid="search-btn"><Search className="w-4 h-4 mr-2" />Caută</Button>
            </div>

            {sicapResults.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Rezultate SICAP (coduri CPV):</p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {sicapResults.map((r, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{r.descriere}</p>
                        <p className="text-xs text-muted-foreground">CPV: {r.cod} &middot; Preț ref: {r.pret_referinta_min?.toLocaleString()} - {r.pret_referinta_max?.toLocaleString()} RON</p>
                      </div>
                      <Button size="sm" variant="outline" onClick={() => addAchizitie(r)} data-testid={`add-sicap-${i}`}><Plus className="w-3 h-3" /></Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {afirResults.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Prețuri referință AFIR:</p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {afirResults.map((r, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{r.subcategorie}</p>
                        <p className="text-xs text-muted-foreground">{r.categorie} &middot; {r.pret_min?.toLocaleString()} - {r.pret_max?.toLocaleString()} RON/{r.unitate}</p>
                      </div>
                      <Button size="sm" variant="outline" onClick={() => addAchizitie({ descriere: r.subcategorie, cod: '', pret_referinta_min: r.pret_min })} data-testid={`add-afir-${i}`}><Plus className="w-3 h-3" /></Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent></Card>

          <h3 className="font-heading text-base font-bold">Lista achiziții proiect</h3>
          {achizitii.length === 0 ? (
            <p className="text-muted-foreground text-sm">Nicio achiziție adăugată. Căutați în bazele SICAP/AFIR.</p>
          ) : (
            <div className="space-y-2">
              {achizitii.map((a, i) => (
                <Card key={a.id || i} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium">{a.descriere}</p>
                    <p className="text-sm text-muted-foreground">{a.cpv && `CPV: ${a.cpv} · `}{a.cantitate} buc × {a.pret_unitar?.toLocaleString()} RON</p>
                  </div>
                  <p className="font-bold">{(a.cantitate * a.pret_unitar)?.toLocaleString()} RON</p>
                </CardContent></Card>
              ))}
              <Card className="bg-primary/5 border-primary/20"><CardContent className="p-4 flex items-center justify-between">
                <p className="font-bold">Total achiziții</p>
                <p className="font-bold text-lg text-primary">{achizitii.reduce((s, a) => s + (a.cantitate * a.pret_unitar), 0)?.toLocaleString()} RON</p>
              </CardContent></Card>
            </div>
          )}
          <Button onClick={saveConfig} data-testid="save-achizitii-btn">Salvează achizițiile</Button>
        </TabsContent>

        {/* DRAFT GENERATION */}
        <TabsContent value="drafturi" className="space-y-4">
          <h2 className="font-heading text-lg font-bold">Generare documente draft</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map(t => (
              <Card key={t.id} className="bg-card border-border hover:border-primary/30 transition-colors" data-testid={`template-${t.id}`}>
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    <p className="font-semibold">{t.label}</p>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {t.sectiuni.slice(0, 3).map((s, i) => <Badge key={i} variant="secondary" className="text-xs">{s}</Badge>)}
                    {t.sectiuni.length > 3 && <Badge variant="secondary" className="text-xs">+{t.sectiuni.length - 3}</Badge>}
                  </div>
                  <Button size="sm" className="w-full" onClick={() => generateDraft(t.id)} disabled={generating === t.id} data-testid={`gen-${t.id}`}>
                    {generating === t.id ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se generează...</> : <><Bot className="w-4 h-4 mr-2" />Generează draft</>}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {drafts.length > 0 && (
            <>
              <h3 className="font-heading text-base font-bold mt-6">Drafturi generate</h3>
              <div className="space-y-3">
                {drafts.map(d => (
                  <Card key={d.id} className="bg-card border-border" data-testid={`draft-${d.id}`}>
                    <CardHeader><CardTitle className="text-base flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary" />{d.template_label}
                      <Badge variant="secondary" className="text-xs ml-auto">v{d.versiune}</Badge>
                    </CardTitle></CardHeader>
                    <CardContent className="max-h-64 overflow-y-auto">
                      <AiMessage text={d.continut} />
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>

        {/* CONFORMITY EVALUATION */}
        <TabsContent value="evaluare" className="space-y-4">
          <h2 className="font-heading text-lg font-bold flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />Evaluare grilă conformitate
          </h2>
          <Card className="bg-card border-border"><CardContent className="p-5 space-y-3">
            <p className="text-muted-foreground">Agentul AI va verifica dosarul complet conform grilei de conformitate: documente obligatorii, coerență date, buget vs achiziții, respectarea ghidului.</p>
            <Button onClick={evaluateConformity} disabled={evaluating} data-testid="evaluate-conformity-btn">
              {evaluating ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se evaluează...</> : <><Shield className="w-4 h-4 mr-2" />Evaluare conformitate</>}
            </Button>
          </CardContent></Card>
          {evalReport && (
            <Card className="bg-card border-border">
              <CardHeader><CardTitle className="text-base flex items-center gap-2">
                <Bot className="w-4 h-4 text-primary" />Raport evaluare conformitate
              </CardTitle></CardHeader>
              <CardContent><AiMessage text={evalReport.result} /></CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
