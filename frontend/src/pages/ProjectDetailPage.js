import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  ArrowLeft, ArrowRight, Send, FileText, Shield, Bot, Clock,
  TrendingUp, AlertTriangle, CheckCircle, XCircle, Milestone, DollarSign, MessageSquare
} from 'lucide-react';
import { AiMessage } from '@/components/shared/AiMessage';

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

const ALL_STATES = [
  'draft', 'pre_eligibil', 'blocat', 'conform', 'depus',
  'aprobat', 'respins', 'in_implementare', 'suspendat',
  'finalizat', 'audit_post', 'arhivat'
];
const STATE_LABELS = {
  draft: 'Ciornă', pre_eligibil: 'Pre-eligibil', blocat: 'Blocat',
  conform: 'Conform', depus: 'Depus', aprobat: 'Aprobat', respins: 'Respins',
  in_implementare: 'Implementare', suspendat: 'Suspendat',
  finalizat: 'Finalizat', audit_post: 'Audit', arhivat: 'Arhivat'
};

export function ProjectDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [states, setStates] = useState({});
  const [loading, setLoading] = useState(true);
  const [transitionLoading, setTransitionLoading] = useState(false);
  const [chatMsg, setChatMsg] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [eligibilityLoading, setEligibilityLoading] = useState(false);
  const [reports, setReports] = useState([]);
  const [submissionReady, setSubmissionReady] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [pRes, sRes, rRes] = await Promise.all([
          api.get(`/projects/${id}`),
          api.get('/projects/states'),
          api.get(`/compliance/reports/${id}`).catch(() => ({ data: [] }))
        ]);
        setProject(pRes.data);
        setStates(sRes.data.transitions || {});
        setReports(rRes.data || []);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, [id]);

  const handleTransition = async (newState) => {
    setTransitionLoading(true);
    try {
      await api.post(`/projects/${id}/transition`, { new_state: newState });
      const res = await api.get(`/projects/${id}`);
      setProject(res.data);
    } catch (e) { console.error(e); }
    setTransitionLoading(false);
  };

  const checkEligibility = async () => {
    setEligibilityLoading(true);
    try {
      const res = await api.post('/compliance/eligibility-check', { project_id: id });
      setReports([res.data, ...reports]);
    } catch (e) { console.error(e); }
    setEligibilityLoading(false);
  };

  const checkSubmission = async () => {
    try {
      const res = await api.post(`/compliance/submission-ready/${id}`);
      setSubmissionReady(res.data);
    } catch (e) { console.error(e); }
  };

  const sendChat = async () => {
    if (!chatMsg.trim()) return;
    const msg = chatMsg;
    setChatHistory([...chatHistory, { role: 'user', text: msg }]);
    setChatMsg('');
    setChatLoading(true);
    try {
      const res = await api.post('/compliance/navigator', { message: msg, project_id: id });
      setChatHistory(h => [...h, { role: 'assistant', text: res.data.response }]);
    } catch (e) {
      setChatHistory(h => [...h, { role: 'assistant', text: 'Eroare la generarea răspunsului.' }]);
    }
    setChatLoading(false);
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;
  if (!project) return <div className="text-center text-muted-foreground">Proiectul nu a fost găsit</div>;

  const possibleTransitions = states[project.stare] || [];
  const budgetProgress = project.buget_estimat > 0 ? Math.min((project.cheltuieli_totale / project.buget_estimat) * 100, 100) : 0;

  return (
    <div data-testid="project-detail-page" className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/projects"><Button variant="ghost" size="icon" data-testid="back-to-projects"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-bold tracking-tight">{project.titlu}</h1>
            <Badge className={`rounded-full px-2.5 py-0.5 text-xs font-medium border ${STATE_COLORS[project.stare] || STATE_COLORS.draft}`}>
              {project.stare_label}
            </Badge>
          </div>
          <p className="text-muted-foreground text-sm">{project.organizatie_denumire} &middot; {project.program_finantare}</p>
        </div>
      </div>

      {/* State Machine */}
      <Card className="bg-card border-border">
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto pb-2">
            {ALL_STATES.map((s, i) => (
              <div key={s} className="flex items-center">
                <div className={`px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-all ${
                  s === project.stare ? 'bg-primary text-primary-foreground shadow-[0_0_10px_rgba(59,130,246,0.5)]'
                  : project.history?.some(h => h.to_state === s) ? 'bg-muted text-foreground' : 'bg-muted/50 text-muted-foreground'
                }`} data-testid={`state-${s}`}>
                  {STATE_LABELS[s]}
                </div>
                {i < ALL_STATES.length - 1 && <ArrowRight className="w-3 h-3 text-muted-foreground mx-1 flex-shrink-0" />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Transitions */}
      {possibleTransitions.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-muted-foreground">Tranziții disponibile:</span>
          {possibleTransitions.map((t) => (
            <Button key={t} variant="outline" size="sm" onClick={() => handleTransition(t)} disabled={transitionLoading} data-testid={`transition-${t}`}>
              <ArrowRight className="w-3 h-3 mr-1" />{STATE_LABELS[t]}
            </Button>
          ))}
        </div>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="bg-muted">
          <TabsTrigger value="overview" data-testid="tab-overview">Sumar</TabsTrigger>
          <TabsTrigger value="compliance" data-testid="tab-compliance">Conformitate</TabsTrigger>
          <TabsTrigger value="budget" data-testid="tab-budget">Buget</TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">Istoric</TabsTrigger>
          <TabsTrigger value="navigator" data-testid="tab-navigator">Ghid AI</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-card border-border"><CardContent className="p-4">
              <p className="text-sm text-muted-foreground mb-1">Buget estimat</p>
              <p className="text-xl font-bold">{project.buget_estimat?.toLocaleString()} RON</p>
            </CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-4">
              <p className="text-sm text-muted-foreground mb-1">Cheltuieli totale</p>
              <p className="text-xl font-bold">{project.cheltuieli_totale?.toLocaleString()} RON</p>
            </CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-4">
              <p className="text-sm text-muted-foreground mb-1">Documente</p>
              <p className="text-xl font-bold">{project.documents?.length || 0}</p>
            </CardContent></Card>
          </div>
          {project.descriere && (
            <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base">Descriere</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">{project.descriere}</p></CardContent>
            </Card>
          )}
          {project.obiective?.length > 0 && (
            <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base">Obiective</CardTitle></CardHeader>
              <CardContent><ul className="space-y-1">{project.obiective.map((o, i) => (
                <li key={i} className="text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" />{o}</li>
              ))}</ul></CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="compliance" className="space-y-4">
          <div className="flex gap-2">
            <Button onClick={checkEligibility} disabled={eligibilityLoading} data-testid="check-eligibility-btn">
              <Shield className="w-4 h-4 mr-2" />{eligibilityLoading ? 'Se verifică...' : 'Verifică eligibilitate'}
            </Button>
            <Button variant="outline" onClick={checkSubmission} data-testid="check-submission-btn">
              <FileText className="w-4 h-4 mr-2" />Verifică pregătire depunere
            </Button>
          </div>
          {submissionReady && (
            <Card className="bg-card border-border"><CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                {submissionReady.status === 'READY_FOR_SUBMISSION' ? <CheckCircle className="w-5 h-5 text-green-400" /> : <AlertTriangle className="w-5 h-5 text-amber-400" />}
                {submissionReady.status === 'READY_FOR_SUBMISSION' ? 'Pregătit pentru depunere' : 'Blocaje identificate'}
              </CardTitle>
            </CardHeader><CardContent className="space-y-2">
              {submissionReady.checks.map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {c.passed ? <CheckCircle className="w-4 h-4 text-green-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
                  <span className={c.passed ? 'text-foreground' : 'text-muted-foreground'}>{c.check}</span>
                </div>
              ))}
            </CardContent></Card>
          )}
          {reports.map((r) => (
            <Card key={r.id} className="bg-card border-border"><CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Bot className="w-4 h-4 text-purple-400" />{r.type === 'eligibility' ? 'Raport eligibilitate' : 'Raport validare'}
                <span className="text-xs text-muted-foreground ml-auto">{new Date(r.created_at).toLocaleDateString('ro-RO')}</span>
              </CardTitle>
            </CardHeader><CardContent>
              <AiMessage text={r.result} />
            </CardContent></Card>
          ))}
        </TabsContent>

        <TabsContent value="budget" className="space-y-4">
          <Card className="bg-card border-border"><CardContent className="p-4 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Buget utilizat</span>
              <span className="font-medium">{budgetProgress.toFixed(1)}%</span>
            </div>
            <Progress value={budgetProgress} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Cheltuieli: {project.cheltuieli_totale?.toLocaleString()} RON</span>
              <span>Buget: {project.buget_estimat?.toLocaleString()} RON</span>
            </div>
          </CardContent></Card>
          <h3 className="font-heading text-lg font-bold">Jaloane (Milestones)</h3>
          {(project.milestones || []).length === 0 ? (
            <p className="text-sm text-muted-foreground">Niciun jalon definit</p>
          ) : (
            <div className="space-y-2">{project.milestones.map((m) => (
              <Card key={m.id} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                <div><p className="font-medium text-sm">{m.titlu}</p><p className="text-xs text-muted-foreground">Deadline: {m.deadline} &middot; Buget: {m.buget_alocat?.toLocaleString()} RON</p></div>
                <Badge className="rounded-full">{m.status}</Badge>
              </CardContent></Card>
            ))}</div>
          )}
          <h3 className="font-heading text-lg font-bold">Cheltuieli</h3>
          {(project.expenses || []).length === 0 ? (
            <p className="text-sm text-muted-foreground">Nicio cheltuială înregistrată</p>
          ) : (
            <div className="space-y-2">{project.expenses.map((e) => (
              <Card key={e.id} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                <div><p className="font-medium text-sm">{e.descriere}</p><p className="text-xs text-muted-foreground">{e.categorie}</p></div>
                <span className="font-medium">{e.suma?.toLocaleString()} RON</span>
              </CardContent></Card>
            ))}</div>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <div className="relative pl-6">
            {(project.history || []).slice().reverse().map((h, i) => (
              <div key={i} className="relative pb-6 last:pb-0">
                <div className="absolute left-[-18px] top-1 w-3 h-3 rounded-full bg-primary border-2 border-background" />
                {i < project.history.length - 1 && <div className="absolute left-[-13px] top-4 bottom-0 w-px bg-border" />}
                <div>
                  <div className="flex items-center gap-2">
                    <Badge className={`rounded-full px-2 py-0.5 text-xs border ${STATE_COLORS[h.to_state] || ''}`}>{STATE_LABELS[h.to_state]}</Badge>
                    <span className="text-xs text-muted-foreground">{new Date(h.timestamp).toLocaleString('ro-RO')}</span>
                  </div>
                  {h.motiv && <p className="text-sm text-muted-foreground mt-1">{h.motiv}</p>}
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="navigator" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader><CardTitle className="text-base flex items-center gap-2">
              <Bot className="w-5 h-5 text-purple-400" />Ghid GrantFlow
              <Badge className="bg-purple-500/15 text-purple-400 border-purple-500/20 rounded-full text-xs">AI</Badge>
            </CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="max-h-80 overflow-y-auto space-y-3 min-h-[100px]" data-testid="chat-history">
                {chatHistory.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">Întreabă ghidul despre stadiul proiectului, pași următori sau blocaje.</p>
                )}
                {chatHistory.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg px-3 py-2 ${
                      m.role === 'user' ? 'bg-primary text-primary-foreground text-sm' : 'bg-muted'
                    }`}>
                      {m.role === 'user' ? m.text : <AiMessage text={m.text} />}
                    </div>
                  </div>
                ))}
                {chatLoading && <div className="flex justify-start"><div className="bg-muted rounded-lg px-3 py-2 text-sm text-muted-foreground animate-pulse">Se generează...</div></div>}
              </div>
              <div className="flex gap-2">
                <Input
                  value={chatMsg}
                  onChange={(e) => setChatMsg(e.target.value)}
                  placeholder="Întreabă ghidul..."
                  onKeyDown={(e) => e.key === 'Enter' && sendChat()}
                  data-testid="chat-input"
                />
                <Button onClick={sendChat} disabled={chatLoading || !chatMsg.trim()} data-testid="chat-send-btn">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
