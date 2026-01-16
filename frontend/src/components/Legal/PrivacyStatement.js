/**
 * Privacy Statement Page
 * Privacy Policy for Top Pilot Enterprises, Inc.
 * Professional, comprehensive, GDPR/CCPA compliant
 */
import React from 'react';

const PrivacyStatement = ({ onClose, onAccept }) => {
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.9)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000,
      padding: 20,
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #1a1035, #2d1f4e)',
        borderRadius: 20,
        maxWidth: 800,
        width: '100%',
        maxHeight: '90vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        border: '2px solid rgba(124, 58, 237, 0.4)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #06b6d4, #0891b2)',
          padding: '20px 30px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <h2 style={{ color: '#fff', margin: 0, fontSize: '1.5rem' }}>
            🔒 Privacy Statement
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: 'none',
                color: '#fff',
                width: 36,
                height: 36,
                borderRadius: '50%',
                cursor: 'pointer',
                fontSize: '1.2rem',
              }}
            >
              ✕
            </button>
          )}
        </div>
        
        {/* Content */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: 30,
          color: '#e5e7eb',
          lineHeight: 1.7,
        }}>
          <div style={{ marginBottom: 30 }}>
            <h3 style={{ color: '#22d3ee', marginBottom: 10 }}>
              Top Pilot Enterprises, Inc. - Privacy Policy
            </h3>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
              Last Updated: December 2025 | Effective Date: Upon Registration
            </p>
          </div>
          
          <Section title="1. Introduction">
            <p>
              Top Pilot Enterprises, Inc. (&ldquo;Company&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;, &ldquo;our&rdquo;) respects your privacy 
              and is committed to protecting your personal data. This Privacy Statement explains 
              how we collect, use, disclose, and safeguard your information when you use 
              InfoPilot Explorer (&ldquo;the Service&rdquo;).
            </p>
          </Section>
          
          <Section title="2. Information We Collect">
            <p><strong>2.1 Information You Provide:</strong></p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Account information (name, email, password)</li>
              <li>Profile information (avatar, bio, preferences)</li>
              <li>Content you create (protocols, categories, reports)</li>
              <li>Communications (messages, support requests)</li>
              <li>Payment information (processed by PayPal)</li>
            </ul>
            
            <p><strong>2.2 Automatically Collected Information:</strong></p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Device information (browser type, operating system)</li>
              <li>Usage data (searches performed, pages visited)</li>
              <li>IP address and approximate location</li>
              <li>Cookies and similar tracking technologies</li>
              <li>Search queries and collation history</li>
            </ul>
            
            <p><strong>2.3 Third-Party Sources:</strong></p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Google OAuth (if used for login)</li>
              <li>Search engine APIs (Google, Bing, DuckDuckGo, Brave)</li>
              <li>PayPal (payment processing)</li>
            </ul>
          </Section>
          
          <Section title="3. How We Use Your Information">
            <p>We use collected information to:</p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Provide, maintain, and improve the Service</li>
              <li>Process transactions and send related information</li>
              <li>Send newsletters and promotional communications (opt-out available)</li>
              <li>Respond to your comments, questions, and requests</li>
              <li>Monitor and analyze usage trends and preferences</li>
              <li>Detect, prevent, and address technical issues and fraud</li>
              <li>Personalize your experience and provide recommendations</li>
              <li>Comply with legal obligations</li>
            </ul>
          </Section>
          
          <Section title="4. Information Sharing">
            <p>We may share your information with:</p>
            <ul style={{ paddingLeft: 25 }}>
              <li><strong>Service Providers:</strong> Third parties that help us operate the Service (hosting, analytics, payment processing)</li>
              <li><strong>Other Users:</strong> Public profile information, protocols you list for sale, and content you share in public areas</li>
              <li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
              <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
            </ul>
            
            <p><strong>We DO NOT:</strong></p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Sell your personal data to third parties</li>
              <li>Share your search history with advertisers</li>
              <li>Provide access to your private content without consent</li>
            </ul>
          </Section>
          
          <Section title="5. Data Security">
            <p>
              We implement appropriate security measures to protect your personal information, 
              including:
            </p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Encryption of data in transit (HTTPS/TLS)</li>
              <li>Secure password hashing (bcrypt)</li>
              <li>Access controls and authentication</li>
              <li>Regular security assessments</li>
              <li>Secure data storage practices</li>
            </ul>
            <p>
              However, no method of transmission over the Internet is 100% secure. While we 
              strive to protect your information, we cannot guarantee absolute security.
            </p>
          </Section>
          
          <Section title="6. Your Rights">
            <p>Depending on your location, you may have the right to:</p>
            <ul style={{ paddingLeft: 25 }}>
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Correction:</strong> Request correction of inaccurate data</li>
              <li><strong>Deletion:</strong> Request deletion of your data ("right to be forgotten")</li>
              <li><strong>Portability:</strong> Receive your data in a portable format</li>
              <li><strong>Object:</strong> Object to certain processing of your data</li>
              <li><strong>Withdraw Consent:</strong> Withdraw consent where processing is based on consent</li>
              <li><strong>Opt-Out:</strong> Unsubscribe from marketing communications</li>
            </ul>
            <p>
              To exercise these rights, contact us at privacy@toppilot.com or use the settings 
              in your account.
            </p>
          </Section>
          
          <Section title="7. Cookies and Tracking">
            <p>We use cookies and similar technologies to:</p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Keep you logged in</li>
              <li>Remember your preferences</li>
              <li>Analyze usage patterns</li>
              <li>Improve Service performance</li>
            </ul>
            <p>
              You can control cookies through your browser settings. Disabling cookies may 
              affect Service functionality.
            </p>
          </Section>
          
          <Section title="8. Data Retention">
            <p>
              We retain your personal data for as long as your account is active or as needed 
              to provide services. We may retain certain information for legal compliance, 
              dispute resolution, or enforcement purposes.
            </p>
            <p>
              Search history and analytics data may be retained in anonymized form for 
              statistical purposes.
            </p>
          </Section>
          
          <Section title="9. Children's Privacy">
            <p>
              The Service is not intended for children under 13. We do not knowingly collect 
              personal information from children under 13. If we become aware of such collection, 
              we will delete that information promptly.
            </p>
          </Section>
          
          <Section title="10. International Transfers">
            <p>
              Your information may be transferred to and processed in countries other than your 
              own. We take appropriate measures to ensure your data receives adequate protection 
              in accordance with this Privacy Statement.
            </p>
          </Section>
          
          <Section title="11. California Privacy Rights (CCPA)">
            <p>California residents have additional rights, including:</p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Right to know what personal information is collected</li>
              <li>Right to know if personal information is sold or disclosed</li>
              <li>Right to say no to the sale of personal information</li>
              <li>Right to equal service and price</li>
            </ul>
            <p>
              <strong>We do not sell personal information.</strong>
            </p>
          </Section>
          
          <Section title="12. European Privacy Rights (GDPR)">
            <p>
              If you are in the European Economic Area (EEA), you have rights under the General 
              Data Protection Regulation (GDPR), including:
            </p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Right to access, rectify, or erase your data</li>
              <li>Right to restrict or object to processing</li>
              <li>Right to data portability</li>
              <li>Right to lodge a complaint with a supervisory authority</li>
            </ul>
          </Section>
          
          <Section title="13. Changes to This Policy">
            <p>
              We may update this Privacy Statement from time to time. We will notify you of 
              significant changes by posting a notice on the Service or by email.
            </p>
          </Section>
          
          <Section title="14. Contact Us">
            <p>
              For questions or concerns about this Privacy Statement:<br/>
              <strong>Top Pilot Enterprises, Inc.</strong><br/>
              Privacy Officer: privacy@toppilot.com<br/>
              Data Protection Inquiries: dpo@toppilot.com<br/>
              General Support: support@infopilot.com
            </p>
          </Section>
          
          <div style={{
            background: 'rgba(6, 182, 212, 0.2)',
            padding: 20,
            borderRadius: 12,
            marginTop: 30,
            border: '1px solid rgba(6, 182, 212, 0.3)',
          }}>
            <p style={{ margin: 0, fontSize: '0.95rem' }}>
              <strong style={{ color: '#22d3ee' }}>Your Privacy Matters to Us</strong><br/>
              We're committed to transparency and giving you control over your personal data. 
              If you have any questions about our privacy practices, please don't hesitate to 
              reach out.
            </p>
          </div>
        </div>
        
        {/* Footer */}
        {onAccept && (
          <div style={{
            padding: 20,
            borderTop: '1px solid rgba(6, 182, 212, 0.3)',
            display: 'flex',
            gap: 15,
            justifyContent: 'flex-end',
          }}>
            {onClose && (
              <button
                onClick={onClose}
                style={{
                  padding: '12px 25px',
                  background: 'rgba(255,255,255,0.1)',
                  color: '#a1a1aa',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontSize: '0.95rem',
                }}
              >
                Cancel
              </button>
            )}
            <button
              onClick={onAccept}
              style={{
                padding: '12px 30px',
                background: 'linear-gradient(135deg, #06b6d4, #0891b2)',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: '0.95rem',
                fontWeight: 600,
              }}
            >
              ✓ I Understand
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Reusable section component
const Section = ({ title, children }) => (
  <div style={{ marginBottom: 25 }}>
    <h4 style={{ color: '#67e8f9', marginBottom: 10, fontSize: '1.1rem' }}>
      {title}
    </h4>
    <div style={{ color: '#d1d5db' }}>{children}</div>
  </div>
);

export default PrivacyStatement;
