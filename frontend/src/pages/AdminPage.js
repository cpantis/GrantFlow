import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  Users, Building2, FolderKanban, FileText, Shield, Clock,
  Activity, BarChart3, TrendingUp, Plug, TestTube, CheckCircle,
  XCircle, AlertTriangle, Settings, ExternalLink, Loader2
} from 'lucide-react';

const STATUS_BADGE = {
  activ: 'bg-green-500/10 text-green-600 border-green-500/20',
  mock: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  neconfigurat: 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20',
  eroare: 'bg-red-500/10 text-red-500 border-red-500/20',
};

const CAT_LABELS = { firme: 'Firme', programe: 'Programe finanțare', achizitii: 'Achiziții' };
const CAT_ICONS = { firme: Building2, programe: FolderKanban, achizitii: Shield };

export function AdminPage() {
  const [dashboard, setDashboard] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [users, setUsers] = useState([]);
  const [integrations, setIntegrations] = useState({});
  const [loading, setLoading] = useState(true);
  const [configOpen, setConfigOpen] = useState(false);
  const [configTarget, setConfigTarget] = useState(null);
  const [configForm, setConfigForm] = useState({ api_key: '', api_url: '', notes: '' });
  const [testing, setTesting] = useState(null);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [dRes, aRes, uRes, iRes] = await Promise.all([
          api.get('/admin/dashboard'),
          api.get('/admin/audit-log'),
          api.get('/admin/users').catch(() => ({ data: [] })),
          api.get('/integrations').catch(() => ({ data: {} })),
        ]);
        setDashboard(dRes.data);
        setAuditLog(aRes.data || []);
        setUsers(uRes.data || []);
        setIntegrations(iRes.data || {});
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, []);

  const openConfig = (integ) => {
    setConfigTarget(integ);
    setConfigForm({ api_key: '', api_url: integ.url_config || '', notes: integ.notes || '' });
    setTestResult(null);
    setConfigOpen(true);
  };

  const saveConfig = async () => {
    if (!configTarget) return;
    try {
      await api.put(`/integrations/${configTarget.id}`, { api_key: configForm.api_key || undefined, api_url: configForm.api_url || undefined, notes: configForm.notes || undefined, enabled: true });
      setConfigOpen(false);
      const res = await api.get('/integrations');
      setIntegrations(res.data || {});
    } catch (e) { console.error(e); }
  };

  const testIntegration = async (id) => {
    setTesting(id);
    setTestResult(null);
    try {
      const res = await api.post(`/integrations/${id}/test`);
      setTestResult(res.data);
    } catch (e) { setTestResult({ status: 'eroare', message: 'Eroare la testare' }); }
    setTesting(null);
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;
  const stats = dashboard?.stats || {};

  return (
    <div data-testid="admin-page" className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Administrare</h1>
        <p className="text-muted-foreground mt-1">Panou de administrare, integrări și audit</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: 'Utilizatori', value: stats.total_users, icon: Users, color: 'text-blue-600' },
          { label: 'Firme', value: stats.total_organizations, icon: Building2, color: 'text-green-600' },
          { label: 'Proiecte', value: stats.total_projects, icon: FolderKanban, color: 'text-purple-600' },
          { label: 'Documente', value: stats.total_documents, icon: FileText, color: 'text-amber-600' },
          { label: 'Specialiști', value: stats.total_specialists, icon: Shield, color: 'text-cyan-600' },
        ].map((s) => (
          <Card key={s.label} className="bg-card border-border">
            <CardContent className="p-5 flex items-center gap-3">
              <s.icon className={`w-5 h-5 ${s.color}`} />
              <div><p className="text-sm text-muted-foreground">{s.label}</p><p className="text-xl font-bold">{s.value || 0}</p></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="integrations" className="space-y-4">
        <TabsList className="bg-muted">
          <TabsTrigger value="integrations" data-testid="tab-integrations"><Plug className="w-4 h-4 mr-1.5" />Integrări API</TabsTrigger>
          <TabsTrigger value="audit" data-testid="tab-audit">Audit Log</TabsTrigger>
          <TabsTrigger value="users" data-testid="tab-users">Utilizatori</TabsTrigger>
        </TabsList>

        {/* INTEGRATIONS */}
        <TabsContent value="integrations" className="space-y-6">
          {Object.entries(integrations).map(([cat, items]) => {
            const CatIcon = CAT_ICONS[cat] || Plug;
            return (
              <div key={cat} className="space-y-3">
                <h3 className="font-heading text-lg font-bold flex items-center gap-2">
                  <CatIcon className="w-5 h-5 text-primary" />{CAT_LABELS[cat] || cat}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {items.map((integ) => (
                    <Card key={integ.id} className="bg-card border-border" data-testid={`integ-${integ.id}`}>
                      <CardContent className="p-5 space-y-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold text-[15px]">{integ.nume}</p>
                            <p className="text-sm text-muted-foreground mt-0.5">{integ.descriere}</p>
                          </div>
                          <Badge className={`rounded-full text-xs border flex-shrink-0 ml-3 ${STATUS_BADGE[integ.status] || STATUS_BADGE.neconfigurat}`}>
                            {integ.status === 'activ' && <CheckCircle className="w-3 h-3 mr-1" />}
                            {integ.status === 'mock' && <AlertTriangle className="w-3 h-3 mr-1" />}
                            {integ.status}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {integ.fields?.slice(0, 5).map((f, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">{f}</Badge>
                          ))}
                          {integ.fields?.length > 5 && <Badge variant="secondary" className="text-xs">+{integ.fields.length - 5}</Badge>}
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <Button size="sm" variant="outline" onClick={() => openConfig(integ)} data-testid={`config-${integ.id}`}>
                            <Settings className="w-3.5 h-3.5 mr-1.5" />Configurare
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => testIntegration(integ.id)} disabled={testing === integ.id} data-testid={`test-${integ.id}`}>
                            {testing === integ.id ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <TestTube className="w-3.5 h-3.5 mr-1.5" />}Test
                          </Button>
                          {integ.url_config && (
                            <a href={integ.url_config} target="_blank" rel="noopener noreferrer">
                              <Button size="sm" variant="ghost"><ExternalLink className="w-3.5 h-3.5" /></Button>
                            </a>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </TabsContent>

        {/* AUDIT */}
        <TabsContent value="audit" className="space-y-2">
          {auditLog.length === 0 ? <p className="text-muted-foreground">Nicio acțiune înregistrată</p> : auditLog.map((a) => (
            <Card key={a.id} className="bg-card border-border" data-testid={`audit-${a.id}`}>
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Activity className="w-4 h-4 text-primary" />
                  <div>
                    <p className="text-[15px] font-medium">{a.action}</p>
                    <p className="text-sm text-muted-foreground">{a.entity_type} &middot; {JSON.stringify(a.details || {}).slice(0, 80)}</p>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap">{new Date(a.timestamp).toLocaleString('ro-RO')}</span>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* USERS */}
        <TabsContent value="users" className="space-y-2">
          {users.map((u) => (
            <Card key={u.id} className="bg-card border-border" data-testid={`user-${u.id}`}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-[15px] font-medium">{u.prenume} {u.nume}</p>
                  <p className="text-sm text-muted-foreground">{u.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={`rounded-full text-sm ${u.is_active ? 'bg-green-500/15 text-green-600 border-green-500/20' : 'bg-red-500/15 text-red-500 border-red-500/20'}`}>
                    {u.is_active ? 'Activ' : 'Inactiv'}
                  </Badge>
                  {u.is_admin && <Badge className="bg-primary/15 text-primary border-primary/20 rounded-full text-sm">Admin</Badge>}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>

      {/* Config Dialog */}
      <Dialog open={configOpen} onOpenChange={setConfigOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plug className="w-5 h-5 text-primary" />Configurare {configTarget?.nume}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">{configTarget?.descriere}</p>
            <div className="space-y-2">
              <Label>API Key</Label>
              <Input type="password" value={configForm.api_key} onChange={(e) => setConfigForm({ ...configForm, api_key: e.target.value })} placeholder="Introduceți cheia API" data-testid="config-api-key" />
              <p className="text-xs text-muted-foreground">Variabilă ENV: {configTarget?.env_key}</p>
            </div>
            <div className="space-y-2">
              <Label>URL API</Label>
              <Input value={configForm.api_url} onChange={(e) => setConfigForm({ ...configForm, api_url: e.target.value })} data-testid="config-api-url" />
            </div>
            <div className="space-y-2">
              <Label>Note</Label>
              <Textarea value={configForm.notes} onChange={(e) => setConfigForm({ ...configForm, notes: e.target.value })} rows={2} placeholder="Observații..." data-testid="config-notes" />
            </div>
            {testResult && (
              <div className={`p-3 rounded-lg border text-sm ${testResult.status === 'ok' ? 'bg-green-500/5 border-green-500/20 text-green-700' : testResult.status === 'mock' ? 'bg-amber-500/5 border-amber-500/20 text-amber-700' : 'bg-red-500/5 border-red-500/20 text-red-700'}`} data-testid="test-result">
                {testResult.status === 'ok' && <CheckCircle className="w-4 h-4 inline mr-1.5" />}
                {testResult.status === 'eroare' && <XCircle className="w-4 h-4 inline mr-1.5" />}
                {testResult.status === 'mock' && <AlertTriangle className="w-4 h-4 inline mr-1.5" />}
                {testResult.message}
              </div>
            )}
            <div className="flex gap-2">
              <Button onClick={saveConfig} className="flex-1" data-testid="config-save-btn">Salvează configurarea</Button>
              <Button variant="outline" onClick={() => testIntegration(configTarget?.id)} disabled={testing} data-testid="config-test-btn">
                {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <TestTube className="w-4 h-4 mr-1" />}Test
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
