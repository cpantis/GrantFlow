import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Bot, Send, Shield, MessageSquare } from 'lucide-react';
import { AiMessage } from '@/components/shared/AiMessage';
import { useFirm } from '@/contexts/FirmContext';

export function CompliancePage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chatMsg, setChatMsg] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const { activeFirm } = useFirm();

  useEffect(() => {
    const load = async () => {
      try {
        const params = activeFirm ? `?organizatie_id=${activeFirm.id}` : '';
        const res = await api.get(`/projects${params}`);
        setProjects(res.data || []);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, []);

  const sendChat = async () => {
    if (!chatMsg.trim()) return;
    const msg = chatMsg;
    setChatHistory([...chatHistory, { role: 'user', text: msg }]);
    setChatMsg('');
    setChatLoading(true);
    try {
      const res = await api.post('/compliance/navigator', { message: msg });
      setChatHistory(h => [...h, { role: 'assistant', text: res.data.response }]);
    } catch (e) {
      setChatHistory(h => [...h, { role: 'assistant', text: 'Eroare la generarea răspunsului.' }]);
    }
    setChatLoading(false);
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="compliance-page" className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Conformitate & Eligibilitate</h1>
        <p className="text-muted-foreground mt-1">Verifică eligibilitatea și conformitatea proiectelor</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="font-heading text-lg font-bold flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />Proiecte - Stare conformitate
          </h2>
          {projects.length === 0 ? (
            <p className="text-sm text-muted-foreground">Niciun proiect disponibil</p>
          ) : (
            <div className="space-y-2">
              {projects.map((p) => (
                <Card key={p.id} className="bg-card border-border" data-testid={`compliance-project-${p.id}`}>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-sm">{p.titlu}</p>
                      <p className="text-xs text-muted-foreground">{p.program_finantare}</p>
                    </div>
                    <Badge className="rounded-full text-xs">{p.stare_label}</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        <div>
          <Card className="bg-card border-border">
            <CardHeader><CardTitle className="text-base flex items-center gap-2">
              <Bot className="w-5 h-5 text-purple-400" />Navigator AI
              <Badge className="bg-purple-500/15 text-purple-400 border-purple-500/20 rounded-full text-xs">GPT-5.2</Badge>
            </CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="max-h-[500px] overflow-y-auto space-y-4 min-h-[150px] scroll-smooth" data-testid="compliance-chat-history">
                {chatHistory.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-8">Întreabă despre eligibilitate, programe de finanțare, cerințe sau pașii de urmat.</p>
                )}
                {chatHistory.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {m.role === 'user' ? (
                      <div className="max-w-[75%] rounded-lg px-4 py-2.5 bg-primary text-primary-foreground text-sm">
                        {m.text}
                      </div>
                    ) : (
                      <div className="max-w-[90%] rounded-lg px-4 py-3 bg-secondary/50 border border-border">
                        <AiMessage text={m.text} />
                      </div>
                    )}
                  </div>
                ))}
                {chatLoading && <div className="flex justify-start"><div className="bg-muted rounded-lg px-3 py-2 text-sm animate-pulse">Se generează...</div></div>}
              </div>
              <div className="flex gap-2">
                <Input
                  value={chatMsg}
                  onChange={(e) => setChatMsg(e.target.value)}
                  placeholder="Întreabă navigatorul..."
                  onKeyDown={(e) => e.key === 'Enter' && sendChat()}
                  data-testid="compliance-chat-input"
                />
                <Button onClick={sendChat} disabled={chatLoading || !chatMsg.trim()} data-testid="compliance-chat-send">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
