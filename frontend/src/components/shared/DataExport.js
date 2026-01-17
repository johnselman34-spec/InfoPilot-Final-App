import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const DataExport = ({ showToast }) => {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportType, setExportType] = useState('all');
  const [format, setFormat] = useState('json');

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API}/export/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSummary(data.summary);
      }
    } catch (e) {
      console.error('Failed to fetch export summary:', e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    // Data fetch on mount
    let mounted = true;
    const loadSummary = async () => {
      if (mounted) await fetchSummary();
    };
    loadSummary();
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleExport = async () => {
    setExporting(true);
    try {
      let endpoint = `/export/${exportType}`;
      if (exportType !== 'all') {
        endpoint += `?format=${format}`;
      } else {
        endpoint += `?format=${format}`;
      }
      
      const res = await fetch(`${API}${endpoint}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from Content-Disposition header or create one
        const disposition = res.headers.get('Content-Disposition');
        let filename = `infopilot_export.${format}`;
        if (disposition) {
          const match = disposition.match(/filename=([^;]+)/);
          if (match) filename = match[1].trim();
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        showToast('Export downloaded successfully!', 'success');
      } else {
        showToast('Export failed. Please try again.', 'error');
      }
    } catch (e) {
      console.error('Export error:', e);
      showToast('Export failed. Please try again.', 'error');
    }
    setExporting(false);
  };

  if (loading) {
    return (
      <div className="bg-gray-900/50 border border-gray-700 rounded-xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-700 rounded w-1/3"></div>
          <div className="h-4 bg-gray-700 rounded w-2/3"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-20 bg-gray-700 rounded"></div>
            <div className="h-20 bg-gray-700 rounded"></div>
            <div className="h-20 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 border border-gray-700 rounded-xl p-6" data-testid="data-export-panel">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Export Your Data
      </h3>
      
      <p className="text-gray-400 text-sm mb-6">
        Download your InfoPilot data including categories, search results, protocols, and more.
      </p>

      {/* Data Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-purple-400">{summary.categories}</div>
            <div className="text-xs text-gray-500">Categories</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-400">{summary.search_results}</div>
            <div className="text-xs text-gray-500">Search Results</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-pink-400">{summary.protocol_templates}</div>
            <div className="text-xs text-gray-500">Templates</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-400">{summary.xp}</div>
            <div className="text-xs text-gray-500">XP Earned</div>
          </div>
        </div>
      )}

      {/* Export Options */}
      <div className="space-y-4">
        {/* Export Type */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">What to export</label>
          <select
            value={exportType}
            onChange={(e) => setExportType(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="all">All Data</option>
            <option value="categories">Categories Only</option>
            <option value="search-results">Search Results Only</option>
            <option value="protocols">Protocols Only</option>
          </select>
        </div>

        {/* Format */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">Format</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="format"
                value="json"
                checked={format === 'json'}
                onChange={(e) => setFormat(e.target.value)}
                className="text-purple-500 focus:ring-purple-500"
              />
              <span className="text-white">JSON</span>
              <span className="text-xs text-gray-500">(Detailed)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="format"
                value="csv"
                checked={format === 'csv'}
                onChange={(e) => setFormat(e.target.value)}
                className="text-purple-500 focus:ring-purple-500"
              />
              <span className="text-white">CSV</span>
              <span className="text-xs text-gray-500">(Spreadsheet)</span>
            </label>
          </div>
        </div>

        {/* Export Button */}
        <button
          onClick={handleExport}
          disabled={exporting}
          className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {exporting ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Preparing Export...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download Export
            </>
          )}
        </button>
      </div>

      {/* Privacy Note */}
      <p className="text-xs text-gray-500 mt-4 text-center">
        Your data is yours. Export includes all personal data stored in InfoPilot.
      </p>
    </div>
  );
};

export default DataExport;
