/**
 * Document Type Testing Component
 * Admin tool to test InfoJet 2.0 document classification protocols
 */
import React, { useState } from 'react';
import { API } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';

const DoctypeTestingTool = ({ showToast }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [testData, setTestData] = useState({
    title: '',
    content: '',
    url: ''
  });
  const [result, setResult] = useState(null);
  
  const runTest = async () => {
    if (!testData.title && !testData.content) {
      showToast?.('Please provide title and/or content to test', 'error');
      return;
    }
    
    setLoading(true);
    setResult(null);
    
    try {
      const res = await fetch(`${API}/admin/doctype-test`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(testData)
      });
      
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        showToast?.(`Classified as: ${data.classification}`, 'success');
      } else {
        const err = await res.json();
        showToast?.(err.detail || 'Test failed', 'error');
      }
    } catch (err) {
      console.error('Test failed:', err);
      showToast?.('Test failed', 'error');
    }
    
    setLoading(false);
  };
  
  const loadSample = (type) => {
    const samples = {
      phd: {
        title: "Dr. Smith's Research on Climate Change",
        content: "In this peer-reviewed study, Dr. John Smith, Ph.D., examines the impact of climate change on coastal ecosystems. The research, conducted at the University of Maine, found that there are significant changes in marine biodiversity. There is evidence that these kinds of environmental shifts may have long-term consequences. It is easily observable that more than 50% of species are affected. Dr. Smith's findings suggest that this kind of research is essential for policy-making. The study includes over 2000 words of detailed analysis from multiple Ph.D. researchers including D.Phil. candidates from Oxford University.",
        url: ""
      },
      informative: {
        title: "Understanding Modern Technology",
        content: "There are many types of technologies that may have significant impacts on our daily lives. These kinds of innovations are changing how we work. There is growing evidence that this type of automation is easily implemented. More than half of businesses report that it is beneficial. Less than 10% face significant challenges. It is important to note that these types of solutions are becoming standard.",
        url: ""
      },
      blog: {
        title: "My Blog Post About Cooking",
        content: "Welcome to my cooking blog! In this blog post, I'll share my favorite recipes. This blog started as a hobby, but now my blog has thousands of readers. Check out my other blog entries for more recipes!",
        url: "https://example.com/blog/cooking"
      },
      forum: {
        title: "Forum Discussion: Best Programming Languages",
        content: "Hey everyone! I wanted to start this forum thread to discuss the best programming languages for beginners. What do you all think?",
        url: "https://example.com/forum/programming"
      },
      personal: {
        title: "My Experience Moving to a New City",
        content: "I wanted to share my experience moving to Portland, Maine. When I first arrived, I was nervous about starting fresh. I didn't know anyone in town. I spent the first week exploring the neighborhood. I found a great coffee shop near my apartment. I joined a local hiking group. I made new friends through work. I discovered that the food scene is amazing. I fell in love with the coastal views. I now consider this my home. Looking back, I am so glad I made this move.",
        url: ""
      },
      news: {
        title: "Breaking News: Major Discovery",
        content: "In today's news story, scientists announced a major breakthrough. This news article covers the latest developments. The news report indicates significant progress. News outlets worldwide are covering this story.",
        url: "https://example.com/news/discovery"
      }
    };
    
    const sample = samples[type];
    if (sample) {
      setTestData(sample);
      setResult(null);
    }
  };
  
  return (
    <div data-testid="doctype-testing-tool">
      <div style={{
        background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(239, 68, 68, 0.1))',
        borderRadius: 15,
        padding: 20,
        marginBottom: 20,
        border: '1px solid rgba(251, 191, 36, 0.3)'
      }}>
        <h3 style={{ color: '#fbbf24', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
          🧪 Document Type Testing Tool
        </h3>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem', margin: 0 }}>
          Paste sample text to test how the InfoJet 2.0 protocols classify documents.
          This helps verify your protocols are working correctly before production use.
        </p>
      </div>
      
      {/* Sample Buttons */}
      <div style={{ marginBottom: 15 }}>
        <span style={{ color: '#a1a1aa', fontSize: '0.85rem', marginRight: 10 }}>Load Sample:</span>
        {[
          { key: 'phd', label: '🎓 PhD' },
          { key: 'informative', label: '📚 Informative' },
          { key: 'blog', label: '✍️ Blog' },
          { key: 'forum', label: '💬 Forum' },
          { key: 'personal', label: '👤 Personal' },
          { key: 'news', label: '📰 News' }
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => loadSample(key)}
            style={{
              background: 'rgba(124, 58, 237, 0.2)',
              border: '1px solid rgba(124, 58, 237, 0.3)',
              color: '#a78bfa',
              padding: '4px 10px',
              borderRadius: 6,
              marginRight: 6,
              marginBottom: 6,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            {label}
          </button>
        ))}
      </div>
      
      {/* Test Inputs */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 15, marginBottom: 20 }}>
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Title
          </label>
          <input
            type="text"
            className="input"
            placeholder="Enter document title..."
            value={testData.title}
            onChange={(e) => setTestData({ ...testData, title: e.target.value })}
          />
        </div>
        
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Content
          </label>
          <textarea
            className="input"
            rows={8}
            placeholder="Paste document content here..."
            value={testData.content}
            onChange={(e) => setTestData({ ...testData, content: e.target.value })}
            style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
            <span style={{ color: '#71717a', fontSize: '0.75rem' }}>
              {testData.content.length} characters • {testData.content.split(' ').filter(w => w).length} words
            </span>
          </div>
        </div>
        
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            URL (optional)
          </label>
          <input
            type="text"
            className="input"
            placeholder="https://example.com/article"
            value={testData.url}
            onChange={(e) => setTestData({ ...testData, url: e.target.value })}
          />
        </div>
        
        <button
          onClick={runTest}
          disabled={loading || (!testData.title && !testData.content)}
          className="btn btn-primary"
          style={{
            padding: 15,
            fontSize: '1rem',
            background: loading ? 'rgba(124, 58, 237, 0.3)' : 'linear-gradient(135deg, #fbbf24, #f59e0b)'
          }}
        >
          {loading ? '⏳ Analyzing...' : '🧪 Run Classification Test'}
        </button>
      </div>
      
      {/* Results */}
      {result && (
        <div style={{
          background: 'rgba(0,0,0,0.3)',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <h4 style={{ color: '#10b981', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
            Classification Result
          </h4>
          
          {/* Main Result */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.1))',
            borderRadius: 10,
            padding: 20,
            textAlign: 'center',
            marginBottom: 20
          }}>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem', margin: '0 0 5px 0' }}>Document Type:</p>
            <p style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
              {result.classification}
            </p>
          </div>
          
          {/* Analysis */}
          <div style={{ marginBottom: 15 }}>
            <h5 style={{ color: '#a78bfa', marginBottom: 10 }}>📊 Analysis</h5>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
              <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: 10, borderRadius: 8 }}>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>Word Count</div>
                <div style={{ color: '#fff', fontWeight: 600 }}>{result.analysis.word_count}</div>
              </div>
              <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: 10, borderRadius: 8 }}>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>Content Length</div>
                <div style={{ color: '#fff', fontWeight: 600 }}>{result.analysis.content_length} chars</div>
              </div>
              <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: 10, borderRadius: 8 }}>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>Title Provided</div>
                <div style={{ color: '#fff', fontWeight: 600 }}>{result.analysis.title_provided ? 'Yes' : 'No'}</div>
              </div>
              <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: 10, borderRadius: 8 }}>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>URL Provided</div>
                <div style={{ color: '#fff', fontWeight: 600 }}>{result.analysis.url_provided ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>
          
          {/* Protocol Matches */}
          <div>
            <h5 style={{ color: '#a78bfa', marginBottom: 10 }}>🔍 Protocol Matches</h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {result.protocol_matches.map((match, i) => (
                <div 
                  key={i}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: match.passed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    padding: '8px 12px',
                    borderRadius: 8,
                    border: `1px solid ${match.passed ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                  }}
                >
                  <span style={{ color: '#fff', fontSize: '0.9rem' }}>{match.type}</span>
                  <span style={{ 
                    color: match.passed ? '#10b981' : '#f87171',
                    fontSize: '0.85rem',
                    fontWeight: 600
                  }}>
                    {match.passed ? '✓ PASSED' : '✗ Not matched'}
                    {match.matches !== undefined && ` (${match.matches}/${match.required || '?'})`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DoctypeTestingTool;
