import { useState, useEffect, useRef } from 'react';
import api from '@/lib/api';
import { useFirm } from '@/contexts/FirmContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { FileText, Upload, Filter, FolderOpen, CheckCircle, AlertTriangle, Scan, X, Loader2, Download } from 'lucide-react';

export function DocumentsPage() {
  const { activeFirm } = useFirm();
  const [applications, setApplications] = useState([]);
  const [selectedApp, setSelectedApp] = useState('');
  const [appData, setAppData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);
  const [uploadFolder, setUploadFolder] = useState('depunere');

  useEffect(() => {
    const load = async () => {
      try {
        const params = activeFirm ? `?company_id=${activeFirm.id}` : '';
        const res = await api.get(`/v2/applications${params}`);
        setApplications(res.data || []);
        // Auto-select first
        if (res.data?.length > 0 && !selectedApp) {
          setSelectedApp(res.data[0].id);
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, [activeFirm]);

  useEffect(() => {
    if (!selectedApp) { setAppData(null); return; }
    const loadApp = async () => {
      try {
        const res = await api.get(`/v2/applications/${selectedApp}`);
        setAppData(res.data);
      } catch (e) { console.error(e); }
    };
    loadApp();
  }, [selectedApp]);

  const handleUpload = async () => {
    if (!fileRef.current?.files[0] || !selectedApp) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', fileRef.current.files[0]);
      fd.append('folder_group', uploadFolder);
      await api.post(`/v2/applications/${selectedApp}/documents`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      fileRef.current.value = '';
      // Reload app data
      const res = await api.get(`/v2/applications/${selectedApp}`);
      setAppData(res.data);
    } catch (e) { console.error(e); }
    setUploading(false);
  };

  const deleteDoc = async (docId) => {
    try {
      await api.delete(`/v2/applications/${selectedApp}/documents/${docId}`);
      const res = await api.get(`/v2/applications/${selectedApp}`);
      setAppData(res.data);
    } catch (e) { console.error(e); }
  };

  const docs = appData?.documents || [];
  const folders = appData?.folder_groups || [
    { key: 'achizitii', name: '01_Achiziții', order: 1 },
    { key: 'depunere', name: '02_Depunere', order: 2 },
    { key: 'contractare', name: '03_Contractare', order: 3 },
    { key: 'implementare', name: '04_Implementare', order: 4 },
  ];
  const reqDocs = appData?.required_documents || [];

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Se încarcă...</div>;

  return (
    <div data-testid="documents-page" className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Documente</h1>
        <p className="text-muted-foreground mt-1">
          {activeFirm ? <><span className="text-primary font-medium">{activeFirm.denumire}</span> &middot; CUI: {activeFirm.cui}</> : 'Selectează o firmă'}
        </p>
      </div>

      {/* Project selector */}
      <div className="flex items-center gap-4">
        <div className="flex-1 max-w-md space-y-1">
          <Label className="text-sm">Proiect (dosar)</Label>
          <Select value={selectedApp} onValueChange={setSelectedApp}>
            <SelectTrigger data-testid="select-app"><SelectValue placeholder="Selectează proiectul" /></SelectTrigger>
            <SelectContent>
              {applications.map(a => <SelectItem key={a.id} value={a.id}>{a.title} ({a.status_label})</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        {reqDocs.length > 0 && (
          <div className="text-sm text-muted-foreground">
            Checklist: <strong>{reqDocs.filter(r => r.status === 'uploaded').length}</strong>/{reqDocs.length} documente
          </div>
        )}
      </div>

      {!selectedApp ? (
        <Card className="bg-card border-border"><CardContent className="p-14 text-center">
          <FileText className="w-14 h-14 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">Selectează un proiect</h3>
          <p className="text-base text-muted-foreground">Documentele sunt organizate pe proiecte și foldere</p>
        </CardContent></Card>
      ) : (
        <>
          {/* Upload area */}
          <Card className="bg-card border-border">
            <CardContent className="p-5">
              <div className="flex items-end gap-4">
                <div className="flex-1 space-y-1">
                  <Label className="text-sm">Încarcă document</Label>
                  <Input ref={fileRef} type="file" data-testid="doc-file-input" />
                </div>
                <div className="w-48 space-y-1">
                  <Label className="text-sm">Folder</Label>
                  <Select value={uploadFolder} onValueChange={setUploadFolder}>
                    <SelectTrigger data-testid="doc-folder-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {folders.map(f => <SelectItem key={f.key} value={f.key}>{f.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleUpload} disabled={uploading} data-testid="doc-upload-btn">
                  {uploading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Se încarcă...</> : <><Upload className="w-4 h-4 mr-2" />Încarcă</>}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Folders with documents */}
          {folders.map(fg => {
            const folderDocs = docs.filter(d => d.folder_group === fg.key);
            return (
              <div key={fg.key} className="space-y-2">
                <h3 className="font-heading text-base font-bold flex items-center gap-2">
                  <FolderOpen className="w-4 h-4 text-primary" />{fg.name}
                  <Badge variant="secondary" className="text-xs">{folderDocs.length}</Badge>
                </h3>
                {folderDocs.length === 0 ? (
                  <p className="text-sm text-muted-foreground pl-6">Niciun document în acest folder</p>
                ) : (
                  <div className="space-y-1.5 pl-2">
                    {folderDocs.map(d => (
                      <Card key={d.id} className="bg-card border-border" data-testid={`doc-${d.id}`}>
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                              <span className="text-sm font-medium truncate">{d.filename}</span>
                              {d.tip_document && d.tip_document !== 'altele' && <Badge variant="secondary" className="text-xs">{d.tip_document}</Badge>}
                            </div>
                            <div className="flex items-center gap-2">
                              {d.ocr_status === 'completed' && <Badge className="text-xs rounded-full bg-green-50 text-green-600"><CheckCircle className="w-3 h-3 mr-1" />OCR</Badge>}
                              {d.ocr_status === 'needs_review' && <Badge className="text-xs rounded-full bg-amber-50 text-amber-600"><AlertTriangle className="w-3 h-3 mr-1" />Revizuire</Badge>}
                              {d.pdf_filename && <a href={`${process.env.REACT_APP_BACKEND_URL}/api/v2/drafts/download/${d.pdf_filename}`} target="_blank" rel="noopener noreferrer"><Button variant="ghost" size="sm" className="h-7 w-7 p-0"><Download className="w-3.5 h-3.5" /></Button></a>}
                              <Button variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10 h-7 w-7 p-0" onClick={() => deleteDoc(d.id)} data-testid={`del-${d.id}`}><X className="w-3.5 h-3.5" /></Button>
                            </div>
                          </div>
                          {d.ocr_data?.extracted_fields && Object.keys(d.ocr_data.extracted_fields).length > 0 && (
                            <div className="mt-2 pl-6 text-xs text-muted-foreground border-t pt-2 flex flex-wrap gap-x-4 gap-y-1">
                              {Object.entries(d.ocr_data.extracted_fields).slice(0, 5).map(([k, v]) => (
                                <span key={k}><strong>{k.replace(/_/g, ' ')}:</strong> {String(v).slice(0, 40)}</span>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
