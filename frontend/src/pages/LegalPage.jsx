import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Globe, Shield, Scale } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LegalPage = ({ docType }) => {
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocument();
  }, [docType]);

  const fetchDocument = async () => {
    try {
      // Use axios directly without auth for public legal pages
      const response = await axios.get(`${API}/legal/${docType}`);
      setDocument(response.data);
    } catch (error) {
      console.error("Error fetching legal document:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FFFFF0] py-12 px-6" data-testid={`legal-${docType}`}>
      <div className="max-w-3xl mx-auto">
        <Link to="/" className="flex items-center gap-2 text-[#007AFF] mb-8 hover:underline">
          <Globe className="w-5 h-5" />
          Back to InfoPilot Explorer
        </Link>
        
        <Card className="glass-card">
          <CardContent className="p-8">
            <div className="flex items-center gap-3 mb-6">
              {docType === 'privacy-policy' ? (
                <Shield className="w-8 h-8 text-[#007AFF]" />
              ) : (
                <Scale className="w-8 h-8 text-[#007AFF]" />
              )}
              <div>
                <h1 className="text-3xl font-bold font-['Outfit']">{document?.title}</h1>
                <p className="text-sm text-gray-500">Last Updated: {document?.last_updated}</p>
              </div>
            </div>
            
            <div className="prose prose-slate max-w-none">
              {/* Render markdown-like content */}
              {document?.content?.split('\n').map((line, i) => {
                if (line.startsWith('# ')) {
                  return <h1 key={i} className="text-2xl font-bold mt-8 mb-4">{line.substring(2)}</h1>;
                } else if (line.startsWith('## ')) {
                  return <h2 key={i} className="text-xl font-semibold mt-6 mb-3">{line.substring(3)}</h2>;
                } else if (line.startsWith('### ')) {
                  return <h3 key={i} className="text-lg font-medium mt-4 mb-2">{line.substring(4)}</h3>;
                } else if (line.startsWith('- ')) {
                  return <li key={i} className="ml-4">{line.substring(2)}</li>;
                } else if (line.startsWith('**') && line.endsWith('**')) {
                  return <p key={i} className="font-bold">{line.slice(2, -2)}</p>;
                } else if (line.startsWith('*') && line.endsWith('*')) {
                  return <p key={i} className="italic text-gray-600">{line.slice(1, -1)}</p>;
                } else if (line.startsWith('---')) {
                  return <hr key={i} className="my-6 border-gray-200" />;
                } else if (line.trim() === '') {
                  return <br key={i} />;
                } else {
                  return <p key={i} className="my-2">{line}</p>;
                }
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LegalPage;
