import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AiMessage } from '@/components/shared/AiMessage';
import {
  ArrowLeft, ArrowRight, Upload, FileText, Shield, Bot, CheckCircle, XCircle,
  FolderOpen, BookOpen, PenTool, Zap, Download, Loader2, Plus, AlertTriangle, Package
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

  const load = async () => {
    try {
      const [aRes, tRes] = await Promise.all([api.get(`/v2/applications/${id}`), api.get('/v2/templates')]);
      setApp(aRes.data);
      setTemplates(tRes.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };
  useEffect(() => { load(); }, [id]);

  const transition = async (newState) => {
    setTransitioning(true);
    try { await api.post(`/v2/applications/${id}/transition`, { new_state: newState }); load(); } catch (e) { console.error(e); }
    setTransitioning(false);
  };

  const uploadGuide = async (e) => {
    if (!e.target.files[0]) return;
    const fd = new FormData(); fd.append('file', e.target.files[0]); fd.append('tip', 'ghid');
    try { await api.post(`/v2/applications/${id}/guide`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }); load(); } catch (err) { console.error(err); }
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
          <TabsTrigger value="guide"><BookOpen className="w-4 h-4 mr-1" />Ghid & Anexe</TabsTrigger>
          <TabsTrigger value="checklist"><CheckCircle className="w-4 h-4 mr-1" />Checklist</TabsTrigger>
          <TabsTrigger value="documents"><FolderOpen className="w-4 h-4 mr-1" />Documente</TabsTrigger>
          <TabsTrigger value="drafts"><PenTool className="w-4 h-4 mr-1" />Drafturi</TabsTrigger>
          <TabsTrigger value="validation"><Shield className="w-4 h-4 mr-1" />Validare</TabsTrigger>
          <TabsTrigger value="history">Istoric</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Sesiune</p><p className="font-bold mt-1">{app.call_name}</p></CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Ghid & Anexe</p><p className="font-bold mt-1">{app.guide_assets?.length || 0} fișiere</p></CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Documente</p><p className="font-bold mt-1">{docs.length} / {reqDocs.length} cerute</p></CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-5"><p className="text-sm text-muted-foreground">Drafturi</p><p className="font-bold mt-1">{drafts.length} generate</p></CardContent></Card>
          </div>
        </TabsContent>

        <TabsContent value="guide" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-lg font-bold">Ghid solicitant & Anexe</h2>
            <div><input type="file" id="guide-upload" className="hidden" onChange={uploadGuide} /><Button variant="outline" onClick={() => document.getElementById('guide-upload').click()} data-testid="upload-guide-btn"><Upload className="w-4 h-4 mr-2" />Încarcă ghid / anexă</Button></div>
          </div>
          {(app.guide_assets || []).length === 0 ? <p className="text-muted-foreground">Niciun ghid încărcat. Încarcă ghidul solicitantului pentru a continua.</p> : (
            <div className="space-y-2">{app.guide_assets.map(g => (
              <Card key={g.id} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3"><BookOpen className="w-5 h-5 text-primary" /><div><p className="font-medium">{g.filename}</p><p className="text-xs text-muted-foreground">{g.tip} &middot; {(g.file_size / 1024).toFixed(0)} KB</p></div></div>
                <Badge variant="secondary">{g.tip}</Badge>
              </CardContent></Card>
            ))}</div>
          )}
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
                  <Card key={d.id} className="bg-card border-border ml-6"><CardContent className="p-3 flex items-center justify-between">
                    <div className="flex items-center gap-2"><FileText className="w-4 h-4 text-muted-foreground" /><span className="text-sm font-medium">{d.filename}</span></div>
                    <Badge className={`text-xs rounded-full ${d.status === 'uploaded' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'}`}>{d.status}</Badge>
                  </CardContent></Card>
                ))}
              </div>
            );
          })}
        </TabsContent>

        <TabsContent value="drafts" className="space-y-4">
          <h2 className="font-heading text-lg font-bold">Generare documente (Redactor AI)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map(t => (
              <Card key={t.id} className="bg-card border-border hover:border-primary/30 transition-colors"><CardContent className="p-5 space-y-3">
                <div className="flex items-center gap-2"><FileText className="w-5 h-5 text-primary" /><p className="font-semibold">{t.label}</p></div>
                <Button size="sm" className="w-full" onClick={() => generateDraft(t.id)} disabled={generating === t.id} data-testid={`gen-${t.id}`}>
                  {generating === t.id ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se generează...</> : <><Bot className="w-4 h-4 mr-2" />Generează PDF</>}
                </Button>
              </CardContent></Card>
            ))}
          </div>
          {drafts.length > 0 && <div className="space-y-3 mt-4">
            <h3 className="font-heading text-base font-bold">Generate ({drafts.length})</h3>
            {drafts.map(d => (
              <Card key={d.id} className="bg-card border-border"><CardHeader className="pb-2"><CardTitle className="text-base flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />{d.template_label}
                {d.pdf_url && <a href={`${process.env.REACT_APP_BACKEND_URL}${d.pdf_url}`} target="_blank" rel="noopener noreferrer" className="ml-auto"><Button size="sm" variant="outline"><Download className="w-3 h-3 mr-1" />PDF</Button></a>}
              </CardTitle></CardHeader>
              <CardContent className="max-h-48 overflow-y-auto border-t pt-2"><AiMessage text={d.content} /></CardContent></Card>
            ))}
          </div>}
        </TabsContent>

        <TabsContent value="validation" className="space-y-4">
          <div className="flex gap-2">
            <Button onClick={validate} disabled={validating} data-testid="validate-btn">
              {validating ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se validează...</> : <><Shield className="w-4 h-4 mr-2" />Validare dosar</>}
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
