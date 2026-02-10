import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Zap, Database, Scan, ShieldCheck, PenTool, CheckCircle,
  ClipboardCheck, MessageCircle, Plus, X, Bot
} from 'lucide-react';

const ICON_MAP = {
  zap: Zap, database: Database, scan: Scan, 'shield-check': ShieldCheck,
  'pen-tool': PenTool, 'check-circle': CheckCircle,
  'clipboard-check': ClipboardCheck, 'message-circle': MessageCircle
};

const TYPE_COLORS = {
  coordonare: 'bg-purple-500/10 text-purple-600 border-purple-500/20',
  date: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  procesare: 'bg-cyan-500/10 text-cyan-600 border-cyan-500/20',
  verificare: 'bg-green-500/10 text-green-600 border-green-500/20',
  generare: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  asistenta: 'bg-pink-500/10 text-pink-600 border-pink-500/20',
};

export function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newRules, setNewRules] = useState({});
  const [adding, setAdding] = useState(null);

  const load = async () => {
    try {
      const res = await api.get('/agents');
      setAgents(res.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const addRule = async (agentId) => {
    const rule = newRules[agentId]?.trim();
    if (!rule) return;
    setAdding(agentId);
    try {
      await api.post(`/agents/${agentId}/rules`, { regula: rule });
      setNewRules({ ...newRules, [agentId]: '' });
      load();
    } catch (e) { console.error(e); }
    setAdding(null);
  };

  const deleteRule = async (agentId, index) => {
    try {
      await api.delete(`/agents/${agentId}/rules/${index}`);
      load();
    } catch (e) { console.error(e); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="agents-page" className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
          <Bot className="w-8 h-8 text-primary" />Agenți AI
        </h1>
        <p className="text-muted-foreground mt-1">Configurează regulile fiecărui agent. Regulile custom se adaugă peste cele implicite.</p>
      </div>

      <div className="space-y-4">
        {agents.map((agent) => {
          const Icon = ICON_MAP[agent.icon] || Bot;
          const typeColor = TYPE_COLORS[agent.tip] || TYPE_COLORS.coordonare;
          return (
            <Card key={agent.id} className="bg-card border-border" data-testid={`agent-card-${agent.id}`}>
              <CardHeader className="pb-3">
                <div className="flex items-start gap-3">
                  <div className={`w-11 h-11 rounded-lg flex items-center justify-center flex-shrink-0 ${typeColor.split(' ')[0]}`}>
                    <Icon className={`w-5 h-5 ${typeColor.split(' ')[1]}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-lg flex items-center gap-2">
                      {agent.nume}
                      <Badge className={`rounded-full text-xs border ${typeColor}`}>{agent.tip}</Badge>
                    </CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">{agent.descriere}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Default rules */}
                <div>
                  <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2 font-medium">Reguli implicite</p>
                  <div className="space-y-1.5">
                    {agent.reguli_default?.map((r, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="w-3.5 h-3.5 mt-0.5 text-muted-foreground flex-shrink-0" />
                        <span className="text-muted-foreground">{r}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Custom rules */}
                <div>
                  <p className="text-xs uppercase tracking-wider text-primary mb-2 font-medium">Reguli custom</p>
                  {agent.reguli_custom?.length > 0 ? (
                    <div className="space-y-1.5">
                      {agent.reguli_custom.map((r, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm group" data-testid={`custom-rule-${agent.id}-${i}`}>
                          <div className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
                          <span className="flex-1 font-medium">{r}</span>
                          <button onClick={() => deleteRule(agent.id, i)} className="opacity-0 group-hover:opacity-100 transition-opacity" data-testid={`delete-rule-${agent.id}-${i}`}>
                            <X className="w-3.5 h-3.5 text-destructive" />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">Nicio regulă custom adăugată</p>
                  )}
                </div>

                {/* Add rule */}
                <div className="flex gap-2 pt-1">
                  <Input
                    value={newRules[agent.id] || ''}
                    onChange={(e) => setNewRules({ ...newRules, [agent.id]: e.target.value })}
                    placeholder="Adaugă o regulă nouă..."
                    className="text-sm"
                    onKeyDown={(e) => e.key === 'Enter' && addRule(agent.id)}
                    data-testid={`rule-input-${agent.id}`}
                  />
                  <Button size="sm" onClick={() => addRule(agent.id)} disabled={adding === agent.id || !newRules[agent.id]?.trim()} data-testid={`add-rule-${agent.id}`}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
