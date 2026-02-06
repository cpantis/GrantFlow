import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Users, Plus, Star, Clock, Briefcase, CheckCircle } from 'lucide-react';

export function MarketplacePage() {
  const [specialists, setSpecialists] = useState([]);
  const [myProfile, setMyProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ specializare: '', descriere: '', experienta_ani: '', competente: '', tarif_orar: '' });

  const load = async () => {
    try {
      const [sRes, pRes] = await Promise.all([
        api.get('/marketplace/specialists'),
        api.get('/marketplace/profile/me').catch(() => ({ data: null }))
      ]);
      setSpecialists(sRes.data || []);
      setMyProfile(pRes.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.post('/marketplace/profile', {
        ...form,
        experienta_ani: parseInt(form.experienta_ani) || 0,
        competente: form.competente.split(',').map(c => c.trim()).filter(Boolean),
        tarif_orar: parseFloat(form.tarif_orar) || null
      });
      setOpen(false);
      load();
    } catch (e) { console.error(e); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="marketplace-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight">Marketplace Specialiști</h1>
          <p className="text-muted-foreground mt-1">Găsește consultanți și experți pentru proiectele tale</p>
        </div>
        {!myProfile && (
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button data-testid="create-profile-btn"><Plus className="w-4 h-4 mr-2" />Devino specialist</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Creează profil specialist</DialogTitle></DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2"><Label>Specializare</Label>
                  <Input value={form.specializare} onChange={(e) => setForm({ ...form, specializare: e.target.value })} required data-testid="spec-specializare" placeholder="ex: Fonduri europene" /></div>
                <div className="space-y-2"><Label>Descriere</Label>
                  <Textarea value={form.descriere} onChange={(e) => setForm({ ...form, descriere: e.target.value })} required data-testid="spec-descriere" rows={3} /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2"><Label>Experiență (ani)</Label>
                    <Input type="number" value={form.experienta_ani} onChange={(e) => setForm({ ...form, experienta_ani: e.target.value })} data-testid="spec-experienta" /></div>
                  <div className="space-y-2"><Label>Tarif orar (RON)</Label>
                    <Input type="number" value={form.tarif_orar} onChange={(e) => setForm({ ...form, tarif_orar: e.target.value })} data-testid="spec-tarif" /></div>
                </div>
                <div className="space-y-2"><Label>Competențe (separate prin virgulă)</Label>
                  <Input value={form.competente} onChange={(e) => setForm({ ...form, competente: e.target.value })} data-testid="spec-competente" placeholder="PNRR, POR, Achiziții publice" /></div>
                <Button type="submit" className="w-full" data-testid="spec-submit-btn">Creează profil</Button>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {specialists.length === 0 ? (
        <Card className="bg-card border-border"><CardContent className="p-12 text-center">
          <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Niciun specialist disponibil</h3>
          <p className="text-muted-foreground">Fii primul specialist înregistrat pe platformă</p>
        </CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {specialists.map((s) => (
            <Card key={s.id} className="bg-card border-border hover:border-primary/50 transition-colors duration-300" data-testid={`specialist-${s.id}`}>
              <CardContent className="p-6 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-[15px]">{s.prenume} {s.nume}</p>
                    <p className="text-base text-primary">{s.specializare}</p>
                  </div>
                  <Badge className={`rounded-full text-xs ${s.disponibilitate === 'disponibil' ? 'bg-green-500/15 text-green-400 border-green-500/20' : 'bg-amber-500/15 text-amber-400 border-amber-500/20'}`}>
                    {s.disponibilitate}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2">{s.descriere}</p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><Briefcase className="w-3 h-3" />{s.experienta_ani} ani</span>
                  {s.tarif_orar && <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{s.tarif_orar} RON/oră</span>}
                  <span className="flex items-center gap-1"><CheckCircle className="w-3 h-3" />{s.proiecte_finalizate} proiecte</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {(s.competente || []).slice(0, 4).map((c, i) => (
                    <Badge key={i} variant="secondary" className="text-xs rounded-full">{c}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
