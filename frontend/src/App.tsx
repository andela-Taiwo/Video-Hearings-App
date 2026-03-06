
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { HearingsPage } from './pages/HearingsPage.tsx';
import { HearingDetailPage } from './pages/HearingDetailPage.tsx';
import { EditHearingPage } from './pages/EditHearingPage.tsx';
import { Layout } from './components/layout/Layout.tsx';
import { Toast } from './components/common/Toast.tsx';
import { useToast } from './hooks/useToast.ts';

function App() {
  const { toasts, removeToast } = useToast();

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/hearings" replace />} />
          <Route path="/hearings" element={<HearingsPage />} />
          <Route path="/hearings/:id" element={<HearingDetailPage />} />
          <Route path="/hearings/:id/edit" element={<EditHearingPage />} />
          <Route path="*" element={<Navigate to="/hearings" replace />} />
        </Routes>
      </Layout>

      {/* Toast Notifications */}
      <div className="fixed bottom-0 right-0 z-50 m-4 space-y-2">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </Router>
  );
}

export default App;