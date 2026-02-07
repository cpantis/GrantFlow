import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Plus, Building2, ArrowUpRight, Search, MapPin, Hash, Upload } from 'lucide-react';

export function OrganizationsPage() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cui, setCui] = useState('');
  const [adding, setAdding] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState('auto');
  const [onrcFile, setOnrcFile] = useState(null);
  const [ciFile, setCiFile] = useState(null);

  const load = async () => {
    try {
      const res = await api.get('/organizations');
      setOrgs(res.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    setAdding(true);
    try {
      await api.post('/organizations', { cui: cui.trim() });
      setCui('');
      setOpen(false);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare');
    }
    setAdding(false);
  };

  const handleManualAdd = async (e) => {
    e.preventDefault();
    setError('');
    if (!onrcFile) { setError('Încarcă documentul ONRC'); return; }
    if (!ciFile) { setError('Încarcă cartea de identitate (CI)'); return; }
    setAdding(true);
    try {
      const fd = new FormData();
      fd.append('onrc_file', onrcFile);
      fd.append('ci_file', ciFile);
      await api.post('/organizations/manual', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setOnrcFile(null);
      setCiFile(null);
      setOpen(false);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la procesare');
    }
    setAdding(false);
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="organizations-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight">Firme</h1>
          <p className="text-muted-foreground mt-1">Gestionează firmele înregistrate</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-org-btn"><Plus className="w-4 h-4 mr-2" />Adaugă firmă</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Adaugă firmă</DialogTitle>
            </DialogHeader>
            <div className="flex gap-2 mb-4">
              <Button variant={mode === 'auto' ? 'default' : 'outline'} size="sm" onClick={() => setMode('auto')} data-testid="mode-auto-btn">
                <Search className="w-4 h-4 mr-1.5" />Automat (CUI)
              </Button>
              <Button variant={mode === 'manual' ? 'default' : 'outline'} size="sm" onClick={() => setMode('manual')} data-testid="mode-manual-btn">
                <Upload className="w-4 h-4 mr-1.5" />Manual (Upload ONRC)
              </Button>
            </div>
            {error && <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm mb-3">{error}</div>}

            {mode === 'auto' ? (
              <form onSubmit={handleAdd} className="space-y-4">
                <div className="space-y-2">
                  <Label>CUI (Cod Unic de Înregistrare)</Label>
                  <Input placeholder="ex: 14399840" value={cui} onChange={(e) => setCui(e.target.value)} required data-testid="org-cui-input" />
                  <p className="text-xs text-muted-foreground">Datele vor fi preluate automat din ONRC via OpenAPI.ro</p>
                </div>
                <Button type="submit" disabled={adding} className="w-full" data-testid="org-submit-btn">
                  {adding ? 'Se preiau datele...' : 'Adaugă firma'}
                </Button>
              </form>
            ) : (
              <form onSubmit={handleManualAdd} className="space-y-4">
                <div className="p-3 rounded-md bg-primary/5 border border-primary/20 text-sm">
                  <p className="font-medium">Upload certificat constatator / document ONRC</p>
                  <p className="text-muted-foreground text-xs mt-1">Documentul va fi procesat OCR automat pentru extragerea datelor.</p>
                </div>
                <div className="space-y-2">
                  <Label>Document ONRC *</Label>
                  <Input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setManualFile(e.target.files[0])} data-testid="manual-file-input" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label className="text-sm">CUI *</Label>
                    <Input value={manualForm.cui} onChange={(e) => setManualForm({ ...manualForm, cui: e.target.value })} placeholder="ex: 14399840" required data-testid="manual-cui-input" />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm">Denumire firmă *</Label>
                    <Input value={manualForm.denumire} onChange={(e) => setManualForm({ ...manualForm, denumire: e.target.value })} placeholder="SC Exemplu SRL" required data-testid="manual-denumire-input" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label className="text-sm">Formă juridică</Label>
                    <Select value={manualForm.forma_juridica} onValueChange={(v) => setManualForm({ ...manualForm, forma_juridica: v })}>
                      <SelectTrigger data-testid="manual-forma-select"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {['SRL', 'SA', 'PFA', 'II', 'SCS', 'SNC', 'ONG'].map(f => <SelectItem key={f} value={f}>{f}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm">Nr. Reg. Comerțului</Label>
                    <Input value={manualForm.nr_reg_com} onChange={(e) => setManualForm({ ...manualForm, nr_reg_com: e.target.value })} placeholder="J40/123/2020" data-testid="manual-regcom-input" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm">Adresă sediu social</Label>
                  <Input value={manualForm.adresa} onChange={(e) => setManualForm({ ...manualForm, adresa: e.target.value })} placeholder="Str. Exemplu nr. 10, București" data-testid="manual-adresa-input" />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1.5">
                    <Label className="text-sm">Județ</Label>
                    <Input value={manualForm.judet} onChange={(e) => setManualForm({ ...manualForm, judet: e.target.value })} placeholder="București" data-testid="manual-judet-input" />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm">Telefon</Label>
                    <Input value={manualForm.telefon} onChange={(e) => setManualForm({ ...manualForm, telefon: e.target.value })} data-testid="manual-telefon-input" />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm">Data înființare</Label>
                    <Input type="date" value={manualForm.data_infiintare} onChange={(e) => setManualForm({ ...manualForm, data_infiintare: e.target.value })} data-testid="manual-data-input" />
                  </div>
                </div>
                <Button type="submit" disabled={adding} className="w-full" data-testid="manual-submit-btn">
                  {adding ? 'Se adaugă...' : 'Adaugă firma manual'}
                </Button>
              </form>
            )}
          </DialogContent>
        </Dialog>
      </div>

      {orgs.length === 0 ? (
        <Card className="bg-card border-border">
          <CardContent className="p-14 text-center">
            <Building2 className="w-14 h-14 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">Nicio firmă</h3>
            <p className="text-base text-muted-foreground mb-4">Adaugă prima firmă prin introducerea CUI-ului</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {orgs.map((org) => (
            <Link key={org.id} to={`/organizations/${org.id}`} data-testid={`org-item-${org.id}`}>
              <Card className="bg-card border-border hover:border-primary/50 transition-colors duration-300 h-full">
                <CardContent className="p-6 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="w-11 h-11 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-primary" />
                    </div>
                    <Badge className={`rounded-full px-3 py-1 text-sm font-medium border ${org.stare === 'ACTIVA' ? 'bg-green-500/15 text-green-600 border-green-500/20' : 'bg-red-500/15 text-red-500 border-red-500/20'}`}>
                      {org.stare}
                    </Badge>
                  </div>
                  <div>
                    <p className="font-semibold text-[15px]">{org.denumire}</p>
                    <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1"><Hash className="w-3.5 h-3.5" />{org.cui}</span>
                      <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{org.judet}</span>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {org.caen_principal?.descriere}
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-border">
                    <span className="text-sm text-muted-foreground">{org.forma_juridica} &middot; {org.nr_angajati} angajați</span>
                    <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
