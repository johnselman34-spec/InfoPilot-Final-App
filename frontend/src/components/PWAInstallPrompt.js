import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Download, X, Smartphone } from 'lucide-react';

// Check if installed synchronously
const checkIsInstalled = () => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(display-mode: standalone)').matches;
};

// Check if iOS
const checkIsIOS = () => {
  if (typeof navigator === 'undefined') return false;
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
};

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  
  // Initialize values synchronously
  const isInstalled = checkIsInstalled();
  const isIOS = checkIsIOS();

  useEffect(() => {
    // Skip if already installed
    if (isInstalled) return;

    // Listen for the beforeinstallprompt event
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Show prompt after a delay
      setTimeout(() => setShowPrompt(true), 3000);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // Check if dismissed recently
    const dismissed = localStorage.getItem('pwa-prompt-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed);
      // Don't show for 7 days after dismissal
      if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        return;
      }
    }

    // Show iOS prompt after delay
    if (isIOS) {
      setTimeout(() => setShowPrompt(true), 5000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, [isInstalled, isIOS]);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setShowPrompt(false);
    }
    
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
  };

  if (isInstalled || !showPrompt) return null;

  return (
    <div className="fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-80 z-50 animate-slide-up">
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border border-yellow-400/30 rounded-xl p-4 shadow-2xl">
        <button 
          onClick={handleDismiss}
          className="absolute top-2 right-2 text-white/50 hover:text-white"
          aria-label="Dismiss"
        >
          <X size={18} />
        </button>
        
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-yellow-400/20 flex items-center justify-center flex-shrink-0">
            <Smartphone className="text-yellow-400" size={24} />
          </div>
          
          <div className="flex-1">
            <h3 className="text-white font-semibold text-sm mb-1">
              Install InfoPilot
            </h3>
            <p className="text-white/60 text-xs mb-3">
              {isIOS 
                ? "Tap the share button, then 'Add to Home Screen'"
                : "Install our app for quick access and offline search"}
            </p>
            
            {!isIOS && deferredPrompt ? (
              <Button 
                onClick={handleInstall}
                className="btn-gold w-full text-sm py-2"
                data-testid="pwa-install-btn"
              >
                <Download size={16} className="mr-2" />
                Install App
              </Button>
            ) : isIOS ? (
              <div className="flex items-center gap-2 text-white/70 text-xs">
                <span>Tap</span>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L11 14.586V4a1 1 0 011-1z"/>
                </svg>
                <span>then &ldquo;Add to Home Screen&rdquo;</span>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PWAInstallPrompt;
