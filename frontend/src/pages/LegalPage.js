/**
 * User Agreement and Privacy Statement
 * Top Pilot Enterprises, Inc.
 * Professional and comprehensive legal documents
 */
import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const LegalPage = ({ showToast }) => {
  const { isDarkMode } = useTheme();
  const [activeTab, setActiveTab] = useState('terms');
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  const accentColor = '#7c3aed';
  
  return (
    <div style={{ 
      maxWidth: 900, 
      margin: '0 auto', 
      padding: 20,
      background: bgColor,
      minHeight: '100vh'
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 30 }}>
        <h1 style={{ 
          color: '#f472b6', 
          fontSize: '2rem',
          marginBottom: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 10
        }}>
          ⚖️ Legal Documents
        </h1>
        <p style={{ color: mutedColor, fontSize: '0.9rem' }}>
          Top Pilot Enterprises, Inc. • Last Updated: January 2026
        </p>
      </div>
      
      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: 10, 
        marginBottom: 30,
        borderBottom: '2px solid rgba(124, 58, 237, 0.3)',
        paddingBottom: 15
      }}>
        {[
          { id: 'terms', label: '📜 Terms of Service' },
          { id: 'privacy', label: '🔒 Privacy Policy' },
          { id: 'acceptable', label: '✅ Acceptable Use' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: activeTab === tab.id 
                ? 'linear-gradient(135deg, #7c3aed, #ec4899)' 
                : 'transparent',
              border: activeTab === tab.id 
                ? 'none' 
                : '1px solid rgba(124, 58, 237, 0.3)',
              borderRadius: 10,
              padding: '12px 20px',
              color: activeTab === tab.id ? '#fff' : mutedColor,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            data-testid={`legal-tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Terms of Service */}
      {activeTab === 'terms' && (
        <div style={{ color: textColor, lineHeight: 1.8 }} data-testid="terms-content">
          <h2 style={{ color: accentColor }}>Terms of Service</h2>
          <p style={{ color: mutedColor, fontSize: '0.85rem' }}>
            Effective Date: January 1, 2026
          </p>
          
          <h3>1. Acceptance of Terms</h3>
          <p>
            By accessing or using InfoPilot Explorer ("the Service"), operated by Top Pilot Enterprises, Inc. 
            ("Company," "we," "us," or "our"), you agree to be bound by these Terms of Service. If you do not 
            agree to all terms, you may not use the Service.
          </p>
          
          <h3>2. Description of Service</h3>
          <p>
            InfoPilot Explorer is a comprehensive information exchange platform that provides:
          </p>
          <ul>
            <li>Advanced search protocol creation and management (InfoJet 2.0)</li>
            <li>Web content aggregation, categorization, and analysis</li>
            <li>Community marketplace for sharing and selling search protocols</li>
            <li>Social features including groups, messaging, and user profiles</li>
            <li>Interactive mapping and geolocation visualization</li>
            <li>Gamification features including Easter Eggs and achievements</li>
          </ul>
          
          <h3>3. User Accounts</h3>
          <p>
            3.1. You must provide accurate, complete registration information and maintain account security.<br/>
            3.2. You are responsible for all activities under your account.<br/>
            3.3. You must be at least 18 years old to create an account.<br/>
            3.4. Accounts may be terminated for violations of these Terms.
          </p>
          
          <h3>4. Subscription and Payment</h3>
          <p>
            4.1. The Service offers both free and premium features.<br/>
            4.2. Premium subscriptions are billed monthly at rates displayed at time of purchase.<br/>
            4.3. Protocol purchases are processed through PayPal with 15% commission to Top Pilot Enterprises.<br/>
            4.4. Minimum transaction amount is $1.00 per PayPal requirements.<br/>
            4.5. <strong>Pay-As-You-Go promotion is available while supplies last</strong> - we are testing our 
            business model sustainability. API subscriptions for Google Maps, AI search, and other services are 
            expensive to maintain.
          </p>
          
          <h3>5. User-Generated Content</h3>
          <p>
            5.1. You retain ownership of protocols and content you create.<br/>
            5.2. By posting content, you grant us a non-exclusive license to display and distribute it.<br/>
            5.3. You are responsible for ensuring your content does not infringe third-party rights.<br/>
            5.4. We reserve the right to remove content that violates these Terms.
          </p>
          
          <h3>6. Prohibited Activities</h3>
          <p>Users may not:</p>
          <ul>
            <li>Use the Service for illegal purposes</li>
            <li>Harass, abuse, or harm other users</li>
            <li>Post defamatory, obscene, or hateful content</li>
            <li>Attempt to gain unauthorized access to systems</li>
            <li>Use automated tools to scrape or collect data</li>
            <li>Resell or redistribute Service features without authorization</li>
            <li>Create multiple accounts to abuse free features</li>
          </ul>
          
          <h3>7. Intellectual Property</h3>
          <p>
            7.1. The Service, including its design, features, and technology, is owned by Top Pilot Enterprises.<br/>
            7.2. "InfoPilot Explorer" and "InfoJet 2.0" are trademarks of Top Pilot Enterprises, Inc.<br/>
            7.3. Search protocols created by users remain their intellectual property.
          </p>
          
          <h3>8. Disclaimers</h3>
          <p>
            THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND. WE DO NOT GUARANTEE 
            ACCURACY OF SEARCH RESULTS OR THIRD-PARTY CONTENT. USE AT YOUR OWN RISK.
          </p>
          
          <h3>9. Limitation of Liability</h3>
          <p>
            TOP PILOT ENTERPRISES SHALL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, OR 
            CONSEQUENTIAL DAMAGES ARISING FROM USE OF THE SERVICE.
          </p>
          
          <h3>10. Modifications</h3>
          <p>
            We reserve the right to modify these Terms at any time. Continued use after changes 
            constitutes acceptance.
          </p>
          
          <h3>11. Contact Information</h3>
          <p>
            Top Pilot Enterprises, Inc.<br/>
            Email: support@infopilotexplorer.biz<br/>
            Website: https://infopilotexplorer.biz
          </p>
        </div>
      )}
      
      {/* Privacy Policy */}
      {activeTab === 'privacy' && (
        <div style={{ color: textColor, lineHeight: 1.8 }} data-testid="privacy-content">
          <h2 style={{ color: accentColor }}>Privacy Policy</h2>
          <p style={{ color: mutedColor, fontSize: '0.85rem' }}>
            Effective Date: January 1, 2026
          </p>
          
          <h3>1. Information We Collect</h3>
          <p><strong>1.1 Personal Information:</strong></p>
          <ul>
            <li>Name, email address, and password (encrypted)</li>
            <li>Profile information (bio, avatar, location - optional)</li>
            <li>Payment information (processed securely through PayPal)</li>
          </ul>
          
          <p><strong>1.2 Usage Information:</strong></p>
          <ul>
            <li>Search queries and protocols created</li>
            <li>Categories and content preferences</li>
            <li>Interaction with features (gamification, Easter eggs)</li>
            <li>Device information and IP address</li>
          </ul>
          
          <h3>2. How We Use Information</h3>
          <ul>
            <li>Provide and improve the Service</li>
            <li>Process transactions and send confirmations</li>
            <li>Send newsletters (tri-weekly at 5:46 AM, 9:42 AM, and 4:20 PM)</li>
            <li>Respond to support requests</li>
            <li>Analyze usage patterns to enhance features</li>
            <li>Detect and prevent fraud or abuse</li>
          </ul>
          
          <h3>3. Information Sharing</h3>
          <p>We do not sell your personal information. We may share information:</p>
          <ul>
            <li>With service providers (PayPal, hosting services)</li>
            <li>When required by law or legal process</li>
            <li>To protect rights and safety of users</li>
            <li>In connection with business transfers</li>
          </ul>
          
          <h3>4. Data Security</h3>
          <p>
            We implement industry-standard security measures including encryption, secure 
            servers, and regular security audits. However, no system is completely secure.
          </p>
          
          <h3>5. Cookies and Tracking</h3>
          <p>
            We use cookies for authentication, preferences, and analytics. You can control 
            cookie settings in your browser.
          </p>
          
          <h3>6. Your Rights</h3>
          <p>You have the right to:</p>
          <ul>
            <li>Access your personal data</li>
            <li>Request correction of inaccurate data</li>
            <li>Request deletion of your account</li>
            <li>Opt-out of marketing communications</li>
            <li>Export your data</li>
          </ul>
          
          <h3>7. Content Filtering</h3>
          <p>
            Users may adjust content filtering preferences in Settings. Adult content is 
            filtered by default. Users must be 18+ to access unfiltered content.
          </p>
          
          <h3>8. Children's Privacy</h3>
          <p>
            The Service is not intended for users under 18. We do not knowingly collect 
            information from minors.
          </p>
          
          <h3>9. International Users</h3>
          <p>
            Data is processed in the United States. By using the Service, you consent to 
            transfer of data to the US.
          </p>
          
          <h3>10. Changes to Privacy Policy</h3>
          <p>
            We will notify users of material changes via email or Service notification.
          </p>
          
          <h3>11. Contact</h3>
          <p>
            For privacy inquiries: privacy@infopilotexplorer.biz
          </p>
        </div>
      )}
      
      {/* Acceptable Use Policy */}
      {activeTab === 'acceptable' && (
        <div style={{ color: textColor, lineHeight: 1.8 }} data-testid="acceptable-content">
          <h2 style={{ color: accentColor }}>Acceptable Use Policy</h2>
          <p style={{ color: mutedColor, fontSize: '0.85rem' }}>
            Effective Date: January 1, 2026
          </p>
          
          <h3>1. Community Standards</h3>
          <p>
            InfoPilot Explorer is committed to maintaining a respectful, productive community. 
            All users must adhere to these standards.
          </p>
          
          <h3>2. Permitted Uses</h3>
          <ul>
            <li>Creating and sharing search protocols</li>
            <li>Participating in groups and discussions</li>
            <li>Buying, selling, and trading protocols</li>
            <li>Creating personal reports and content</li>
            <li>Using maps and analytics features</li>
          </ul>
          
          <h3>3. Prohibited Content</h3>
          <ul>
            <li>Illegal content or promotion of illegal activities</li>
            <li>Harassment, threats, or hate speech</li>
            <li>Spam, phishing, or malware</li>
            <li>Impersonation of others</li>
            <li>Content that infringes intellectual property</li>
            <li>Explicit content outside designated areas (Content Filter must be disabled)</li>
          </ul>
          
          <h3>4. Protocol Guidelines</h3>
          <ul>
            <li>Protocols must have accurate descriptions</li>
            <li>Pricing must be fair and clearly stated</li>
            <li>Copied protocols must credit original creators</li>
            <li>Protocols cannot be used for illegal data collection</li>
          </ul>
          
          <h3>5. Group and Page Moderation</h3>
          <p>
            Page and Group creators may moderate their communities. They may boot, ban, or mute 
            users who violate community standards. Appeals can be made to support@infopilotexplorer.biz.
          </p>
          
          <h3>6. Admin Enforcement</h3>
          <p>
            Administrators have authority to:
          </p>
          <ul>
            <li>Remove content that violates these policies</li>
            <li>Suspend or terminate user accounts</li>
            <li>Ban users from groups, pages, maps, and marketplace</li>
            <li>Issue warnings with explanations</li>
          </ul>
          
          <h3>7. Reporting Violations</h3>
          <p>
            Report violations using the report feature on content or by emailing 
            abuse@infopilotexplorer.biz with details.
          </p>
          
          <h3>8. Consequences</h3>
          <ul>
            <li><strong>First offense:</strong> Warning and content removal</li>
            <li><strong>Second offense:</strong> Temporary suspension (7 days)</li>
            <li><strong>Third offense:</strong> Permanent ban</li>
            <li><strong>Severe violations:</strong> Immediate permanent ban</li>
          </ul>
          
          <h3>9. Appeals</h3>
          <p>
            Users may appeal enforcement actions within 30 days by emailing 
            appeals@infopilotexplorer.biz.
          </p>
          
          {/* Maintenance Cost Notice */}
          <div style={{
            marginTop: 30,
            padding: 20,
            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(239, 68, 68, 0.1))',
            borderRadius: 12,
            border: '1px solid rgba(245, 158, 11, 0.3)'
          }}>
            <h4 style={{ color: '#f59e0b', margin: '0 0 10px 0' }}>
              💰 Supporting InfoPilot Explorer
            </h4>
            <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>
              Maintaining an app this functional is expensive! Google Maps API keys, AI search 
              subscriptions (Brave, SerpAPI, DuckDuckGo), and server infrastructure costs add up. 
              Your subscriptions and protocol purchases help keep InfoPilot Explorer running. 
              Thank you for your support! 🙏
            </p>
          </div>
        </div>
      )}
      
      {/* Footer */}
      <div style={{
        marginTop: 40,
        padding: 20,
        borderTop: '1px solid rgba(124, 58, 237, 0.2)',
        textAlign: 'center'
      }}>
        <p style={{ color: mutedColor, fontSize: '0.85rem' }}>
          © 2026 Top Pilot Enterprises, Inc. All rights reserved.<br/>
          InfoPilot Explorer™ and InfoJet 2.0™ are trademarks of Top Pilot Enterprises, Inc.
        </p>
        <p style={{ color: mutedColor, fontSize: '0.75rem', marginTop: 10 }}>
          📚 Also by the founder: <a 
            href="https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J/" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: '#f472b6' }}
          >
            "Letters to Evelyn" by John Selman
          </a> - A 5-star memoir of survival, love, and redemption.
        </p>
      </div>
    </div>
  );
};

export default LegalPage;
