import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  const [mode, setMode] = useState('auto'); // 'auto' | 'manual'
  const [manualForm, setManualForm] = useState({ cui: '', denumire: '', forma_juridica: 'SRL', nr_reg_com: '', adresa: '', judet: '', telefon: '', data_infiintare: '' });
  const [manualFile, setManualFile] = useState(null);

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
    if (!manualFile) { setError('Încarcă documentul ONRC'); return; }
    if (!manualForm.cui || !manualForm.denumire) { setError('CUI și Denumire sunt obligatorii'); return; }
    setAdding(true);
    try {
      const fd = new FormData();
      fd.append('file', manualFile);
      Object.entries(manualForm).forEach(([k, v]) => { if (v) fd.append(k, v); });
      await api.post('/organizations/manual', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setManualForm({ cui: '', denumire: '', forma_juridica: 'SRL', nr_reg_com: '', adresa: '', judet: '', telefon: '', data_infiintare: '' });
      setManualFile(null);
      setOpen(false);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare');
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
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Adaugă firmă după CUI</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAdd} className="space-y-4">
              {error && <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm">{error}</div>}
              <div className="space-y-2">
                <Label>CUI (Cod Unic de Înregistrare)</Label>
                <Input placeholder="ex: 12345678" value={cui} onChange={(e) => setCui(e.target.value)} required data-testid="org-cui-input" />
                <p className="text-xs text-muted-foreground">Datele vor fi preluate automat din ONRC</p>
              </div>
              <Button type="submit" disabled={adding} className="w-full" data-testid="org-submit-btn">
                {adding ? 'Se preiau datele...' : 'Adaugă firma'}
              </Button>
            </form>
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
