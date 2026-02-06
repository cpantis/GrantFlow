import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Bot, ArrowRight } from 'lucide-react';

export function RegisterPage() {
  const [form, setForm] = useState({ email: '', password: '', confirm: '', nume: '', prenume: '', telefon: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm) { setError('Parolele nu se potrivesc'); return; }
    if (form.password.length < 6) { setError('Parola trebuie să aibă minim 6 caractere'); return; }
    setLoading(true);
    try {
      await register({ email: form.email, password: form.password, nume: form.nume, prenume: form.prenume, telefon: form.telefon || null });
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Eroare la înregistrare');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <Card className="w-full max-w-lg bg-card border-border">
        <CardHeader className="space-y-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-xl font-bold">GrantFlow</span>
          </div>
          <CardTitle className="font-heading text-2xl font-bold">Înregistrare cont nou</CardTitle>
          <CardDescription>Creați un cont pentru a accesa platforma</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm" data-testid="register-error">{error}</div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="prenume">Prenume</Label>
                <Input id="prenume" value={form.prenume} onChange={update('prenume')} required data-testid="register-prenume-input" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="nume">Nume</Label>
                <Input id="nume" value={form.nume} onChange={update('nume')} required data-testid="register-nume-input" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="email@companie.ro" value={form.email} onChange={update('email')} required data-testid="register-email-input" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="telefon">Telefon (opțional)</Label>
              <Input id="telefon" value={form.telefon} onChange={update('telefon')} data-testid="register-telefon-input" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="password">Parolă</Label>
                <Input id="password" type="password" value={form.password} onChange={update('password')} required data-testid="register-password-input" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm">Confirmă parola</Label>
                <Input id="confirm" type="password" value={form.confirm} onChange={update('confirm')} required data-testid="register-confirm-input" />
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={loading} data-testid="register-submit-btn">
              {loading ? 'Se creează contul...' : 'Creează cont'}
              {!loading && <ArrowRight className="ml-2 w-4 h-4" />}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Ai deja cont?{' '}
              <Link to="/login" className="text-primary hover:underline" data-testid="login-link">Autentificare</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
