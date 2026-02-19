/**
 * useKeyboardShortcuts - Hook for power user keyboard navigation
 * Shortcuts:
 * - Ctrl+M: Toggle map
 * - Ctrl+D: Switch data sources
 * - Ctrl+A: Select all categories
 * - Ctrl+Shift+A: Deselect all categories
 * - Ctrl+F: Focus search input
 * - Ctrl+Enter: Execute search
 * - Escape: Close modals
 */
import { useEffect, useCallback } from 'react';

export const useKeyboardShortcuts = ({
  onToggleMap,
  onToggleDataSource,
  onSelectAllCategories,
  onDeselectAllCategories,
  onFocusSearch,
  onExecuteSearch,
  onCloseModal,
  enabled = true
}) => {
  const handleKeyDown = useCallback((e) => {
    if (!enabled) return;
    
    // Don't trigger shortcuts when typing in inputs (except for specific ones)
    const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);
    
    // Ctrl+M: Toggle map
    if (e.ctrlKey && e.key === 'm') {
      e.preventDefault();
      onToggleMap && onToggleMap();
      return;
    }
    
    // Ctrl+D: Switch data sources
    if (e.ctrlKey && e.key === 'd') {
      e.preventDefault();
      onToggleDataSource && onToggleDataSource();
      return;
    }
    
    // Ctrl+A: Select all (when not typing)
    if (e.ctrlKey && e.key === 'a' && !isTyping) {
      e.preventDefault();
      if (e.shiftKey) {
        onDeselectAllCategories && onDeselectAllCategories();
      } else {
        onSelectAllCategories && onSelectAllCategories();
      }
      return;
    }
    
    // Ctrl+F: Focus search
    if (e.ctrlKey && e.key === 'f') {
      e.preventDefault();
      onFocusSearch && onFocusSearch();
      return;
    }
    
    // Ctrl+Enter: Execute search
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      onExecuteSearch && onExecuteSearch();
      return;
    }
    
    // Escape: Close modal
    if (e.key === 'Escape') {
      onCloseModal && onCloseModal();
      return;
    }
  }, [enabled, onToggleMap, onToggleDataSource, onSelectAllCategories, 
      onDeselectAllCategories, onFocusSearch, onExecuteSearch, onCloseModal]);
  
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
};

// Keyboard shortcuts help display component
export const KeyboardShortcutsHelp = ({ onClose }) => {
  const shortcuts = [
    { keys: 'Ctrl + M', action: 'Toggle map view' },
    { keys: 'Ctrl + D', action: 'Switch data source (My Data / Worldwide)' },
    { keys: 'Ctrl + A', action: 'Select all categories' },
    { keys: 'Ctrl + Shift + A', action: 'Deselect all categories' },
    { keys: 'Ctrl + F', action: 'Focus search input' },
    { keys: 'Ctrl + Enter', action: 'Execute search' },
    { keys: 'Escape', action: 'Close modal / Cancel' },
  ];
  
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #1a1035, #2d1f4e)',
        borderRadius: 16,
        padding: 30,
        maxWidth: 450,
        border: '2px solid rgba(139, 92, 246, 0.4)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ color: '#a78bfa', margin: 0 }}>⌨️ Keyboard Shortcuts</h2>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.1)',
              border: 'none',
              color: '#a1a1aa',
              width: 32,
              height: 32,
              borderRadius: '50%',
              cursor: 'pointer',
              fontSize: '1.2rem'
            }}
          >
            ✕
          </button>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {shortcuts.map((shortcut, i) => (
            <div 
              key={i}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '10px 15px',
                background: 'rgba(0,0,0,0.2)',
                borderRadius: 8
              }}
            >
              <span style={{ color: '#d1d5db' }}>{shortcut.action}</span>
              <kbd style={{
                background: 'rgba(139, 92, 246, 0.3)',
                padding: '4px 10px',
                borderRadius: 6,
                color: '#c4b5fd',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                border: '1px solid rgba(139, 92, 246, 0.5)'
              }}>
                {shortcut.keys}
              </kbd>
            </div>
          ))}
        </div>
        
        <p style={{ color: '#71717a', fontSize: '0.8rem', marginTop: 20, textAlign: 'center' }}>
          Press <kbd style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: 4 }}>?</kbd> anytime to show this help
        </p>
      </div>
    </div>
  );
};

export default useKeyboardShortcuts;
