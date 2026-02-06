import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Bot, ArrowLeft, Mail, KeyRound, CheckCircle } from 'lucide-react';

export function ResetPasswordPage() {
  const [step, setStep] = useState('request'); // request | confirm | done
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [displayToken, setDisplayToken] = useState('');

  const handleRequest = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/reset-password', { email });
      if (res.data.reset_token) {
        setDisplayToken(res.data.reset_token);
        setResetToken(res.data.reset_token);
      }
      setStep('confirm');
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la trimiterea cererii');
    }
    setLoading(false);
  };

  const handleConfirm = async (e) => {
    e.preventDefault();
    setError('');
    if (newPassword !== confirmPassword) { setError('Parolele nu se potrivesc'); return; }
    if (newPassword.length < 6) { setError('Parola trebuie să aibă minim 6 caractere'); return; }
    setLoading(true);
    try {
      await api.post('/auth/reset-password/confirm', { token: resetToken, new_password: newPassword });
      setStep('done');
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la resetarea parolei');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-card border-border">
        <CardHeader className="space-y-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-xl font-bold">GrantFlow</span>
          </div>
          <CardTitle className="font-heading text-2xl font-bold">
            {step === 'request' && 'Resetare parolă'}
            {step === 'confirm' && 'Parolă nouă'}
            {step === 'done' && 'Parolă resetată'}
          </CardTitle>
          <CardDescription>
            {step === 'request' && 'Introduceți adresa de email asociată contului'}
            {step === 'confirm' && 'Introduceți token-ul și noua parolă'}
            {step === 'done' && 'Parola a fost schimbată cu succes'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === 'request' && (
            <form onSubmit={handleRequest} className="space-y-4">
              {error && <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm" data-testid="reset-error">{error}</div>}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="email@companie.ro" value={email} onChange={(e) => setEmail(e.target.value)} required data-testid="reset-email-input" />
              </div>
              <Button type="submit" className="w-full" disabled={loading} data-testid="reset-request-btn">
                <Mail className="w-4 h-4 mr-2" />{loading ? 'Se trimite...' : 'Trimite cerere de resetare'}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                <Link to="/login" className="text-primary hover:underline flex items-center justify-center gap-1">
                  <ArrowLeft className="w-3 h-3" />Înapoi la autentificare
                </Link>
              </p>
            </form>
          )}

          {step === 'confirm' && (
            <form onSubmit={handleConfirm} className="space-y-4">
              {error && <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm">{error}</div>}
              {displayToken && (
                <div className="p-3 rounded-md bg-primary/10 border border-primary/20 text-sm">
                  <p className="text-muted-foreground mb-1">Token de resetare (demo):</p>
                  <p className="font-mono text-xs break-all text-primary" data-testid="reset-token-display">{displayToken}</p>
                </div>
              )}
              <div className="space-y-2">
                <Label>Token de resetare</Label>
                <Input value={resetToken} onChange={(e) => setResetToken(e.target.value)} required data-testid="reset-token-input" placeholder="Introduceți token-ul" />
              </div>
              <div className="space-y-2">
                <Label>Parolă nouă</Label>
                <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required data-testid="reset-new-password" />
              </div>
              <div className="space-y-2">
                <Label>Confirmă parola nouă</Label>
                <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required data-testid="reset-confirm-password" />
              </div>
              <Button type="submit" className="w-full" disabled={loading} data-testid="reset-confirm-btn">
                <KeyRound className="w-4 h-4 mr-2" />{loading ? 'Se resetează...' : 'Resetează parola'}
              </Button>
            </form>
          )}

          {step === 'done' && (
            <div className="text-center space-y-4">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
              <p className="text-muted-foreground">Vă puteți autentifica cu noua parolă.</p>
              <Link to="/login">
                <Button className="w-full" data-testid="reset-to-login-btn">Mergi la autentificare</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
