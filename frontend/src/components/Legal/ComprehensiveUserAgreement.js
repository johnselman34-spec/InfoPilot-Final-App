/**
 * Comprehensive User Agreement with Age Verification
 * Requirements:
 * - Age 26+ STRICTLY verified THREE times
 * - Promise not to impersonate anyone over 26
 * - Promise not to contact anyone under 26
 * - Prohibited content restrictions (nuclear, terrorism, biological/chemical/psychological warfare)
 * - Complete privacy statement
 */
import React, { useState } from 'react';

// List of prohibited research topics
const PROHIBITED_TOPICS = [
  'nuclear weapons', 'nuclear technology', 'uranium enrichment', 'plutonium',
  'terrorism', 'terrorist', 'bomb making', 'explosive devices',
  'biological weapons', 'bioweapons', 'anthrax', 'smallpox weaponization',
  'chemical weapons', 'nerve agents', 'sarin', 'mustard gas', 'VX gas',
  'psychological warfare', 'mind control', 'brainwashing techniques',
  'mass destruction', 'WMD', 'radiological weapons', 'dirty bomb'
];

// Export prohibited topics for use in search filtering
export const getProhibitedTopics = () => PROHIBITED_TOPICS;

// Check if a search query contains prohibited content
export const containsProhibitedContent = (query) => {
  const lowerQuery = query.toLowerCase();
  return PROHIBITED_TOPICS.some(topic => lowerQuery.includes(topic.toLowerCase()));
};

const ComprehensiveUserAgreement = ({ onAccept, onDecline }) => {
  // Age verification states - must be confirmed THREE times
  const [ageConfirm1, setAgeConfirm1] = useState(false);
  const [ageConfirm2, setAgeConfirm2] = useState(false);
  const [ageConfirm3, setAgeConfirm3] = useState(false);
  
  // Other agreement checkboxes
  const [noImpersonation, setNoImpersonation] = useState(false);
  const [noContactMinors, setNoContactMinors] = useState(false);
  const [understandProhibited, setUnderstandProhibited] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  
  // Current section being viewed
  const [currentSection, setCurrentSection] = useState('age');
  
  // Check if all age verifications are complete
  const allAgeVerified = ageConfirm1 && ageConfirm2 && ageConfirm3;
  
  // Check if all agreements are accepted
  const allAccepted = allAgeVerified && noImpersonation && noContactMinors && 
                      understandProhibited && acceptPrivacy && acceptTerms;

  const handleAccept = () => {
    if (allAccepted) {
      onAccept({
        ageVerifiedThreeTimes: true,
        ageConfirmations: [ageConfirm1, ageConfirm2, ageConfirm3],
        noImpersonationAccepted: noImpersonation,
        noContactMinorsAccepted: noContactMinors,
        prohibitedContentAcknowledged: understandProhibited,
        privacyPolicyAccepted: acceptPrivacy,
        termsAccepted: acceptTerms,
        acceptedAt: new Date().toISOString()
      });
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.95)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000,
      padding: 20,
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #1a1035, #2d1f4e)',
        borderRadius: 20,
        maxWidth: 900,
        width: '100%',
        maxHeight: '95vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        border: '3px solid rgba(239, 68, 68, 0.6)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7)',
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
          padding: '20px 30px',
        }}>
          <h2 style={{ color: '#fff', margin: 0, fontSize: '1.5rem' }}>
            ⚠️ MANDATORY USER AGREEMENT & AGE VERIFICATION
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.8)', margin: '8px 0 0 0', fontSize: '0.9rem' }}>
            You MUST complete ALL sections before using InfoPilot Explorer
          </p>
        </div>
        
        {/* Navigation Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid rgba(124, 58, 237, 0.3)',
          background: 'rgba(0,0,0,0.2)'
        }}>
          {[
            { id: 'age', label: '1. Age Verification', icon: '🎂', complete: allAgeVerified },
            { id: 'conduct', label: '2. User Conduct', icon: '👤', complete: noImpersonation && noContactMinors },
            { id: 'prohibited', label: '3. Prohibited Content', icon: '🚫', complete: understandProhibited },
            { id: 'privacy', label: '4. Privacy & Terms', icon: '🔒', complete: acceptPrivacy && acceptTerms },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentSection(tab.id)}
              style={{
                flex: 1,
                padding: '12px 10px',
                background: currentSection === tab.id ? 'rgba(124, 58, 237, 0.3)' : 'transparent',
                border: 'none',
                borderBottom: currentSection === tab.id ? '3px solid #8b5cf6' : '3px solid transparent',
                color: tab.complete ? '#10b981' : (currentSection === tab.id ? '#fff' : '#a1a1aa'),
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: currentSection === tab.id ? 600 : 400,
              }}
            >
              {tab.icon} {tab.label} {tab.complete && '✓'}
            </button>
          ))}
        </div>
        
        {/* Content */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: 30,
          color: '#e5e7eb',
          lineHeight: 1.7,
        }}>
          {/* Section 1: Age Verification */}
          {currentSection === 'age' && (
            <div>
              <h3 style={{ color: '#ef4444', marginBottom: 20 }}>
                🎂 MANDATORY AGE VERIFICATION (26+ ONLY)
              </h3>
              
              <div style={{
                background: 'rgba(239, 68, 68, 0.15)',
                padding: 20,
                borderRadius: 12,
                border: '2px solid rgba(239, 68, 68, 0.4)',
                marginBottom: 25
              }}>
                <p style={{ color: '#fca5a5', fontWeight: 600, fontSize: '1.1rem', margin: 0 }}>
                  ⚠️ IMPORTANT: This platform is STRICTLY for users aged 26 years or older.
                </p>
                <p style={{ color: '#fca5a5', margin: '10px 0 0 0' }}>
                  If you are under 26 years of age, you must exit this application immediately.
                  Falsifying your age is a violation of our terms and may result in legal action.
                </p>
              </div>
              
              <p style={{ marginBottom: 20 }}>
                To ensure compliance, you must confirm your age THREE (3) separate times:
              </p>
              
              {/* Age Confirmation 1 */}
              <VerificationCheckbox
                checked={ageConfirm1}
                onChange={setAgeConfirm1}
                number={1}
                title="First Age Confirmation"
                description="I confirm that I am 26 years of age or older. I understand that this platform is designed exclusively for adults aged 26 and above."
                testId="age-confirm-1"
              />
              
              {/* Age Confirmation 2 */}
              <VerificationCheckbox
                checked={ageConfirm2}
                onChange={setAgeConfirm2}
                number={2}
                title="Second Age Confirmation"
                description="I hereby declare under penalty of perjury that I was born on or before today's date 26 years ago. I am legally an adult over the age of 26."
                testId="age-confirm-2"
                disabled={!ageConfirm1}
              />
              
              {/* Age Confirmation 3 */}
              <VerificationCheckbox
                checked={ageConfirm3}
                onChange={setAgeConfirm3}
                number={3}
                title="Final Age Confirmation"
                description="I solemnly affirm for the third and final time that I am at least 26 years old. I understand that providing false information about my age may result in immediate account termination and potential legal consequences."
                testId="age-confirm-3"
                disabled={!ageConfirm2}
              />
              
              {allAgeVerified && (
                <div style={{
                  background: 'rgba(16, 185, 129, 0.2)',
                  padding: 15,
                  borderRadius: 10,
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  marginTop: 20
                }}>
                  <p style={{ color: '#10b981', margin: 0, fontWeight: 600 }}>
                    ✓ Age verification complete! Please proceed to the next section.
                  </p>
                </div>
              )}
            </div>
          )}
          
          {/* Section 2: User Conduct */}
          {currentSection === 'conduct' && (
            <div>
              <h3 style={{ color: '#f59e0b', marginBottom: 20 }}>
                👤 USER CONDUCT AGREEMENT
              </h3>
              
              <div style={{
                background: 'rgba(245, 158, 11, 0.15)',
                padding: 20,
                borderRadius: 12,
                border: '2px solid rgba(245, 158, 11, 0.4)',
                marginBottom: 25
              }}>
                <h4 style={{ color: '#fbbf24', margin: '0 0 15px 0' }}>
                  Identity & Communication Rules
                </h4>
                <p style={{ margin: 0, color: '#fcd34d' }}>
                  To maintain a safe and trustworthy community, all users must agree to the following 
                  conduct requirements. Violations will result in immediate account termination.
                </p>
              </div>
              
              {/* No Impersonation */}
              <VerificationCheckbox
                checked={noImpersonation}
                onChange={setNoImpersonation}
                icon="🎭"
                title="No Impersonation Agreement"
                description="I promise that I will NOT impersonate any person over the age of 26, including but not limited to: creating fake profiles, using someone else's photos, assuming false identities, or misrepresenting my credentials, profession, or affiliations. I will only represent myself truthfully."
                testId="no-impersonation"
              />
              
              {/* No Contact with Minors */}
              <VerificationCheckbox
                checked={noContactMinors}
                onChange={setNoContactMinors}
                icon="🚫"
                title="No Contact with Minors Agreement"
                description="I promise that I will NOT attempt to contact, communicate with, solicit, or interact with any person under the age of 26 through this platform or using information obtained from this platform. I understand this is a community for adults 26+ only and I will respect these boundaries."
                testId="no-contact-minors"
              />
              
              {noImpersonation && noContactMinors && (
                <div style={{
                  background: 'rgba(16, 185, 129, 0.2)',
                  padding: 15,
                  borderRadius: 10,
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  marginTop: 20
                }}>
                  <p style={{ color: '#10b981', margin: 0, fontWeight: 600 }}>
                    ✓ Conduct agreements accepted! Please proceed to the next section.
                  </p>
                </div>
              )}
            </div>
          )}
          
          {/* Section 3: Prohibited Content */}
          {currentSection === 'prohibited' && (
            <div>
              <h3 style={{ color: '#ef4444', marginBottom: 20 }}>
                🚫 PROHIBITED CONTENT ACKNOWLEDGMENT
              </h3>
              
              <div style={{
                background: 'rgba(239, 68, 68, 0.2)',
                padding: 25,
                borderRadius: 12,
                border: '3px solid rgba(239, 68, 68, 0.5)',
                marginBottom: 25
              }}>
                <h4 style={{ color: '#fca5a5', margin: '0 0 15px 0', fontSize: '1.2rem' }}>
                  ⚠️ STRICTLY PROHIBITED RESEARCH TOPICS
                </h4>
                <p style={{ color: '#fecaca', marginBottom: 15 }}>
                  The following topics are ABSOLUTELY FORBIDDEN on this platform. 
                  Any attempt to research, search for, or share information about these topics 
                  will result in immediate account termination and may be reported to authorities:
                </p>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 15 }}>
                  <ProhibitedCategory 
                    icon="☢️" 
                    title="Nuclear Technology"
                    items={['Nuclear weapons', 'Uranium enrichment', 'Plutonium processing', 'Radiological devices', 'Dirty bombs']}
                  />
                  <ProhibitedCategory 
                    icon="💣" 
                    title="Terrorism"
                    items={['Terrorist activities', 'Bomb making', 'Explosive devices', 'Attack planning', 'Recruitment materials']}
                  />
                  <ProhibitedCategory 
                    icon="🧪" 
                    title="Biological Weapons"
                    items={['Bioweapons', 'Pathogen weaponization', 'Anthrax production', 'Viral enhancement', 'Disease deployment']}
                  />
                  <ProhibitedCategory 
                    icon="⚗️" 
                    title="Chemical Weapons"
                    items={['Nerve agents', 'Toxic chemicals', 'Sarin/VX production', 'Mustard gas', 'Poisoning methods']}
                  />
                </div>
                
                <div style={{ marginTop: 20 }}>
                  <ProhibitedCategory 
                    icon="🧠" 
                    title="Psychological Warfare"
                    items={['Mind control techniques', 'Brainwashing', 'Mass manipulation', 'Psychological torture', 'Coercive control methods']}
                  />
                </div>
              </div>
              
              <VerificationCheckbox
                checked={understandProhibited}
                onChange={setUnderstandProhibited}
                icon="✋"
                title="Prohibited Content Acknowledgment"
                description="I have read and understand the list of prohibited content above. I acknowledge that I will NOT use InfoPilot Explorer to research, search for, collect, or distribute any information related to nuclear technology, terrorism, biological weapons, chemical weapons, psychological warfare, or any other content that could be used to cause mass harm. I understand that violations will be reported to law enforcement."
                testId="understand-prohibited"
              />
              
              {understandProhibited && (
                <div style={{
                  background: 'rgba(16, 185, 129, 0.2)',
                  padding: 15,
                  borderRadius: 10,
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  marginTop: 20
                }}>
                  <p style={{ color: '#10b981', margin: 0, fontWeight: 600 }}>
                    ✓ Prohibited content acknowledgment complete! Please proceed to the final section.
                  </p>
                </div>
              )}
            </div>
          )}
          
          {/* Section 4: Privacy & Terms */}
          {currentSection === 'privacy' && (
            <div>
              <h3 style={{ color: '#8b5cf6', marginBottom: 20 }}>
                🔒 PRIVACY STATEMENT & TERMS OF SERVICE
              </h3>
              
              {/* Privacy Statement */}
              <div style={{
                background: 'rgba(139, 92, 246, 0.1)',
                padding: 25,
                borderRadius: 12,
                border: '1px solid rgba(139, 92, 246, 0.3)',
                marginBottom: 25,
                maxHeight: 300,
                overflowY: 'auto'
              }}>
                <h4 style={{ color: '#a78bfa', margin: '0 0 15px 0' }}>
                  Privacy Statement - Top Pilot Enterprises, Inc.
                </h4>
                
                <PrivacySection title="1. Information We Collect">
                  <ul style={{ paddingLeft: 20 }}>
                    <li><strong>Account Information:</strong> Email, username, password (encrypted)</li>
                    <li><strong>Usage Data:</strong> Search queries, protocols created, marketplace activity</li>
                    <li><strong>Device Information:</strong> Browser type, IP address, device identifiers</li>
                    <li><strong>Payment Information:</strong> Processed securely through Stripe/PayPal</li>
                    <li><strong>Age Verification:</strong> Your confirmation that you are 26+ years old</li>
                  </ul>
                </PrivacySection>
                
                <PrivacySection title="2. How We Use Your Information">
                  <ul style={{ paddingLeft: 20 }}>
                    <li>Providing and improving our services</li>
                    <li>Processing transactions and payments</li>
                    <li>Communicating with you about your account</li>
                    <li>Ensuring platform safety and security</li>
                    <li>Complying with legal obligations</li>
                    <li>Monitoring for prohibited content violations</li>
                  </ul>
                </PrivacySection>
                
                <PrivacySection title="3. Information Sharing">
                  <p>We do NOT sell your personal information. We may share data with:</p>
                  <ul style={{ paddingLeft: 20 }}>
                    <li>Service providers who help operate our platform</li>
                    <li>Law enforcement when required by law</li>
                    <li>Other users (only your public profile/protocols)</li>
                  </ul>
                </PrivacySection>
                
                <PrivacySection title="4. Data Security">
                  <p>
                    We implement industry-standard security measures including encryption, 
                    secure servers, and regular security audits. However, no system is 100% secure.
                  </p>
                </PrivacySection>
                
                <PrivacySection title="5. Your Rights">
                  <ul style={{ paddingLeft: 20 }}>
                    <li>Access your personal data</li>
                    <li>Request data correction or deletion</li>
                    <li>Opt-out of marketing communications</li>
                    <li>Export your data</li>
                    <li>Close your account at any time</li>
                  </ul>
                </PrivacySection>
                
                <PrivacySection title="6. Cookies & Tracking">
                  <p>
                    We use cookies for authentication, preferences, and analytics. 
                    You can control cookies through your browser settings.
                  </p>
                </PrivacySection>
                
                <PrivacySection title="7. Children's Privacy">
                  <p style={{ color: '#fca5a5', fontWeight: 600 }}>
                    This platform is NOT for users under 26 years of age. We do not knowingly 
                    collect information from anyone under 26. If we discover such data, 
                    it will be immediately deleted.
                  </p>
                </PrivacySection>
                
                <PrivacySection title="8. Contact Us">
                  <p>
                    For privacy inquiries: privacy@toppilot.com<br/>
                    Top Pilot Enterprises, Inc.<br/>
                    Last Updated: February 2026
                  </p>
                </PrivacySection>
              </div>
              
              {/* Terms Summary */}
              <div style={{
                background: 'rgba(59, 130, 246, 0.1)',
                padding: 20,
                borderRadius: 12,
                border: '1px solid rgba(59, 130, 246, 0.3)',
                marginBottom: 25
              }}>
                <h4 style={{ color: '#60a5fa', margin: '0 0 10px 0' }}>
                  Terms of Service Summary
                </h4>
                <ul style={{ paddingLeft: 20, color: '#93c5fd' }}>
                  <li>You must be 26+ years old to use this service</li>
                  <li>You are responsible for your account security</li>
                  <li>Prohibited content will result in termination</li>
                  <li>Marketplace transactions are subject to platform fees</li>
                  <li>We reserve the right to modify these terms</li>
                  <li>Service is provided "as is" without warranties</li>
                  <li>Governed by the laws of Maine, United States</li>
                </ul>
              </div>
              
              {/* Final Checkboxes */}
              <VerificationCheckbox
                checked={acceptPrivacy}
                onChange={setAcceptPrivacy}
                icon="🔒"
                title="Privacy Policy Agreement"
                description="I have read and understand the Privacy Statement above. I consent to the collection and use of my information as described."
                testId="accept-privacy"
              />
              
              <VerificationCheckbox
                checked={acceptTerms}
                onChange={setAcceptTerms}
                icon="📜"
                title="Terms of Service Agreement"
                description="I have read and agree to the Terms of Service. I understand my rights and responsibilities as a user of InfoPilot Explorer."
                testId="accept-terms-final"
              />
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div style={{
          padding: 20,
          borderTop: '2px solid rgba(124, 58, 237, 0.3)',
          background: 'rgba(0,0,0,0.3)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
            {allAccepted ? (
              <span style={{ color: '#10b981' }}>✓ All agreements accepted - Ready to continue</span>
            ) : (
              <span>Complete all sections to continue</span>
            )}
          </div>
          
          <div style={{ display: 'flex', gap: 15 }}>
            <button
              onClick={onDecline}
              style={{
                padding: '12px 25px',
                background: 'rgba(239, 68, 68, 0.2)',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: '0.95rem',
              }}
              data-testid="decline-agreement-btn"
            >
              ✕ I Do Not Agree
            </button>
            <button
              onClick={handleAccept}
              disabled={!allAccepted}
              style={{
                padding: '12px 30px',
                background: allAccepted 
                  ? 'linear-gradient(135deg, #10b981, #059669)' 
                  : 'rgba(107, 114, 128, 0.3)',
                color: allAccepted ? '#fff' : '#6b7280',
                border: 'none',
                borderRadius: 8,
                cursor: allAccepted ? 'pointer' : 'not-allowed',
                fontSize: '0.95rem',
                fontWeight: 600,
              }}
              data-testid="accept-all-btn"
            >
              ✓ I Accept All Terms & Conditions
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Reusable verification checkbox component
const VerificationCheckbox = ({ checked, onChange, number, icon, title, description, testId, disabled }) => (
  <div style={{
    background: checked ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.05)',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    border: checked ? '2px solid rgba(16, 185, 129, 0.5)' : '1px solid rgba(255,255,255,0.1)',
    opacity: disabled ? 0.5 : 1,
    transition: 'all 0.2s'
  }}>
    <label style={{ 
      display: 'flex', 
      alignItems: 'flex-start', 
      gap: 15, 
      cursor: disabled ? 'not-allowed' : 'pointer' 
    }}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => !disabled && onChange(e.target.checked)}
        disabled={disabled}
        style={{ 
          width: 24, 
          height: 24, 
          marginTop: 2,
          accentColor: '#10b981',
          cursor: disabled ? 'not-allowed' : 'pointer'
        }}
        data-testid={testId}
      />
      <div>
        <strong style={{ 
          color: checked ? '#10b981' : '#fff', 
          fontSize: '1.05rem',
          display: 'block',
          marginBottom: 5
        }}>
          {number ? `${number}. ` : ''}{icon ? `${icon} ` : ''}{title}
        </strong>
        <p style={{ color: '#d1d5db', margin: 0, lineHeight: 1.6 }}>
          {description}
        </p>
      </div>
    </label>
  </div>
);

// Prohibited category display component
const ProhibitedCategory = ({ icon, title, items }) => (
  <div style={{
    background: 'rgba(0,0,0,0.3)',
    padding: 15,
    borderRadius: 8,
    border: '1px solid rgba(239, 68, 68, 0.3)'
  }}>
    <h5 style={{ color: '#fca5a5', margin: '0 0 10px 0', fontSize: '1rem' }}>
      {icon} {title}
    </h5>
    <ul style={{ margin: 0, paddingLeft: 20, color: '#fecaca', fontSize: '0.85rem' }}>
      {items.map((item, i) => <li key={i}>{item}</li>)}
    </ul>
  </div>
);

// Privacy section component
const PrivacySection = ({ title, children }) => (
  <div style={{ marginBottom: 20 }}>
    <h5 style={{ color: '#c4b5fd', margin: '0 0 8px 0' }}>{title}</h5>
    <div style={{ color: '#d1d5db', fontSize: '0.9rem' }}>{children}</div>
  </div>
);

export default ComprehensiveUserAgreement;
