/**
 * User Agreement Page
 * Terms and Conditions for Top Pilot Enterprises, Inc.
 * Professional, comprehensive, and legally sound
 */
import React from 'react';

const UserAgreement = ({ onClose, onAccept }) => {
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
          background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
          padding: '20px 30px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <h2 style={{ color: '#fff', margin: 0, fontSize: '1.5rem' }}>
            📜 User Agreement
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
            <h3 style={{ color: '#f472b6', marginBottom: 10 }}>
              Top Pilot Enterprises, Inc. - Terms of Service
            </h3>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
              Last Updated: December 2025 | Effective Date: Upon Registration
            </p>
          </div>
          
          <Section title="1. Acceptance of Terms">
            <p>
              By accessing and using InfoPilot Explorer ("the Service"), you accept and agree to be 
              bound by the terms and provisions of this agreement. If you do not agree to abide by 
              these terms, please do not use the Service.
            </p>
            <p>
              Top Pilot Enterprises, Inc. ("Company", "we", "us") reserves the right to modify 
              these terms at any time. Continued use of the Service after changes constitutes 
              acceptance of the new terms.
            </p>
          </Section>
          
          <Section title="2. Description of Service">
            <p>InfoPilot Explorer provides:</p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Advanced web search and content collation services</li>
              <li>Protocol-based categorization and organization tools</li>
              <li>Marketplace for buying and selling search protocols</li>
              <li>Social features including groups, messaging, and achievements</li>
              <li>Analytics and statistics on search patterns</li>
              <li>Map-based visualization of search results</li>
            </ul>
          </Section>
          
          <Section title="3. User Accounts">
            <p>
              <strong>3.1 Registration:</strong> You must provide accurate, current, and complete 
              information during registration. You are responsible for maintaining the confidentiality 
              of your account credentials.
            </p>
            <p>
              <strong>3.2 Account Security:</strong> You are responsible for all activities that 
              occur under your account. Notify us immediately of any unauthorized use.
            </p>
            <p>
              <strong>3.3 Age Requirement:</strong> You must be at least 13 years old to use this 
              Service. Users under 18 require parental consent.
            </p>
          </Section>
          
          <Section title="4. User Conduct">
            <p>You agree NOT to:</p>
            <ul style={{ paddingLeft: 25 }}>
              <li>Violate any applicable laws or regulations</li>
              <li>Infringe on intellectual property rights of others</li>
              <li>Upload malicious content, viruses, or harmful code</li>
              <li>Harass, abuse, or harm other users</li>
              <li>Attempt to gain unauthorized access to the Service</li>
              <li>Use the Service for spam or unsolicited communications</li>
              <li>Create fake accounts or misrepresent your identity</li>
              <li>Manipulate rankings, reviews, or marketplace listings</li>
              <li>Scrape or automate access to the Service without permission</li>
            </ul>
          </Section>
          
          <Section title="5. Marketplace Terms">
            <p>
              <strong>5.1 Protocol Sales:</strong> Users may list protocols for sale. The Company 
              retains a platform fee (percentage configurable by admin) from each sale.
            </p>
            <p>
              <strong>5.2 Pricing:</strong> Sellers set their own prices within platform guidelines. 
              Free protocols ($0.00) are permitted and encouraged for building reputation.
            </p>
            <p>
              <strong>5.3 Payouts:</strong> Earnings are paid via PayPal. Due to PayPal's minimum 
              transaction requirements ($1.00), earnings below this threshold are accumulated in 
              your wallet until the minimum is reached.
            </p>
            <p>
              <strong>5.4 Refunds:</strong> Digital products are generally non-refundable. Exceptions 
              may be made for technical issues at Company discretion.
            </p>
          </Section>
          
          <Section title="6. Content Ownership">
            <p>
              <strong>6.1 Your Content:</strong> You retain ownership of protocols, reports, and 
              content you create. By posting, you grant the Company a license to display and 
              distribute your content within the Service.
            </p>
            <p>
              <strong>6.2 Company Content:</strong> All Service features, design, logos, and 
              proprietary technology are owned by Top Pilot Enterprises, Inc.
            </p>
          </Section>
          
          <Section title="7. Privacy">
            <p>
              Your use of the Service is subject to our Privacy Statement. By using the Service, 
              you consent to the collection and use of information as described in our Privacy Policy.
            </p>
          </Section>
          
          <Section title="8. Subscription and Payments">
            <p>
              <strong>8.1 Free Tier:</strong> Basic features are available free of charge.
            </p>
            <p>
              <strong>8.2 Premium Features:</strong> Additional features may require payment or 
              subscription. Pricing is displayed before purchase.
            </p>
            <p>
              <strong>8.3 Pay-As-You-Go:</strong> The current promotional pricing model is subject 
              to change. The Company reserves the right to modify pricing structure with notice.
            </p>
          </Section>
          
          <Section title="9. Termination">
            <p>
              <strong>9.1 By User:</strong> You may terminate your account at any time through 
              account settings.
            </p>
            <p>
              <strong>9.2 By Company:</strong> We may suspend or terminate accounts that violate 
              these terms. Administrators may boot, ban, mute, or delete users with cause.
            </p>
            <p>
              <strong>9.3 Effect:</strong> Upon termination, your right to use the Service ceases 
              immediately. Certain provisions survive termination.
            </p>
          </Section>
          
          <Section title="10. Disclaimers">
            <p>
              THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND. WE DO NOT GUARANTEE 
              THE ACCURACY, COMPLETENESS, OR USEFULNESS OF ANY SEARCH RESULTS OR CONTENT.
            </p>
            <p>
              We are not responsible for third-party content, websites, or services linked through 
              search results.
            </p>
          </Section>
          
          <Section title="11. Limitation of Liability">
            <p>
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, TOP PILOT ENTERPRISES, INC. SHALL NOT BE 
              LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.
            </p>
          </Section>
          
          <Section title="12. Governing Law">
            <p>
              These terms shall be governed by the laws of the State of Maine, United States, 
              without regard to conflict of law principles.
            </p>
          </Section>
          
          <Section title="13. Contact Information">
            <p>
              For questions about these Terms, please contact:<br/>
              <strong>Top Pilot Enterprises, Inc.</strong><br/>
              Email: legal@toppilot.com<br/>
              Support: support@infopilot.com
            </p>
          </Section>
          
          <div style={{
            background: 'rgba(16, 185, 129, 0.2)',
            padding: 20,
            borderRadius: 12,
            marginTop: 30,
            border: '1px solid rgba(16, 185, 129, 0.3)',
          }}>
            <p style={{ margin: 0, fontSize: '0.95rem' }}>
              <strong style={{ color: '#10b981' }}>Thank you for using InfoPilot Explorer!</strong><br/>
              We're committed to providing you with an excellent search and research experience. 
              If you have any questions or concerns, don't hesitate to reach out.
            </p>
          </div>
        </div>
        
        {/* Footer */}
        {onAccept && (
          <div style={{
            padding: 20,
            borderTop: '1px solid rgba(124, 58, 237, 0.3)',
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
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: '0.95rem',
                fontWeight: 600,
              }}
            >
              ✓ I Accept the Terms
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
    <h4 style={{ color: '#a78bfa', marginBottom: 10, fontSize: '1.1rem' }}>
      {title}
    </h4>
    <div style={{ color: '#d1d5db' }}>{children}</div>
  </div>
);

export default UserAgreement;
