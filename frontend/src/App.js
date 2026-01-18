/**
 * InfoPilot Explorer - Main Application
 * Worldwide Information Exchange Database
 * First in Flight with Monetization of Searches! It's a Bear! 🐻
 * 
 * Top Pilot Enterprises, Inc.
 */
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';

// Contexts
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';

// Components
import Navbar from './components/Navbar';
import FloatingEasterEgg from './components/FloatingEasterEgg';

// Eagerly loaded pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';

// Lazy loaded pages for code splitting
const UltimateSearchPage = lazy(() => import('./pages/UltimateSearchPage'));
const MapPage = lazy(() => import('./pages/MapPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const GroupsPage = lazy(() => import('./pages/GroupsPage'));
const PagesPage = lazy(() => import('./pages/PagesPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const RevenuePage = lazy(() => import('./pages/RevenuePage'));
const MarketplacePage = lazy(() => import('./pages/MarketplacePage'));
const ThemesPage = lazy(() => import('./pages/ThemesPage'));
const TemplatesPage = lazy(() => import('./pages/TemplatesPage'));
const StatsPage = lazy(() => import('./pages/StatsPage'));
const BookPage = lazy(() => import('./pages/BookPage'));
const FoodPage = lazy(() => import('./pages/FoodPage'));
const InfoPilotPage = lazy(() => import('./pages/InfoPilotPage'));
// Old PayPal result pages (deprecated)
const MarketplaceSuccess = lazy(() => import('./pages/MarketplaceResultPages').then(m => ({ default: m.MarketplaceSuccess })));
const MarketplaceCancel = lazy(() => import('./pages/MarketplaceResultPages').then(m => ({ default: m.MarketplaceCancel })));
// New Stripe payment pages
const PaymentSuccess = lazy(() => import('./pages/PaymentPages').then(m => ({ default: m.PaymentSuccess })));
const PaymentCancel = lazy(() => import('./pages/PaymentPages').then(m => ({ default: m.PaymentCancel })));
const SubscriptionCheckout = lazy(() => import('./pages/PaymentPages').then(m => ({ default: m.SubscriptionCheckout })));
const SubscriptionDashboard = lazy(() => import('./pages/SubscriptionDashboard'));

// CSS
import './App.css';

// Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 }
  }
});

// Loading fallback
const PageLoader = () => (
  <div className="min-h-screen pt-24 flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
      <p className="text-white/60">Loading...</p>
    </div>
  </div>
);

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" />;
  return children;
};

// Main App Content
const AppContent = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      <Navbar />
      <FloatingEasterEgg />
      
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/book" element={<BookPage />} />
          <Route path="/food" element={<FoodPage />} />
          <Route path="/infopilot" element={<InfoPilotPage />} />
          
          {/* Protected Routes */}
          <Route path="/search" element={<ProtectedRoute><UltimateSearchPage /></ProtectedRoute>} />
          <Route path="/map" element={<ProtectedRoute><MapPage /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
          <Route path="/groups" element={<ProtectedRoute><GroupsPage /></ProtectedRoute>} />
          <Route path="/pages" element={<ProtectedRoute><PagesPage /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
          <Route path="/revenue" element={<ProtectedRoute><RevenuePage /></ProtectedRoute>} />
          <Route path="/marketplace" element={<ProtectedRoute><MarketplacePage /></ProtectedRoute>} />
          <Route path="/marketplace/success" element={<MarketplaceSuccess />} />
          <Route path="/marketplace/cancel" element={<MarketplaceCancel />} />
          <Route path="/themes" element={<ProtectedRoute><ThemesPage /></ProtectedRoute>} />
          <Route path="/templates" element={<ProtectedRoute><TemplatesPage /></ProtectedRoute>} />
          <Route path="/stats" element={<ProtectedRoute><StatsPage /></ProtectedRoute>} />
          
          {/* Stripe Payment Routes */}
          <Route path="/payment/success" element={<PaymentSuccess />} />
          <Route path="/payment/cancel" element={<PaymentCancel />} />
          <Route path="/subscribe" element={<ProtectedRoute><SubscriptionCheckout /></ProtectedRoute>} />
          <Route path="/subscription" element={<ProtectedRoute><SubscriptionDashboard /></ProtectedRoute>} />
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Suspense>
    </div>
  );
};

// Root App Component
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <AuthProvider>
            <ToastProvider>
              <AppContent />
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
