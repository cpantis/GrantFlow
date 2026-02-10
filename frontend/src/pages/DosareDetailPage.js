import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AiMessage } from '@/components/shared/AiMessage';
import {
  ArrowLeft, ArrowRight, Upload, FileText, Shield, Bot, CheckCircle, XCircle,
  FolderOpen, BookOpen, PenTool, Zap, Download, Loader2, Plus, AlertTriangle, Package,
  Settings, ShoppingCart, MapPin, Search, Send, X
} from 'lucide-react';

const STATES = ["draft","call_selected","guide_ready","preeligibility","data_collection","document_collection","writing","validation","ready_for_submission","submitted","contracting","implementation","monitoring"];
const STATE_LABELS = {draft:"Ciornă",call_selected:"Sesiune aleasă",guide_ready:"Ghid disponibil",preeligibility:"Pre-eligibilitate",data_collection:"Colectare date",document_collection:"Colectare documente",writing:"Redactare",validation:"Validare",ready_for_submission:"Pregătit depunere",submitted:"Depus",contracting:"Contractare",implementation:"Implementare",monitoring:"Monitorizare"};
const TRANSITIONS = {draft:["call_selected"],call_selected:["guide_ready","draft"],guide_ready:["preeligibility","call_selected"],preeligibility:["data_collection","guide_ready"],data_collection:["document_collection","preeligibility"],document_collection:["writing","data_collection"],writing:["validation","document_collection"],validation:["ready_for_submission","writing"],ready_for_submission:["submitted","validation"],submitted:["contracting"],contracting:["implementation"],implementation:["monitoring"],monitoring:[]};

export function DosareDetailPage() {
  const { id } = useParams();
  const [app, setApp] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState(false);
  const [generating, setGenerating] = useState(null);
  const [validating, setValidating] = useState(false);
  const [validationReport, setValidationReport] = useState(null);
  const [newReqDoc, setNewReqDoc] = useState({ official_name: '', folder_group: 'depunere', required: true });
  const [orchestratorReport, setOrchestratorReport] = useState(null);
  const [orchestratorLoading, setOrchestratorLoading] = useState(false);
  const [config, setConfig] = useState({ tip_proiect: '', locatie: '', judet: '', tema: '' });
  const [achizitiiSearch, setAchizitiiSearch] = useState('');
  const [sicapResults, setSicapResults] = useState([]);
  const [afirResults, setAfirResults] = useState([]);
  const [achizitii, setAchizitii] = useState([]);
  const [preeligReport, setPreeligReport] = useState(null);
  const [preeligLoading, setPreeligLoading] = useState(false);
  const [customTemplate, setCustomTemplate] = useState({ label: '', sections: '' });
  const [chatMsg, setChatMsg] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  const load = async () => {
    try {
      const [aRes, tRes] = await Promise.all([api.get(`/v2/applications/${id}`), api.get('/v2/templates')]);
      const a = aRes.data;
      setApp(a);
      setTemplates(tRes.data || []);
      // Init config from app data
      if (a) {
        setConfig({ tip_proiect: a.tip_proiect || '', locatie: a.locatie_implementare || '', judet: a.judet_implementare || '', tema: a.tema_proiect || '', buget: a.budget_estimated || '' });
        setAchizitii(a.achizitii || []);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };
  useEffect(() => { load(); }, [id]);

  const transition = async (newState) => {
    setTransitioning(true);
    try { await api.post(`/v2/applications/${id}/transition`, { new_state: newState }); load(); } catch (e) { console.error(e); }
    setTransitioning(false);
  };

  const [guideProcessing, setGuideProcessing] = useState(false);
  const [guideActions, setGuideActions] = useState([]);

  const uploadGuide = async (e) => {
    if (!e.target.files[0]) return;
    setGuideProcessing(true);
    setGuideActions([]);
    const fd = new FormData(); fd.append('file', e.target.files[0]); fd.append('tip', 'ghid');
    try {
      const res = await api.post(`/v2/applications/${id}/guide`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setGuideActions(res.data.agent_actions || []);
      load();
    } catch (err) { console.error(err); }
    setGuideProcessing(false);
  };

  const addRequiredDoc = async () => {
    if (!newReqDoc.official_name) return;
    try { await api.post(`/v2/applications/${id}/required-docs`, newReqDoc); setNewReqDoc({ official_name: '', folder_group: 'depunere', required: true }); load(); } catch (e) { console.error(e); }
  };

  const proposeRequiredDocs = async () => {
    try { const res = await api.post(`/v2/applications/${id}/required-docs/propose`); setValidationReport({ result: res.data.proposed_text, type: 'proposed_docs' }); } catch (e) { console.error(e); }
  };

  const freezeChecklist = async () => {
    try { await api.post(`/v2/applications/${id}/required-docs/freeze`); load(); } catch (e) { console.error(e); }
  };

  const uploadDocument = async (e, folder) => {
    if (!e.target.files[0]) return;
    const fd = new FormData(); fd.append('file', e.target.files[0]); fd.append('folder_group', folder);
    try { await api.post(`/v2/applications/${id}/documents`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }); load(); } catch (err) { console.error(err); }
  };

  const generateDraft = async (templateId) => {
    setGenerating(templateId);
    try { await api.post(`/v2/applications/${id}/drafts/generate`, { template_id: templateId }); load(); } catch (e) { console.error(e); }
    setGenerating(null);
  };

  const validate = async () => {
    setValidating(true);
    try { const res = await api.post(`/v2/applications/${id}/validate`); setValidationReport(res.data); } catch (e) { console.error(e); }
    setValidating(false);
  };

  const runOrchestrator = async () => {
    setOrchestratorLoading(true);
    try { const res = await api.post(`/v2/applications/${id}/orchestrator`); setOrchestratorReport(res.data); } catch (e) { console.error(e); }
    setOrchestratorLoading(false);
  };

  const saveConfig = async () => {
    try {
      await api.put(`/v2/applications/${id}`, {
        tip_proiect: config.tip_proiect,
        locatie_implementare: config.locatie,
        judet_implementare: config.judet,
        tema_proiect: config.tema,
        budget_estimated: parseFloat(config.buget) || 0,
        achizitii
      });
      load();
    } catch (e) { console.error(e); }
  };

  const searchAchizitii = async () => {
    if (achizitiiSearch.length < 2) return;
    try {
      const [s, a] = await Promise.all([
        api.get(`/v2/sicap/search?q=${encodeURIComponent(achizitiiSearch)}`),
        api.get(`/v2/afir/preturi?q=${encodeURIComponent(achizitiiSearch)}`)
      ]);
      setSicapResults(s.data || []);
      setAfirResults(a.data || []);
    } catch (e) { console.error(e); }
  };

  const addAchizitie = (item) => {
    setAchizitii([...achizitii, { id: Date.now().toString(), descriere: item.descriere || item.subcategorie, cpv: item.cod || '', cantitate: 1, pret_unitar: item.pret_referinta_min || item.pret_min || 0 }]);
  };

  const runPreeligibility = async () => {
    setPreeligLoading(true);
    try { const res = await api.post(`/v2/applications/${id}/evaluate`); setPreeligReport(res.data); } catch (e) { console.error(e); }
    setPreeligLoading(false);
  };

  const sendChat = async () => {
    if (!chatMsg.trim()) return;
    const msg = chatMsg;
    setChatHistory([...chatHistory, { role: 'user', text: msg }]);
    setChatMsg('');
    setChatLoading(true);
    try {
      const res = await api.post('/compliance/navigator', { message: msg, project_id: null });
      setChatHistory(h => [...h, { role: 'assistant', text: res.data.response }]);
    } catch (e) { setChatHistory(h => [...h, { role: 'assistant', text: 'Eroare.' }]); }
    setChatLoading(false);
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;
  if (!app) return <div className="text-muted-foreground text-center">Dosarul nu a fost găsit</div>;

  const possibleNext = TRANSITIONS[app.status] || [];
  const stateIndex = STATES.indexOf(app.status);
  const reqDocs = app.required_documents || [];
  const docs = app.documents || [];
  const drafts = app.drafts || [];
  const folders = app.folder_groups || [];

  return (
    <div data-testid="dosar-detail-page" className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/dosare"><Button variant="ghost" size="icon"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-bold">{app.title}</h1>
            <Badge className="rounded-full text-sm">{app.status_label}</Badge>
          </div>
          <p className="text-muted-foreground text-sm">{app.company_name} &middot; {app.program_name} &middot; {app.call_name}</p>
        </div>
        <a href={`${process.env.REACT_APP_BACKEND_URL}/api/v2/applications/${id}/export`} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" data-testid="export-zip-btn"><Download className="w-4 h-4 mr-2" />Export ZIP</Button>
        </a>
      </div>

      {/* Progress bar */}
      <Card className="bg-card border-border"><CardContent className="p-3">
        <div className="flex items-center gap-0.5 overflow-x-auto">
          {STATES.map((s, i) => (
            <div key={s} className="flex items-center">
              <div className={`px-2.5 py-1.5 rounded-md text-xs font-medium whitespace-nowrap ${i === stateIndex ? 'bg-primary text-white shadow-md' : i < stateIndex ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>{STATE_LABELS[s]}</div>
              {i < STATES.length - 1 && <ArrowRight className="w-3 h-3 text-muted-foreground mx-0.5 flex-shrink-0" />}
            </div>
          ))}
        </div>
      </CardContent></Card>

      {possibleNext.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-muted-foreground">Pasul următor:</span>
          {possibleNext.map(s => (
            <Button key={s} size="sm" onClick={() => transition(s)} disabled={transitioning} data-testid={`transition-${s}`}>
              <ArrowRight className="w-3 h-3 mr-1" />{STATE_LABELS[s]}
            </Button>
          ))}
        </div>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="bg-muted flex-wrap h-auto py-1">
          <TabsTrigger value="overview">Sumar</TabsTrigger>
          <TabsTrigger value="orchestrator"><Zap className="w-4 h-4 mr-1" />Orchestrator</TabsTrigger>
          <TabsTrigger value="guide"><BookOpen className="w-4 h-4 mr-1" />Legislație</TabsTrigger>
          <TabsTrigger value="config"><Settings className="w-4 h-4 mr-1" />Configurare</TabsTrigger>
          <TabsTrigger value="preeligibility"><Shield className="w-4 h-4 mr-1" />Pre-eligibilitate</TabsTrigger>
          <TabsTrigger value="achizitii"><ShoppingCart className="w-4 h-4 mr-1" />Achiziții</TabsTrigger>
          <TabsTrigger value="checklist"><CheckCircle className="w-4 h-4 mr-1" />Checklist</TabsTrigger>
          <TabsTrigger value="documents"><FolderOpen className="w-4 h-4 mr-1" />Documente</TabsTrigger>
          <TabsTrigger value="drafts"><PenTool className="w-4 h-4 mr-1" />Drafturi</TabsTrigger>
          <TabsTrigger value="validation"><Shield className="w-4 h-4 mr-1" />Evaluare</TabsTrigger>
          <TabsTrigger value="history">Istoric</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Program</p><p className="font-bold mt-1">{app.program_name || 'Neprecizat'}</p><p className="text-xs text-muted-foreground">{app.measure_name}</p></CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Buget estimat</p><p className="font-bold mt-1">{app.budget_estimated ? `${app.budget_estimated.toLocaleString()} RON` : 'Nesetat'}</p>{app.call_value_max && <p className="text-xs text-muted-foreground">Max eligibil: {app.call_value_max?.toLocaleString()} RON</p>}</CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Documente</p><p className="font-bold mt-1">{docs.length} / {reqDocs.length} cerute</p></CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Drafturi</p><p className="font-bold mt-1">{drafts.length} generate</p></CardContent></Card>
          </div>
          {app.description && <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground mb-1">Descriere</p><p>{app.description}</p></CardContent></Card>}
          {app.company_context && (
            <Card className="bg-card border-border"><CardContent className="p-5">
              <p className="text-sm text-muted-foreground mb-2">Context firmă activă</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div><span className="text-muted-foreground">Firmă:</span> <strong>{app.company_context.denumire}</strong></div>
                <div><span className="text-muted-foreground">CUI:</span> <strong>{app.company_context.cui}</strong></div>
                <div><span className="text-muted-foreground">CAEN:</span> <strong>{app.company_context.caen_principal?.cod || 'N/A'}</strong></div>
                <div><span className="text-muted-foreground">Județ:</span> <strong>{app.company_context.judet || 'N/A'}</strong></div>
              </div>
            </CardContent></Card>
          )}
          {app.extracted_data?.scraped_info && (
            <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base flex items-center gap-2"><Bot className="w-4 h-4 text-primary" />Date extrase din link-uri (Agent Colector)</CardTitle></CardHeader>
              <CardContent><AiMessage text={app.extracted_data.scraped_info} /></CardContent>
            </Card>
          )}
          {app.custom_links?.length > 0 && (
            <Card className="bg-card border-border"><CardContent className="p-5">
              <p className="text-sm text-muted-foreground mb-2">Link-uri sursă</p>
              {app.custom_links.map((l, i) => <a key={i} href={l} target="_blank" rel="noopener noreferrer" className="block text-sm text-primary hover:underline truncate">{l}</a>)}
            </CardContent></Card>
          )}
        </TabsContent>

        {/* ORCHESTRATOR */}
        <TabsContent value="orchestrator" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-heading text-lg font-bold flex items-center gap-2"><Zap className="w-5 h-5 text-primary" />Agent Coordonator</h2>
              <p className="text-muted-foreground text-sm">Verifică starea tuturor agenților pentru acest dosar</p>
            </div>
            <Button onClick={runOrchestrator} disabled={orchestratorLoading} data-testid="run-orchestrator-btn">
              {orchestratorLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se analizează...</> : <><Zap className="w-4 h-4 mr-2" />Verificare completă</>}
            </Button>
          </div>
          {orchestratorReport && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {orchestratorReport.checks?.map((c, i) => (
                  <Card key={i} className={`border ${c.status === 'ok' ? 'border-green-200 bg-green-50/50' : c.status === 'actiune_necesara' ? 'border-red-200 bg-red-50/50' : 'border-amber-200 bg-amber-50/50'}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 mb-2">
                        {c.status === 'ok' ? <CheckCircle className="w-4 h-4 text-green-500" /> : <AlertTriangle className="w-4 h-4 text-amber-500" />}
                        <span className="font-semibold text-sm">{c.agent}</span>
                      </div>
                      {c.issues?.length > 0 ? <ul className="space-y-1">{c.issues.map((is2, j) => <li key={j} className="text-xs text-muted-foreground">{is2}</li>)}</ul> : <p className="text-xs text-green-600">OK</p>}
                    </CardContent>
                  </Card>
                ))}
              </div>
              <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base flex items-center gap-2"><Bot className="w-4 h-4 text-primary" />Analiză AI</CardTitle></CardHeader>
                <CardContent><AiMessage text={orchestratorReport.ai_analysis} /></CardContent></Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="guide" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-heading text-lg font-bold">Legislație – Ghid solicitant & Anexe</h2>
              <p className="text-sm text-muted-foreground">La încărcare, agenții parsează documentul, extrag criterii, documente cerute și actualizează dosarul automat.</p>
            </div>
            <div>
              <input type="file" id="guide-upload" className="hidden" onChange={uploadGuide} accept=".pdf,.doc,.docx,.txt" />
              <Button variant="outline" onClick={() => document.getElementById('guide-upload').click()} disabled={guideProcessing} data-testid="upload-guide-btn">
                {guideProcessing ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Agenții procesează...</> : <><Upload className="w-4 h-4 mr-2" />Încarcă ghid / anexă</>}
              </Button>
            </div>
          </div>

          {/* Agent actions after upload */}
          {guideActions.length > 0 && (
            <Card className="bg-green-50 border-green-200"><CardContent className="p-4 space-y-1.5">
              <p className="font-semibold text-sm text-green-700 flex items-center gap-2"><Zap className="w-4 h-4" />Acțiuni efectuate de agenți:</p>
              {guideActions.map((a, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-green-800">
                  <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" /><span>{a}</span>
                </div>
              ))}
            </CardContent></Card>
          )}

          {(app.guide_assets || []).length === 0 ? (
            <Card className="bg-card border-border"><CardContent className="p-10 text-center">
              <BookOpen className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
              <p className="font-medium">Niciun ghid încărcat</p>
              <p className="text-sm text-muted-foreground mt-1">Încarcă ghidul solicitantului pentru ca agenții să extragă automat criterii, documente cerute și grila de conformitate.</p>
            </CardContent></Card>
          ) : (
            <div className="space-y-2">{app.guide_assets.map(g => (
              <Card key={g.id} className="bg-card border-border"><CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BookOpen className="w-5 h-5 text-primary" />
                    <div>
                      <p className="font-medium">{g.filename}</p>
                      <p className="text-xs text-muted-foreground">{g.tip} &middot; {(g.file_size / 1024).toFixed(0)} KB</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {g.extraction_status === 'completed' && <Badge className="bg-green-50 text-green-600 text-xs"><CheckCircle className="w-3 h-3 mr-1" />Procesat</Badge>}
                    {g.extraction_status === 'error' && <Badge className="bg-red-50 text-red-500 text-xs"><AlertTriangle className="w-3 h-3 mr-1" />Eroare</Badge>}
                    <Badge variant="secondary">{g.tip}</Badge>
                    <Button variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10 h-7 w-7 p-0" onClick={async () => { try { await api.delete(`/v2/applications/${id}/guide/${g.id}`); load(); } catch(e) { console.error(e); } }} data-testid={`delete-guide-${g.id}`}><X className="w-3.5 h-3.5" /></Button>
                  </div>
                </div>
                {g.extracted_content?.rezumat && (
                  <p className="text-sm text-muted-foreground mt-2 border-t pt-2">{g.extracted_content.rezumat}</p>
                )}
              </CardContent></Card>
            ))}</div>
          )}

          {/* Show extracted eligibility criteria if available */}
          {app.criterii_eligibilitate_ghid?.length > 0 && (
            <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base">Criterii eligibilitate (din ghid)</CardTitle></CardHeader>
              <CardContent><ul className="space-y-1">{app.criterii_eligibilitate_ghid.map((c, i) => (
                <li key={i} className="text-sm flex items-start gap-2"><CheckCircle className="w-3.5 h-3.5 mt-0.5 text-primary flex-shrink-0" />{typeof c === 'string' ? c : c.criteriu || JSON.stringify(c)}</li>
              ))}</ul></CardContent>
            </Card>
          )}
        </TabsContent>

        {/* CONFIGURARE PROIECT */}
        <TabsContent value="config" className="space-y-4">
          <h2 className="font-heading text-lg font-bold flex items-center gap-2"><Settings className="w-5 h-5 text-primary" />Configurare proiect</h2>
          {/* Show call info if available */}
          {(app.call_value_min || app.call_value_max || app.call_budget) && (
            <Card className="bg-primary/5 border-primary/20"><CardContent className="p-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              {app.program_name && <div><p className="text-muted-foreground text-xs">Program</p><p className="font-bold">{app.program_name}</p></div>}
              {app.call_budget && <div><p className="text-muted-foreground text-xs">Buget sesiune</p><p className="font-bold">{app.call_budget?.toLocaleString()} RON</p></div>}
              {app.call_value_min && <div><p className="text-muted-foreground text-xs">Valoare min-max proiect</p><p className="font-bold">{app.call_value_min?.toLocaleString()} – {app.call_value_max?.toLocaleString()} RON</p></div>}
              {app.call_region && <div><p className="text-muted-foreground text-xs">Regiune</p><p className="font-bold">{app.call_region}</p></div>}
            </CardContent></Card>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Tip proiect</Label>
              <select className="w-full h-10 rounded-md border px-3 text-sm" value={config.tip_proiect} onChange={(e) => setConfig({...config, tip_proiect: e.target.value})} data-testid="config-tip">
                <option value="">Selectează...</option>
                <option value="bunuri">Bunuri</option>
                <option value="bunuri_montaj">Bunuri cu montaj</option>
                <option value="constructii">Construcții</option>
                <option value="servicii">Servicii</option>
                <option value="mixt">Mixt</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Buget estimat proiect (RON)</Label>
              <Input type="number" value={config.buget || ''} onChange={(e) => setConfig({...config, buget: e.target.value})} placeholder={app.call_value_max ? `Max: ${app.call_value_max.toLocaleString()} RON` : 'Suma în RON'} data-testid="config-buget" />
              {app.call_value_min && <p className="text-xs text-muted-foreground">Interval eligibil: {app.call_value_min?.toLocaleString()} – {app.call_value_max?.toLocaleString()} RON</p>}
            </div>
            <div className="space-y-2"><Label>Județ implementare</Label><Input value={config.judet} onChange={(e) => setConfig({...config, judet: e.target.value})} placeholder="ex: București" data-testid="config-judet" /></div>
            <div className="space-y-2"><Label>Locație implementare (adresă / CF)</Label><Input value={config.locatie} onChange={(e) => setConfig({...config, locatie: e.target.value})} placeholder="Adresă sau nr. Carte Funciară" data-testid="config-locatie" /></div>
            <div className="space-y-2 md:col-span-2">
              <Label>Tema proiectului (ce se dorește a fi achiziționat)</Label>
              <Textarea value={config.tema} onChange={(e) => setConfig({...config, tema: e.target.value})} rows={3} placeholder="Descrieți obiectivele și ce se va achiziționa prin proiect..." data-testid="config-tema" />
            </div>
          </div>
          <Button onClick={saveConfig} data-testid="save-config-btn">Salvează configurarea</Button>
        </TabsContent>

        {/* PRE-ELIGIBILITATE */}
        <TabsContent value="preeligibility" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-heading text-lg font-bold flex items-center gap-2"><Shield className="w-5 h-5 text-primary" />Pre-eligibilitate</h2>
              <p className="text-muted-foreground text-sm">Verifică eligibilitatea firmei pentru sesiunea selectată</p>
            </div>
            <Button onClick={runPreeligibility} disabled={preeligLoading} data-testid="run-preelig-btn">
              {preeligLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se verifică...</> : <><Bot className="w-4 h-4 mr-2" />Verifică eligibilitate</>}
            </Button>
          </div>
          {app.company_context && (
            <Card className="bg-card border-border"><CardContent className="p-4">
              <p className="text-sm text-muted-foreground mb-2">Date firmă verificate:</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div><strong>{app.company_context.denumire}</strong></div>
                <div>CUI: <strong>{app.company_context.cui}</strong></div>
                <div>CAEN: <strong>{app.company_context.caen_principal?.cod || 'N/A'}</strong></div>
                <div>Angajați: <strong>{app.company_context.nr_angajati || 'N/A'}</strong></div>
              </div>
            </CardContent></Card>
          )}
          {preeligReport && (
            <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base flex items-center gap-2"><Bot className="w-4 h-4 text-primary" />Raport pre-eligibilitate</CardTitle></CardHeader>
              <CardContent><AiMessage text={preeligReport.result} /></CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ACHIZIȚII */}
        <TabsContent value="achizitii" className="space-y-4">
          <h2 className="font-heading text-lg font-bold flex items-center gap-2"><ShoppingCart className="w-5 h-5 text-primary" />Achiziții proiect (SICAP / AFIR)</h2>
          <Card className="bg-card border-border"><CardContent className="p-5 space-y-4">
            <div className="flex gap-2">
              <Input value={achizitiiSearch} onChange={(e) => setAchizitiiSearch(e.target.value)} placeholder="Caută echipamente, servicii..." className="flex-1" onKeyDown={(e) => e.key === 'Enter' && searchAchizitii()} data-testid="search-achizitii" />
              <Button onClick={searchAchizitii} data-testid="search-ach-btn"><Search className="w-4 h-4 mr-1" />Caută</Button>
            </div>
            {sicapResults.length > 0 && <div><p className="text-sm font-medium mb-2">SICAP (CPV):</p>
              <div className="space-y-1.5 max-h-40 overflow-y-auto">{sicapResults.map((r, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-secondary/30 rounded text-sm">
                  <div><strong>{r.descriere}</strong><span className="text-muted-foreground ml-2">CPV: {r.cod} &middot; {r.pret_referinta_min?.toLocaleString()}-{r.pret_referinta_max?.toLocaleString()} RON</span></div>
                  <Button size="sm" variant="ghost" onClick={() => addAchizitie(r)}><Plus className="w-3 h-3" /></Button>
                </div>
              ))}</div>
            </div>}
            {afirResults.length > 0 && <div><p className="text-sm font-medium mb-2">AFIR prețuri referință:</p>
              <div className="space-y-1.5 max-h-40 overflow-y-auto">{afirResults.map((r, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-secondary/30 rounded text-sm">
                  <div><strong>{r.subcategorie}</strong><span className="text-muted-foreground ml-2">{r.pret_min?.toLocaleString()}-{r.pret_max?.toLocaleString()} RON/{r.unitate}</span></div>
                  <Button size="sm" variant="ghost" onClick={() => addAchizitie(r)}><Plus className="w-3 h-3" /></Button>
                </div>
              ))}</div>
            </div>}
          </CardContent></Card>
          {achizitii.length > 0 && <div className="space-y-2">
            <h3 className="font-heading text-base font-bold">Lista achiziții ({achizitii.length})</h3>
            {achizitii.map((a, i) => (
              <Card key={a.id} className="bg-card border-border"><CardContent className="p-3 flex items-center justify-between">
                <div><p className="font-medium text-sm">{a.descriere}</p><p className="text-xs text-muted-foreground">{a.cpv && `CPV: ${a.cpv} · `}{a.cantitate} × {a.pret_unitar?.toLocaleString()} RON</p></div>
                <p className="font-bold text-sm">{(a.cantitate * a.pret_unitar)?.toLocaleString()} RON</p>
              </CardContent></Card>
            ))}
            <Card className="bg-primary/5 border-primary/20"><CardContent className="p-3 flex justify-between"><strong>Total</strong><strong className="text-primary">{achizitii.reduce((s, a) => s + a.cantitate * a.pret_unitar, 0)?.toLocaleString()} RON</strong></CardContent></Card>
            <Button onClick={saveConfig} size="sm">Salvează achizițiile</Button>
          </div>}
        </TabsContent>

        <TabsContent value="checklist" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-lg font-bold">Documente cerute (Checklist)</h2>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={proposeRequiredDocs} data-testid="propose-docs-btn"><Bot className="w-4 h-4 mr-1" />Propune din ghid</Button>
              {!app.checklist_frozen && reqDocs.length > 0 && <Button size="sm" onClick={freezeChecklist} data-testid="freeze-checklist-btn">Înghează checklist</Button>}
            </div>
          </div>
          {app.checklist_frozen && <Badge className="bg-blue-50 text-blue-600 border-blue-200 rounded-full">Checklist înghețat</Badge>}
          <div className="space-y-2">
            {reqDocs.map((rd, i) => (
              <div key={rd.id} className="flex items-center gap-3 p-3 rounded-lg border border-border" data-testid={`req-doc-${rd.id}`}>
                <span className="text-sm font-mono text-muted-foreground w-8">{rd.order_index}.</span>
                {rd.status === 'uploaded' ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-400" />}
                <span className="flex-1 text-sm font-medium">{rd.official_name}</span>
                <Badge variant="secondary" className="text-xs">{rd.folder_group}</Badge>
                <Badge className={`text-xs rounded-full ${rd.status === 'uploaded' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'}`}>{rd.status}</Badge>
              </div>
            ))}
          </div>
          {!app.checklist_frozen && (
            <div className="flex gap-2 items-end mt-4">
              <div className="flex-1 space-y-1"><Label className="text-xs">Nume document</Label><Input value={newReqDoc.official_name} onChange={(e) => setNewReqDoc({...newReqDoc, official_name: e.target.value})} placeholder="Ex: Cerere de finanțare" data-testid="req-doc-name" /></div>
              <div className="w-36 space-y-1"><Label className="text-xs">Folder</Label>
                <select className="w-full h-10 rounded-md border px-2 text-sm" value={newReqDoc.folder_group} onChange={(e) => setNewReqDoc({...newReqDoc, folder_group: e.target.value})} data-testid="req-doc-folder">
                  <option value="achizitii">Achiziții</option><option value="depunere">Depunere</option><option value="contractare">Contractare</option><option value="implementare">Implementare</option>
                </select>
              </div>
              <Button onClick={addRequiredDoc} disabled={!newReqDoc.official_name} data-testid="add-req-doc-btn"><Plus className="w-4 h-4" /></Button>
            </div>
          )}
          {validationReport?.type === 'proposed_docs' && (
            <Card className="bg-card border-border mt-4"><CardHeader><CardTitle className="text-base flex items-center gap-2"><Bot className="w-4 h-4 text-primary" />Documente propuse de AI</CardTitle></CardHeader>
              <CardContent><AiMessage text={validationReport.result} /></CardContent></Card>
          )}
        </TabsContent>

        <TabsContent value="documents" className="space-y-6">
          {folders.map(fg => {
            const folderDocs = docs.filter(d => d.folder_group === fg.key);
            return (
              <div key={fg.key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-heading text-base font-bold flex items-center gap-2"><FolderOpen className="w-4 h-4 text-primary" />{fg.name} ({folderDocs.length})</h3>
                  <div><input type="file" id={`folder-${fg.key}`} className="hidden" onChange={(e) => uploadDocument(e, fg.key)} /><Button variant="outline" size="sm" onClick={() => document.getElementById(`folder-${fg.key}`).click()} data-testid={`upload-${fg.key}`}><Upload className="w-3 h-3 mr-1" />Upload</Button></div>
                </div>
                {folderDocs.length === 0 ? <p className="text-sm text-muted-foreground pl-6">Niciun document</p> : folderDocs.map(d => (
                  <Card key={d.id} className="bg-card border-border ml-6"><CardContent className="p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <span className="text-sm font-medium truncate">{d.filename}</span>
                        {d.tip_document && d.tip_document !== 'altele' && <Badge variant="secondary" className="text-xs">{d.tip_document}</Badge>}
                      </div>
                      <div className="flex items-center gap-2">
                        {d.ocr_status === 'completed' && <Badge className="text-xs rounded-full bg-green-50 text-green-600"><CheckCircle className="w-3 h-3 mr-1" />OCR OK</Badge>}
                        {d.ocr_status === 'needs_review' && <Badge className="text-xs rounded-full bg-amber-50 text-amber-600"><AlertTriangle className="w-3 h-3 mr-1" />Revizuire</Badge>}
                        {d.ocr_status === 'processing' && <Badge className="text-xs rounded-full bg-blue-50 text-blue-600"><Loader2 className="w-3 h-3 mr-1 animate-spin" />OCR...</Badge>}
                        <Badge className={`text-xs rounded-full ${d.status === 'uploaded' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'}`}>{d.status}</Badge>
                        <Button variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10 h-7 w-7 p-0" onClick={async () => { try { await api.delete(`/v2/applications/${id}/documents/${d.id}`); load(); } catch(e) { console.error(e); } }} data-testid={`delete-doc-${d.id}`}><X className="w-3.5 h-3.5" /></Button>
                      </div>
                    </div>
                    {d.ocr_data?.extracted_fields && Object.keys(d.ocr_data.extracted_fields).length > 0 && (
                      <div className="mt-2 pl-6 text-xs text-muted-foreground border-t pt-2 flex flex-wrap gap-x-4 gap-y-1">
                        {Object.entries(d.ocr_data.extracted_fields).slice(0, 5).map(([k, v]) => (
                          <span key={k}><strong className="text-foreground/70">{k.replace(/_/g, ' ')}:</strong> {String(v).slice(0, 40)}</span>
                        ))}
                        {Object.keys(d.ocr_data.extracted_fields).length > 5 && <span>+{Object.keys(d.ocr_data.extracted_fields).length - 5} câmpuri</span>}
                      </div>
                    )}
                  </CardContent></Card>
                ))}
              </div>
            );
          })}
        </TabsContent>

        <TabsContent value="drafts" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-lg font-bold">Generare documente (Redactor AI)</h2>
          </div>
          <p className="text-sm text-muted-foreground">Selectează un template standard sau creează unul propriu. AI-ul completează pe baza datelor firmei și proiectului.</p>

          {/* Standard templates */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {templates.map(t => (
              <Card key={t.id} className="bg-card border-border hover:border-primary/30 transition-colors"><CardContent className="p-4 space-y-2">
                <div className="flex items-center gap-2"><FileText className="w-4 h-4 text-primary" /><p className="font-semibold text-sm">{t.label}</p></div>
                <p className="text-xs text-muted-foreground">{t.sections?.slice(0, 3).join(', ')}{t.sections?.length > 3 ? ` +${t.sections.length - 3}` : ''}</p>
                <Button size="sm" className="w-full" onClick={() => generateDraft(t.id)} disabled={generating === t.id} data-testid={`gen-${t.id}`}>
                  {generating === t.id ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se generează...</> : <><Bot className="w-4 h-4 mr-2" />Generează</>}
                </Button>
              </CardContent></Card>
            ))}
            {/* Custom templates from this application */}
            {(app.custom_templates || []).map(t => (
              <Card key={t.id} className="bg-card border-primary/20 hover:border-primary/40 transition-colors"><CardContent className="p-4 space-y-2">
                <div className="flex items-center gap-2"><FileText className="w-4 h-4 text-amber-500" /><p className="font-semibold text-sm">{t.label}</p><Badge className="text-xs bg-amber-50 text-amber-600">Custom</Badge></div>
                <p className="text-xs text-muted-foreground">{t.sections?.join(', ')}</p>
                <Button size="sm" className="w-full" onClick={() => generateDraft(t.id)} disabled={generating === t.id}>
                  {generating === t.id ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se generează...</> : <><Bot className="w-4 h-4 mr-2" />Generează</>}
                </Button>
              </CardContent></Card>
            ))}
          </div>

          {/* Add custom template */}
          <Card className="bg-secondary/20 border-dashed border-2 border-border"><CardContent className="p-4 space-y-3">
            <p className="font-semibold text-sm flex items-center gap-2"><Plus className="w-4 h-4" />Adaugă template propriu</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1"><Label className="text-xs">Titlu template</Label><Input value={customTemplate.label} onChange={(e) => setCustomTemplate({...customTemplate, label: e.target.value})} placeholder="ex: Declarație pe proprie răspundere" data-testid="custom-tpl-label" /></div>
              <div className="space-y-1"><Label className="text-xs">Secțiuni (separate prin virgulă)</Label><Input value={customTemplate.sections} onChange={(e) => setCustomTemplate({...customTemplate, sections: e.target.value})} placeholder="Identificare, Conținut, Semnătură" data-testid="custom-tpl-sections" /></div>
            </div>
            <Button size="sm" variant="outline" disabled={!customTemplate.label} onClick={async () => {
              try {
                await api.post(`/v2/applications/${id}/custom-template`, { label: customTemplate.label, sections: customTemplate.sections.split(',').map(s => s.trim()).filter(Boolean) });
                setCustomTemplate({ label: '', sections: '' });
                load();
              } catch (e) { console.error(e); }
            }} data-testid="add-custom-tpl-btn"><Plus className="w-4 h-4 mr-1" />Adaugă template</Button>
          </CardContent></Card>

          {/* Generated drafts */}
          {drafts.length > 0 && <div className="space-y-3 mt-4">
            <h3 className="font-heading text-base font-bold">Documente generate ({drafts.length})</h3>
            {drafts.map((d, idx) => (
              <Card key={d.id} className="bg-card border-border"><CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2">
                <span className="text-sm font-mono text-muted-foreground w-6">{String(idx + 1).padStart(2, '0')}.</span>
                <CheckCircle className="w-4 h-4 text-green-500" />{d.template_label}
                {d.pdf_url && <a href={`${process.env.REACT_APP_BACKEND_URL}${d.pdf_url}`} target="_blank" rel="noopener noreferrer" className="ml-auto"><Button size="sm" variant="outline"><Download className="w-3 h-3 mr-1" />PDF</Button></a>}
              </CardTitle></CardHeader>
              <CardContent className="max-h-48 overflow-y-auto border-t pt-2"><AiMessage text={d.content} /></CardContent></Card>
            ))}
          </div>}
        </TabsContent>

        <TabsContent value="validation" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-heading text-lg font-bold flex items-center gap-2"><Shield className="w-5 h-5 text-primary" />Evaluare & Grilă Conformitate</h2>
              <p className="text-muted-foreground text-sm">Agentul Evaluator verifică dosarul conform grilei de conformitate</p>
            </div>
            <Button onClick={validate} disabled={validating} data-testid="validate-btn">
              {validating ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se evaluează...</> : <><Shield className="w-4 h-4 mr-2" />Evaluare conformitate</>}
            </Button>
          </div>
          {validationReport?.type === 'validation' && (
            <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base">Raport validare</CardTitle></CardHeader>
              <CardContent><AiMessage text={validationReport.result} /></CardContent></Card>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-2">
          {(app.history || []).slice().reverse().map((h, i) => (
            <div key={i} className="flex items-center gap-3 p-3 border-b border-border last:border-0">
              <div className="w-2 h-2 rounded-full bg-primary" />
              <Badge className="text-xs rounded-full">{STATE_LABELS[h.to]}</Badge>
              <span className="text-sm text-muted-foreground flex-1">{h.reason}</span>
              <span className="text-xs text-muted-foreground">{new Date(h.at).toLocaleString('ro-RO')}</span>
            </div>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
