import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { FirmProvider } from '@/contexts/FirmContext';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { OrganizationsPage } from '@/pages/OrganizationsPage';
import { OrganizationDetailPage } from '@/pages/OrganizationDetailPage';
import { ProjectsPage } from '@/pages/ProjectsPage';
import { ProjectDetailPage } from '@/pages/ProjectDetailPage';
import { DocumentsPage } from '@/pages/DocumentsPage';
import { CompliancePage } from '@/pages/CompliancePage';
import { MarketplacePage } from '@/pages/MarketplacePage';
import { AdminPage } from '@/pages/AdminPage';
import { ResetPasswordPage } from '@/pages/ResetPasswordPage';
import { VerifyEmailPage } from '@/pages/VerifyEmailPage';
import { ProjectWritingPage } from '@/pages/ProjectWritingPage';
import '@/App.css';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-background flex items-center justify-center text-muted-foreground">Se încarcă...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div>
          <Routes>
            <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
            <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
            <Route path="/reset-password" element={<PublicRoute><ResetPasswordPage /></PublicRoute>} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/" element={<ProtectedRoute><FirmProvider><AppLayout /></FirmProvider></ProtectedRoute>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="organizations" element={<OrganizationsPage />} />
              <Route path="organizations/:id" element={<OrganizationDetailPage />} />
              <Route path="projects" element={<ProjectsPage />} />
              <Route path="projects/:id" element={<ProjectDetailPage />} />
              <Route path="projects/:id/writing" element={<ProjectWritingPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="compliance" element={<CompliancePage />} />
              <Route path="marketplace" element={<MarketplacePage />} />
              <Route path="admin" element={<AdminPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
