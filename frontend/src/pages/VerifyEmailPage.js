import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Bot, CheckCircle, XCircle, Mail } from 'lucide-react';

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading | success | error | manual
  const [token, setToken] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const t = searchParams.get('token');
    if (t) {
      verify(t);
    } else {
      setStatus('manual');
    }
  }, [searchParams]);

  const verify = async (t) => {
    try {
      await api.post('/auth/verify-email', { token: t });
      setStatus('success');
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la verificare');
      setStatus('error');
    }
  };

  const handleManualVerify = async (e) => {
    e.preventDefault();
    if (!token.trim()) return;
    setStatus('loading');
    await verify(token.trim());
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-xl font-bold">GrantFlow</span>
          </div>
          <CardTitle className="font-heading text-2xl font-bold">Verificare email</CardTitle>
        </CardHeader>
        <CardContent>
          {status === 'loading' && <p className="text-muted-foreground text-center py-6">Se verifică...</p>}

          {status === 'success' && (
            <div className="text-center space-y-4" data-testid="verify-success">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
              <p className="font-medium">Email verificat cu succes!</p>
              <p className="text-muted-foreground text-sm">Contul dvs. a fost activat complet.</p>
              <Button onClick={() => navigate('/dashboard')} className="w-full" data-testid="verify-to-dashboard">
                Mergi la panou
              </Button>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center space-y-4" data-testid="verify-error">
              <XCircle className="w-12 h-12 text-red-400 mx-auto" />
              <p className="text-destructive">{error}</p>
              <Button variant="outline" onClick={() => setStatus('manual')} data-testid="verify-retry">
                Introduceți token manual
              </Button>
            </div>
          )}

          {status === 'manual' && (
            <form onSubmit={handleManualVerify} className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Introduceți token-ul de verificare primit pe email:</p>
                <Input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Token de verificare" data-testid="verify-token-input" />
              </div>
              <Button type="submit" className="w-full" data-testid="verify-submit-btn">
                <Mail className="w-4 h-4 mr-2" />Verifică email
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
