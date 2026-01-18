/**
 * InfoPilot Explorer - Toast Context
 */
import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);
export const useToast = () => useContext(ToastContext);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  }, []);

  const removeToast = (id) => setToasts(prev => prev.filter(t => t.id !== id));

  const Icon = ({ type }) => {
    switch(type) {
      case "success": return <CheckCircle className="text-green-400" size={20} />;
      case "error": return <AlertCircle className="text-red-400" size={20} />;
      default: return <Info className="text-blue-400" size={20} />;
    }
  };

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast-${toast.type} flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg animate-slide-up min-w-[300px] bg-slate-800 border border-white/10`}>
            <Icon type={toast.type} />
            <span className="text-white flex-1">{toast.message}</span>
            <button onClick={() => removeToast(toast.id)} className="text-white/50 hover:text-white"><X size={16} /></button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export default ToastProvider;
