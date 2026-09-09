import React from 'react';
import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom';
import { Home } from './pages/Home';
import { Report } from './pages/Report';
import { Dashboard } from './pages/Dashboard';
import { ExpertPortal } from './pages/ExpertPortal';
import { Community } from './pages/Community';
import { Leaderboard } from './pages/Leaderboard';
import { Login } from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Leaf, LogOut, User as UserIcon } from 'lucide-react';

import { Chatbot } from './components/Chatbot';

const NavigationBar: React.FC = () => {
  const { user, logout, isExpert } = useAuth();

  const activeClass = ({ isActive }: { isActive: boolean }) =>
    isActive
      ? 'text-emerald-600 font-bold border-b-2 border-emerald-600 pb-1'
      : 'text-gray-600 hover:text-emerald-600 font-medium transition-colors';

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2 font-black text-xl text-emerald-800">
            <span className="p-1.5 bg-emerald-100 text-emerald-700 rounded-xl">🌿</span>
            CropHealth<span className="text-emerald-500">AI</span>
          </Link>

          <div className="hidden md:flex items-center gap-6 text-sm">
            <NavLink to="/" className={activeClass}>
              Home
            </NavLink>
            <NavLink to="/report" className={activeClass}>
              Diagnose Leaf
            </NavLink>
            <NavLink to="/dashboard" className={activeClass}>
              Dashboard
            </NavLink>
            <NavLink to="/community" className={activeClass}>
              Community
            </NavLink>
            <NavLink to="/leaderboard" className={activeClass}>
              Leaderboard
            </NavLink>
            {isExpert && (
              <NavLink to="/expert" className={activeClass}>
                Expert Portal
              </NavLink>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <span className="text-xs bg-emerald-50 text-emerald-700 font-bold px-3 py-1 rounded-full border border-emerald-200">
                {user.points || 0} pts
              </span>
              <span className="text-xs font-semibold text-gray-700 hidden sm:inline">
                {user.name}
              </span>
              <button
                onClick={logout}
                title="Logout"
                className="p-2 text-gray-500 hover:text-red-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-colors shadow-sm"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

const Footer: React.FC = () => (
  <footer className="border-t border-gray-200 bg-white py-8 text-center text-xs text-gray-500 mt-16">
    <div className="max-w-7xl mx-auto px-4 flex flex-wrap justify-between items-center gap-4">
      <div className="flex items-center gap-2 font-bold text-gray-800">
        <span>🌿</span> CropHealthAI Sentinel Ecosystem
      </div>
      <div>
        Explainable AI • Microclimate Forecasting • Community Sentinel • Offline-First Field Sync
      </div>
      <div>© {new Date().getFullYear()} CropHealthAI. All rights reserved.</div>
    </div>
  </footer>
);

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col justify-between bg-slate-50 text-slate-900">
          <div>
            <NavigationBar />
            <main className="pt-4">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/report" element={<Report />} />
                <Route path="/community" element={<Community />} />
                <Route path="/expert" element={<ExpertPortal />} />
                <Route path="/leaderboard" element={<Leaderboard />} />
              </Routes>
            </main>
          </div>
          <Chatbot />
          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
