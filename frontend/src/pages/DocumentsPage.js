import { useState, useEffect, useRef } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { FileText, Upload, Filter, Eye, Clock, FileUp, Scan, CheckCircle, AlertTriangle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

const TYPE_LABELS = {
  cerere_finantare: 'Cerere finanțare', memoriu: 'Memoriu', declaratie: 'Declarație',
  contract: 'Contract', factura: 'Factură', dovada_plata: 'Dovadă plată',
  proces_verbal: 'Proces verbal', ci: 'CI', bilant: 'Bilanț', balanta: 'Balanță',
  autorizatie: 'Autorizație', certificat: 'Certificat', oferta: 'Ofertă',
  cv: 'CV', imputernicire: 'Împuternicire', altele: 'Altele'
};

const STATUS_COLORS = {
  draft: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/20',
  de_semnat: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  semnat: 'bg-green-500/15 text-green-400 border-green-500/20',
  depus: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  aprobat: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
};

export function DocumentsPage() {
  const [docs, setDocs] = useState([]);
  const [orgs, setOrgs] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [filter, setFilter] = useState({ organizatie_id: '', tip: '', faza: '' });
  const [uploadForm, setUploadForm] = useState({ organizatie_id: '', project_id: '', tip: 'altele', faza: '', descriere: '' });
  const fileRef = useRef(null);

  const load = async () => {
    try {
      const params = {};
      if (filter.organizatie_id) params.organizatie_id = filter.organizatie_id;
      if (filter.tip) params.tip = filter.tip;
      if (filter.faza) params.faza = filter.faza;
      const [dRes, oRes, pRes] = await Promise.all([
        api.get('/documents', { params }),
        api.get('/organizations'),
        api.get('/projects')
      ]);
      setDocs(dRes.data || []);
      setOrgs(oRes.data || []);
      setProjects(pRes.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, [filter]);

  const handleUpload = async () => {
    if (!fileRef.current?.files[0] || !uploadForm.organizatie_id) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', fileRef.current.files[0]);
      fd.append('organizatie_id', uploadForm.organizatie_id);
      if (uploadForm.project_id) fd.append('project_id', uploadForm.project_id);
      fd.append('tip', uploadForm.tip);
      if (uploadForm.faza) fd.append('faza', uploadForm.faza);
      if (uploadForm.descriere) fd.append('descriere', uploadForm.descriere);
      await api.post('/documents/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      fileRef.current.value = '';
      load();
    } catch (e) { console.error(e); }
    setUploading(false);
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="documents-page" className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Documente</h1>
        <p className="text-muted-foreground mt-1">Biblioteca de documente cu versionare și taxonomie</p>
      </div>

      {/* Upload section */}
      <Card className="bg-card border-border">
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><Upload className="w-4 h-4" />Încarcă document</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Organizație *</Label>
              <Select value={uploadForm.organizatie_id} onValueChange={(v) => setUploadForm({ ...uploadForm, organizatie_id: v })}>
                <SelectTrigger data-testid="doc-org-select"><SelectValue placeholder="Selectează" /></SelectTrigger>
                <SelectContent>{orgs.map((o) => <SelectItem key={o.id} value={o.id}>{o.denumire}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Proiect</Label>
              <Select value={uploadForm.project_id} onValueChange={(v) => setUploadForm({ ...uploadForm, project_id: v })}>
                <SelectTrigger data-testid="doc-project-select"><SelectValue placeholder="Opțional" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Niciun proiect</SelectItem>
                  {projects.map((p) => <SelectItem key={p.id} value={p.id}>{p.titlu}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Tip document</Label>
              <Select value={uploadForm.tip} onValueChange={(v) => setUploadForm({ ...uploadForm, tip: v })}>
                <SelectTrigger data-testid="doc-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>{Object.entries(TYPE_LABELS).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Fază</Label>
              <Select value={uploadForm.faza} onValueChange={(v) => setUploadForm({ ...uploadForm, faza: v })}>
                <SelectTrigger data-testid="doc-phase-select"><SelectValue placeholder="Opțional" /></SelectTrigger>
                <SelectContent>
                  {['achizitii', 'depunere', 'contractare', 'implementare', 'clarificari'].map((f) => (
                    <SelectItem key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Input ref={fileRef} type="file" className="flex-1" data-testid="doc-file-input" />
            <Button onClick={handleUpload} disabled={uploading || !uploadForm.organizatie_id} data-testid="doc-upload-btn">
              <FileUp className="w-4 h-4 mr-2" />{uploading ? 'Se încarcă...' : 'Încarcă'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-muted-foreground"><Filter className="w-4 h-4" />Filtre:</div>
        <Select value={filter.organizatie_id} onValueChange={(v) => setFilter({ ...filter, organizatie_id: v === 'all' ? '' : v })}>
          <SelectTrigger className="w-48" data-testid="filter-org"><SelectValue placeholder="Toate organizațiile" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Toate organizațiile</SelectItem>
            {orgs.map((o) => <SelectItem key={o.id} value={o.id}>{o.denumire}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={filter.tip} onValueChange={(v) => setFilter({ ...filter, tip: v === 'all' ? '' : v })}>
          <SelectTrigger className="w-48" data-testid="filter-type"><SelectValue placeholder="Toate tipurile" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Toate tipurile</SelectItem>
            {Object.entries(TYPE_LABELS).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* Document list */}
      {docs.length === 0 ? (
        <Card className="bg-card border-border"><CardContent className="p-12 text-center">
          <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Niciun document</h3>
          <p className="text-muted-foreground">Încarcă primul document</p>
        </CardContent></Card>
      ) : (
        <div className="space-y-2">
          {docs.map((d) => (
            <Card key={d.id} className="bg-card border-border hover:border-primary/30 transition-colors duration-200" data-testid={`doc-item-${d.id}`}>
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <FileText className="w-8 h-8 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{d.filename}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                      <span>{TYPE_LABELS[d.tip] || d.tip}</span>
                      {d.faza && <span>&middot; {d.faza}</span>}
                      <span>&middot; v{d.versiune}</span>
                      <span>&middot; {(d.file_size / 1024).toFixed(0)} KB</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={`rounded-full px-2 py-0.5 text-xs border ${STATUS_COLORS[d.status] || STATUS_COLORS.draft}`}>
                    {d.status}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
