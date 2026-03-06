import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-900 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 6h18M3 10h18M5 6V4h14v2M5 20h14a2 2 0 002-2V10H3v8a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-lg font-semibold text-white tracking-tight">Court Hearings</h1>
            </div>
          </div>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  );
};