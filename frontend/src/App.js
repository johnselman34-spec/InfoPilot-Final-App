import React, { useState } from 'react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';
import './i18n'; // i18n multi-language support

// Import refactored modules
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider, useTheme, ThemeToggle } from './contexts/ThemeContext';
import { Toast, Sidebar, QuoteOfTheDay, BookPromoBanner } from './components/shared';
import { LaughProvider } from './components/Gamification/LaughOMeter';
import { FloatingEasterEggsController } from './components/Gamification/FloatingEasterEggs';
import { 
  LoginPage, 
  RegisterPage, 
  AuthCallback, 
  AdminPanel, 
  SettingsPage, 
  SubscribePage, 
  MessagesPage,
  UltimateSearchPage,
  SocialPage,
  MapPage,
  MarketplacePage,
  AchievementsPage,
  QuoteGalleryPage,
  AnalyticsPage
} from './pages';
import ChatPage from './pages/ChatPage';
import AdvancedAnalytics from './components/AdvancedAnalytics';
import StatisticsPage from './pages/StatisticsPage';
import TutorialsPage from './pages/TutorialsPage';
import PersonalReportsPage from './pages/PersonalReportsPage';
import PayPalWalletPage from './pages/PayPalWalletPage';

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// ==================== MAIN APP ====================
const MainApp = () => {
  const { user } = useAuth();
  const [currentPage, setCurrentPage] = useState('search');
  const [toast, setToast] = useState(null);

  const showToast = (message, type) => {
    setToast({ message, type });
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'admin':
        return user?.is_admin ? <AdminPanel showToast={showToast} /> : <UltimateSearchPage showToast={showToast} />;
      case 'analytics':
        return <AnalyticsPage showToast={showToast} />;
      case 'statistics':
        return <StatisticsPage showToast={showToast} />;
      case 'search':
        return <UltimateSearchPage showToast={showToast} />;
      case 'marketplace':
        return <MarketplacePage showToast={showToast} />;
      case 'achievements':
        return <AchievementsPage showToast={showToast} />;
      case 'social':
        return <SocialPage showToast={showToast} />;
      case 'map':
        return <MapPage showToast={showToast} setCurrentPage={setCurrentPage} />;
      case 'quotes':
        return <QuoteGalleryPage showToast={showToast} />;
      case 'messages':
        return <MessagesPage showToast={showToast} />;
      case 'chat':
        return <ChatPage showToast={showToast} />;
      case 'tutorials':
        return <TutorialsPage showToast={showToast} />;
      case 'settings':
        return <SettingsPage showToast={showToast} setCurrentPage={setCurrentPage} />;
      case 'subscribe':
        return <SubscribePage showToast={showToast} onBack={() => setCurrentPage('settings')} />;
      case 'personal-reports':
        return <PersonalReportsPage showToast={showToast} onBack={() => setCurrentPage('settings')} />;
      case 'wallet':
        return <PayPalWalletPage showToast={showToast} onBack={() => setCurrentPage('settings')} />;
      default:
        return <UltimateSearchPage showToast={showToast} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} showToast={showToast} />
      <main className="main-content pt-16 md:pt-0">
        {/* Book Promotion Banner - Always visible */}
        <BookPromoBanner />
        {/* Quote of the Day - Rotating manuscript quotes */}
        <QuoteOfTheDay />
        {renderPage()}
      </main>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
      {/* Floating Easter Eggs - Fun gamification feature! */}
      <FloatingEasterEggsController enabled={true} frequency={45000} />
    </div>
  );
};

// ==================== APP ROOT ====================
function App() {
  const [authMode, setAuthMode] = useState('login');

  return (
    <AuthProvider>
      <ThemeProvider>
        <LaughProvider>
          <AppContent authMode={authMode} setAuthMode={setAuthMode} />
        </LaughProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

const AppContent = ({ authMode, setAuthMode }) => {
  const { user, loading } = useAuth();

  // Check for session_id in URL hash (Google OAuth callback)
  if (window.location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  if (loading) {
    return (
      <div className="auth-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return authMode === 'login' 
      ? <LoginPage onSwitch={() => setAuthMode('register')} />
      : <RegisterPage onSwitch={() => setAuthMode('login')} />;
  }

  return <MainApp />;
};

export default App;
