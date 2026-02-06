import { useState, useEffect, useRef } from 'react';
import api from '@/lib/api';
import { useFirm } from '@/contexts/FirmContext';
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
  const [ocrOpen, setOcrOpen] = useState(false);
  const [ocrData, setOcrData] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [correcting, setCorrecting] = useState(null);
  const [correctedValue, setCorrectedValue] = useState('');
  const fileRef = useRef(null);
  const { activeFirm } = useFirm();

  const load = async () => {
    try {
      const params = {};
      // Always filter by active firm
      if (activeFirm) params.organizatie_id = activeFirm.id;
      if (filter.tip) params.tip = filter.tip;
      if (filter.faza) params.faza = filter.faza;
      const [dRes, oRes, pRes] = await Promise.all([
        api.get('/documents', { params }),
        api.get('/organizations'),
        api.get('/projects', { params: activeFirm ? { organizatie_id: activeFirm.id } : {} })
      ]);
      setDocs(dRes.data || []);
      setOrgs(oRes.data || []);
      setProjects(pRes.data || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { load(); }, [filter, activeFirm]);

  const handleUpload = async () => {
    const orgId = uploadForm.organizatie_id || activeFirm?.id;
    if (!fileRef.current?.files[0] || !orgId) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', fileRef.current.files[0]);
      fd.append('organizatie_id', uploadForm.organizatie_id || activeFirm?.id);
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

  const triggerOcr = async (docId) => {
    setOcrLoading(true);
    try {
      const res = await api.post(`/documents/${docId}/ocr`);
      setOcrData(res.data);
      setSelectedDoc(docId);
      setOcrOpen(true);
      load();
    } catch (e) { console.error(e); }
    setOcrLoading(false);
  };

  const viewOcr = async (docId) => {
    try {
      const res = await api.get(`/documents/${docId}/ocr`);
      setOcrData(res.data);
      setSelectedDoc(docId);
      setOcrOpen(true);
    } catch (e) { console.error(e); }
  };

  const submitCorrection = async () => {
    if (!correcting || !correctedValue.trim()) return;
    try {
      const res = await api.post(`/documents/${selectedDoc}/ocr/correct?field_name=${correcting}&corrected_value=${encodeURIComponent(correctedValue)}`);
      if (res.data.success) {
        setOcrData(res.data.ocr_data);
        setCorrecting(null);
        setCorrectedValue('');
        load();
      }
    } catch (e) { console.error(e); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="documents-page" className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Documente</h1>
        <p className="text-muted-foreground mt-1">
          {activeFirm ? <><span className="text-primary font-medium">{activeFirm.denumire}</span> &middot; CUI: {activeFirm.cui}</> : 'Selectează o firmă din meniul lateral'}
        </p>
      </div>

      {/* Upload section */}
      <Card className="bg-card border-border">
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><Upload className="w-4 h-4" />Încarcă document</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Firmă *</Label>
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
                    <p className="font-semibold text-[15px] truncate">{d.filename}</p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                      <span>{TYPE_LABELS[d.tip] || d.tip}</span>
                      {d.faza && <span>&middot; {d.faza}</span>}
                      <span>&middot; v{d.versiune}</span>
                      <span>&middot; {(d.file_size / 1024).toFixed(0)} KB</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {d.ocr_status === 'completed' && (
                    <Badge className="bg-green-500/15 text-green-400 border-green-500/20 rounded-full text-xs cursor-pointer" onClick={() => viewOcr(d.id)} data-testid={`ocr-view-${d.id}`}>
                      <CheckCircle className="w-3 h-3 mr-1" />OCR OK
                    </Badge>
                  )}
                  {d.ocr_status === 'needs_review' && (
                    <Badge className="bg-amber-500/15 text-amber-400 border-amber-500/20 rounded-full text-xs cursor-pointer" onClick={() => viewOcr(d.id)} data-testid={`ocr-review-${d.id}`}>
                      <AlertTriangle className="w-3 h-3 mr-1" />Revizuire OCR
                    </Badge>
                  )}
                  {d.ocr_status === 'pending' && (
                    <Button variant="ghost" size="sm" onClick={() => triggerOcr(d.id)} disabled={ocrLoading} data-testid={`ocr-trigger-${d.id}`}>
                      <Scan className="w-3 h-3 mr-1" />OCR
                    </Button>
                  )}
                  <Badge className={`rounded-full px-2 py-0.5 text-xs border ${STATUS_COLORS[d.status] || STATUS_COLORS.draft}`}>
                    {d.status}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* OCR Results Modal */}
      <Dialog open={ocrOpen} onOpenChange={setOcrOpen}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Scan className="w-5 h-5 text-primary" />Rezultate OCR
              {ocrData?.status && (
                <Badge className={`rounded-full text-xs ml-2 ${
                  ocrData.status === 'completed' ? 'bg-green-500/15 text-green-400 border-green-500/20' :
                  ocrData.status === 'needs_review' ? 'bg-amber-500/15 text-amber-400 border-amber-500/20' :
                  'bg-red-500/15 text-red-400 border-red-500/20'
                }`}>{ocrData.status}</Badge>
              )}
            </DialogTitle>
          </DialogHeader>
          {ocrData && ocrData.extracted_fields && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 text-sm">
                <span className="text-muted-foreground">Încredere generală:</span>
                <span className={`font-bold ${ocrData.overall_confidence >= 0.85 ? 'text-green-400' : ocrData.overall_confidence >= 0.7 ? 'text-amber-400' : 'text-red-400'}`}>
                  {(ocrData.overall_confidence * 100).toFixed(1)}%
                </span>
                {ocrData.needs_human_review && (
                  <Badge className="bg-amber-500/15 text-amber-400 border-amber-500/20 rounded-full text-xs">
                    <AlertTriangle className="w-3 h-3 mr-1" />Necesită revizuire
                  </Badge>
                )}
              </div>
              <div className="space-y-2">
                {Object.entries(ocrData.extracted_fields).map(([field, value]) => {
                  const confidence = ocrData.field_confidences?.[field] || 0;
                  const isLow = (ocrData.low_confidence_fields || []).includes(field);
                  return (
                    <div key={field} className={`p-3 rounded-md border ${isLow ? 'border-amber-500/30 bg-amber-500/5' : 'border-border bg-card'}`} data-testid={`ocr-field-${field}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider">{field.replace(/_/g, ' ')}</span>
                        <span className={`text-xs font-mono ${confidence >= 0.85 ? 'text-green-400' : confidence >= 0.7 ? 'text-amber-400' : 'text-red-400'}`}>
                          {(confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {correcting === field ? (
                        <div className="flex gap-2 mt-1">
                          <Input size="sm" value={correctedValue} onChange={(e) => setCorrectedValue(e.target.value)} className="h-8 text-sm" data-testid={`ocr-correct-input-${field}`} />
                          <Button size="sm" className="h-8" onClick={submitCorrection} data-testid={`ocr-correct-save-${field}`}>Salvează</Button>
                          <Button size="sm" variant="ghost" className="h-8" onClick={() => setCorrecting(null)}>Anulează</Button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{value}</span>
                          {isLow && (
                            <Button variant="ghost" size="sm" className="h-6 text-xs text-amber-400" onClick={() => { setCorrecting(field); setCorrectedValue(value); }} data-testid={`ocr-correct-btn-${field}`}>
                              Corectează
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="text-xs text-muted-foreground border-t border-border pt-3">
                Procesat: {ocrData.processed_at ? new Date(ocrData.processed_at).toLocaleString('ro-RO') : 'N/A'} &middot;
                Timp: {ocrData.processing_time_ms}ms &middot;
                Motor: {ocrData.engine}
              </div>
            </div>
          )}
          {ocrData && !ocrData.extracted_fields && (
            <p className="text-muted-foreground text-sm">{ocrData.message || 'Date OCR indisponibile'}</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
