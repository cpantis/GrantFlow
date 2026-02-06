import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

const FirmContext = createContext(null);

export function FirmProvider({ children }) {
  const [firms, setFirms] = useState([]);
  const [activeFirm, setActiveFirm] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadFirms = useCallback(async () => {
    try {
      const res = await api.get('/organizations');
      const list = res.data || [];
      setFirms(list);
      // Restore saved firm or pick first
      const savedId = localStorage.getItem('grantflow_active_firm');
      const saved = list.find(f => f.id === savedId);
      if (saved) {
        setActiveFirm(saved);
      } else if (list.length > 0) {
        setActiveFirm(list[0]);
        localStorage.setItem('grantflow_active_firm', list[0].id);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { loadFirms(); }, [loadFirms]);

  const selectFirm = useCallback((firm) => {
    setActiveFirm(firm);
    localStorage.setItem('grantflow_active_firm', firm.id);
  }, []);

  const refreshFirms = useCallback(async () => {
    setLoading(true);
    await loadFirms();
  }, [loadFirms]);

  return (
    <FirmContext.Provider value={{ firms, activeFirm, selectFirm, loading, refreshFirms }}>
      {children}
    </FirmContext.Provider>
  );
}

export function useFirm() {
  const ctx = useContext(FirmContext);
  if (!ctx) throw new Error('useFirm must be within FirmProvider');
  return ctx;
}
