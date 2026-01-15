/**
 * Privacy Policy Page Component
 * Public page - displays privacy policy from database
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Home, Loader2 } from 'lucide-react';
import { API } from '../utils/constants';

const PrivacyPolicyPage = () => {
  const [content, setContent] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicy();
  }, []);

  const fetchPolicy = async () => {
    try {
      const res = await axios.get(`${API}/legal/privacy-policy`);
      setContent(res.data.content);
      setLastUpdated(res.data.last_updated);
    } catch (error) {
      setContent("Failed to load Privacy Policy. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-950">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <a href="/" className="text-pink-400 hover:text-pink-300 font-mono text-sm flex items-center gap-2 mb-4">
            <Home className="w-4 h-4" /> Back to Home
          </a>
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">PRIVACY POLICY</h1>
          <p className="text-purple-400/60 font-mono text-sm mt-2">Last Updated: {lastUpdated}</p>
        </div>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-pink-400 animate-spin" />
          </div>
        ) : (
          <div className="bg-slate-900/80 border border-purple-500/30 rounded-lg p-6 md:p-8">
            <div className="prose prose-invert prose-pink max-w-none font-mono text-purple-300/90 whitespace-pre-wrap">
              {content}
            </div>
          </div>
        )}
        
        <div className="mt-8 text-center">
          <p className="text-purple-400/40 font-mono text-xs">InfoPilot Explorer © 2026</p>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicyPage;
