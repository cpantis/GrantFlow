import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import {
  Users, Building2, FolderKanban, FileText, Shield, Clock,
  Activity, BarChart3, TrendingUp
} from 'lucide-react';

export function AdminPage() {
  const [dashboard, setDashboard] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [dRes, aRes, uRes] = await Promise.all([
          api.get('/admin/dashboard'),
          api.get('/admin/audit-log'),
          api.get('/admin/users').catch(() => ({ data: [] }))
        ]);
        setDashboard(dRes.data);
        setAuditLog(aRes.data || []);
        setUsers(uRes.data || []);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, []);

  const toggleUser = async (userId) => {
    try {
      await api.put(`/admin/users/${userId}/toggle-active`);
      const res = await api.get('/admin/users');
      setUsers(res.data || []);
    } catch (e) { console.error(e); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  const stats = dashboard?.stats || {};

  return (
    <div data-testid="admin-page" className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Administrare</h1>
        <p className="text-muted-foreground mt-1">Panou de administrare și audit</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: 'Utilizatori', value: stats.total_users, icon: Users, color: 'text-blue-400' },
          { label: 'Organizații', value: stats.total_organizations, icon: Building2, color: 'text-green-400' },
          { label: 'Proiecte', value: stats.total_projects, icon: FolderKanban, color: 'text-purple-400' },
          { label: 'Documente', value: stats.total_documents, icon: FileText, color: 'text-amber-400' },
          { label: 'Specialiști', value: stats.total_specialists, icon: Shield, color: 'text-cyan-400' },
        ].map((s) => (
          <Card key={s.label} className="bg-card border-border">
            <CardContent className="p-4 flex items-center gap-3">
              <s.icon className={`w-5 h-5 ${s.color}`} />
              <div><p className="text-xs text-muted-foreground">{s.label}</p><p className="text-lg font-bold">{s.value || 0}</p></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="audit" className="space-y-4">
        <TabsList className="bg-muted">
          <TabsTrigger value="audit" data-testid="tab-audit">Audit Log</TabsTrigger>
          <TabsTrigger value="users" data-testid="tab-users">Utilizatori</TabsTrigger>
          <TabsTrigger value="states" data-testid="tab-states">Proiecte pe stări</TabsTrigger>
        </TabsList>

        <TabsContent value="audit" className="space-y-2">
          {auditLog.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nicio acțiune înregistrată</p>
          ) : (
            auditLog.map((a) => (
              <Card key={a.id} className="bg-card border-border" data-testid={`audit-${a.id}`}>
                <CardContent className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Activity className="w-4 h-4 text-primary" />
                    <div>
                      <p className="text-sm font-medium">{a.action}</p>
                      <p className="text-xs text-muted-foreground">{a.entity_type} &middot; {JSON.stringify(a.details || {}).slice(0, 80)}</p>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">{new Date(a.timestamp).toLocaleString('ro-RO')}</span>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="users" className="space-y-2">
          {users.map((u) => (
            <Card key={u.id} className="bg-card border-border" data-testid={`user-${u.id}`}>
              <CardContent className="p-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{u.prenume} {u.nume}</p>
                  <p className="text-xs text-muted-foreground">{u.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={`rounded-full text-xs ${u.is_active ? 'bg-green-500/15 text-green-400 border-green-500/20' : 'bg-red-500/15 text-red-400 border-red-500/20'}`}>
                    {u.is_active ? 'Activ' : 'Inactiv'}
                  </Badge>
                  {u.is_admin && <Badge className="bg-primary/15 text-primary border-primary/20 rounded-full text-xs">Admin</Badge>}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="states" className="space-y-2">
          {Object.entries(dashboard?.projects_by_state || {}).map(([state, count]) => (
            <Card key={state} className="bg-card border-border">
              <CardContent className="p-3 flex items-center justify-between">
                <span className="text-sm font-medium capitalize">{state.replace('_', ' ')}</span>
                <Badge variant="secondary" className="rounded-full">{count}</Badge>
              </CardContent>
            </Card>
          ))}
          {Object.keys(dashboard?.projects_by_state || {}).length === 0 && (
            <p className="text-sm text-muted-foreground">Niciun proiect</p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
