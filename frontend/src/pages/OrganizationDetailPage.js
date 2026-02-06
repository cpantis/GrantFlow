import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Building2, Users, FileText, TrendingUp, RefreshCw, ArrowLeft, Shield, Calendar, MapPin, Hash, Briefcase } from 'lucide-react';

export function OrganizationDetailPage() {
  const { id } = useParams();
  const [org, setOrg] = useState(null);
  const [financial, setFinancial] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [oRes, fRes] = await Promise.all([
          api.get(`/organizations/${id}`),
          api.get(`/organizations/${id}/financial`).catch(() => ({ data: null }))
        ]);
        setOrg(oRes.data);
        if (fRes.data) setFinancial(fRes.data);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, [id]);

  const refreshOnrc = async () => {
    try { await api.post(`/organizations/${id}/refresh-onrc`); window.location.reload(); } catch (e) { console.error(e); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;
  if (!org) return <div className="text-center text-muted-foreground">Firma nu a fost găsită</div>;

  return (
    <div data-testid="org-detail-page" className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/organizations"><Button variant="ghost" size="icon" data-testid="back-to-orgs"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div className="flex-1">
          <h1 className="font-heading text-2xl font-bold tracking-tight">{org.denumire}</h1>
          <p className="text-muted-foreground text-sm">CUI: {org.cui} &middot; {org.nr_reg_com}</p>
        </div>
        <Button variant="outline" onClick={refreshOnrc} data-testid="refresh-onrc-btn"><RefreshCw className="w-4 h-4 mr-2" />Actualizare ONRC</Button>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList className="bg-muted">
          <TabsTrigger value="general" data-testid="tab-general">General</TabsTrigger>
          <TabsTrigger value="members" data-testid="tab-members">Membri</TabsTrigger>
          <TabsTrigger value="financial" data-testid="tab-financial">Financiar</TabsTrigger>
          <TabsTrigger value="caen" data-testid="tab-caen">CAEN</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-card border-border"><CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><Building2 className="w-4 h-4" />Forma juridică</div>
              <p className="font-medium">{org.forma_juridica}</p>
            </CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><MapPin className="w-4 h-4" />Adresă</div>
              <p className="font-medium text-sm">{org.adresa}</p>
            </CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><Calendar className="w-4 h-4" />Înființare</div>
              <p className="font-medium">{org.data_infiintare}</p>
            </CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><Users className="w-4 h-4" />Angajați</div>
              <p className="font-medium">{org.nr_angajati}</p>
            </CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><TrendingUp className="w-4 h-4" />Capital social</div>
              <p className="font-medium">{org.capital_social?.toLocaleString()} RON</p>
            </CardContent></Card>
            <Card className="bg-card border-border"><CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><Shield className="w-4 h-4" />Status</div>
              <Badge className="bg-green-500/15 text-green-400 border-green-500/20 rounded-full">{org.stare}</Badge>
            </CardContent></Card>
          </div>
          {org.certificat_constatator && (
            <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base">Certificat Constatator</CardTitle></CardHeader>
              <CardContent className="text-sm space-y-1">
                <p>Nr: {org.certificat_constatator.numar}</p>
                <p>Emis: {org.certificat_constatator.data_emitere}</p>
                <p>Valabil până: {org.certificat_constatator.valabil_pana}</p>
                <Badge className="bg-green-500/15 text-green-400 border-green-500/20 rounded-full mt-2">{org.certificat_constatator.status}</Badge>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="members" className="space-y-4">
          <h3 className="font-heading text-lg font-bold">Administratori (ONRC)</h3>
          <div className="space-y-2">
            {(org.administratori || []).map((a, i) => (
              <Card key={i} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                <div><p className="font-medium">{a.nume}</p><p className="text-xs text-muted-foreground">{a.functie} &middot; din {a.data_numire}</p></div>
                <Badge className="bg-primary/15 text-primary border-primary/20 rounded-full">ONRC</Badge>
              </CardContent></Card>
            ))}
          </div>
          <h3 className="font-heading text-lg font-bold mt-6">Asociați</h3>
          <div className="space-y-2">
            {(org.asociati || []).map((a, i) => (
              <Card key={i} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                <p className="font-medium">{a.nume}</p>
                <span className="text-sm text-muted-foreground">{a.procent}%</span>
              </CardContent></Card>
            ))}
          </div>
          <h3 className="font-heading text-lg font-bold mt-6">Membri platformă</h3>
          <div className="space-y-2">
            {(org.members || []).map((m, i) => (
              <Card key={i} className="bg-card border-border"><CardContent className="p-4 flex items-center justify-between">
                <p className="text-sm">{m.email}</p>
                <Badge className="rounded-full">{m.rol}</Badge>
              </CardContent></Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="financial" className="space-y-4">
          {financial?.financial_history?.map((f, i) => (
            <Card key={i} className="bg-card border-border"><CardHeader><CardTitle className="text-base">Anul {f.an}</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><p className="text-muted-foreground">Cifra afaceri</p><p className="font-medium">{f.cifra_afaceri?.toLocaleString()} RON</p></div>
                <div><p className="text-muted-foreground">Profit net</p><p className="font-medium">{f.profit_net?.toLocaleString()} RON</p></div>
                <div><p className="text-muted-foreground">Angajați</p><p className="font-medium">{f.numar_angajati}</p></div>
                <div><p className="text-muted-foreground">Active totale</p><p className="font-medium">{f.active_totale?.toLocaleString()} RON</p></div>
              </CardContent>
            </Card>
          ))}
          {financial?.obligatii_restante && (
            <Card className="bg-card border-border"><CardContent className="p-4 flex items-center gap-3">
              <Shield className={`w-5 h-5 ${financial.obligatii_restante.are_obligatii_restante ? 'text-red-400' : 'text-green-400'}`} />
              <span className="text-sm">{financial.obligatii_restante.are_obligatii_restante ? `Obligații restante: ${financial.obligatii_restante.suma_restanta?.toLocaleString()} RON` : 'Fără obligații restante la ANAF'}</span>
            </CardContent></Card>
          )}
        </TabsContent>

        <TabsContent value="caen" className="space-y-4">
          <Card className="bg-card border-border"><CardHeader><CardTitle className="text-base">CAEN Principal</CardTitle></CardHeader>
            <CardContent><p className="text-sm"><span className="font-mono text-primary">{org.caen_principal?.cod}</span> &mdash; {org.caen_principal?.descriere}</p></CardContent>
          </Card>
          <h3 className="font-heading text-lg font-bold">CAEN Secundare</h3>
          <div className="space-y-2">
            {(org.caen_secundare || []).map((c, i) => (
              <Card key={i} className="bg-card border-border"><CardContent className="p-3 text-sm">
                <span className="font-mono text-primary">{c.cod}</span> &mdash; {c.descriere}
              </CardContent></Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
