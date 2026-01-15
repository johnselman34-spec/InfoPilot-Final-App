import React, { useState } from 'react';

/**
 * CopyButton Component
 * Allows copying text to clipboard with visual feedback
 */
const CopyButton = ({ 
  text, 
  label = 'Copy', 
  successLabel = 'Copied!',
  disabled = false,
  className = '',
  style = {},
  size = 'sm',  // sm, md, lg
  variant = 'secondary',  // primary, secondary, icon
  showToast,
  'data-testid': testId
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    if (disabled || !text) return;

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      if (showToast) {
        showToast('📋 Copied to clipboard!', 'success');
      }
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        setCopied(true);
        if (showToast) {
          showToast('📋 Copied to clipboard!', 'success');
        }
        setTimeout(() => setCopied(false), 2000);
      } catch (e) {
        if (showToast) {
          showToast('Failed to copy', 'error');
        }
      }
      document.body.removeChild(textArea);
    }
  };

  const sizeStyles = {
    sm: { padding: '4px 8px', fontSize: '0.75rem' },
    md: { padding: '6px 12px', fontSize: '0.85rem' },
    lg: { padding: '8px 16px', fontSize: '1rem' }
  };

  const variantStyles = {
    primary: {
      background: copied ? '#10b981' : 'linear-gradient(135deg, #7c3aed, #a855f7)',
      color: '#fff',
      border: 'none'
    },
    secondary: {
      background: copied ? 'rgba(16, 185, 129, 0.2)' : 'rgba(124, 58, 237, 0.2)',
      color: copied ? '#10b981' : '#a78bfa',
      border: '1px solid ' + (copied ? '#10b981' : 'rgba(124, 58, 237, 0.3)')
    },
    icon: {
      background: 'transparent',
      color: copied ? '#10b981' : '#a1a1aa',
      border: 'none',
      padding: '4px'
    }
  };

  return (
    <button
      onClick={handleCopy}
      disabled={disabled}
      data-testid={testId}
      className={className}
      style={{
        ...sizeStyles[size],
        ...variantStyles[variant],
        borderRadius: 6,
        cursor: disabled ? 'not-allowed' : 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        transition: 'all 0.2s',
        opacity: disabled ? 0.5 : 1,
        ...style
      }}
      title={disabled ? 'Copy not available' : `Copy ${label}`}
    >
      {copied ? (
        <>✓ {successLabel}</>
      ) : (
        <>📋 {label}</>
      )}
    </button>
  );
};

/**
 * ProtocolCopyButtons Component
 * Shows copy buttons for protocol title and content based on access
 */
export const ProtocolCopyButtons = ({
  title,
  protocol,
  hasAccess = false,
  showToast,
  style = {}
}) => {
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', ...style }}>
      {/* Title can always be copied */}
      <CopyButton
        text={title}
        label="Title"
        successLabel="Title Copied!"
        size="sm"
        variant="secondary"
        showToast={showToast}
        data-testid="copy-title-btn"
      />
      
      {/* Protocol can only be copied if user has access */}
      {hasAccess && protocol && (
        <CopyButton
          text={protocol}
          label="Protocol"
          successLabel="Protocol Copied!"
          size="sm"
          variant="primary"
          showToast={showToast}
          data-testid="copy-protocol-btn"
        />
      )}
      
      {!hasAccess && (
        <span 
          style={{ 
            fontSize: '0.7rem', 
            color: '#71717a',
            alignSelf: 'center',
            fontStyle: 'italic'
          }}
          title="Purchase or copy this protocol to get access"
        >
          🔒 Protocol locked
        </span>
      )}
    </div>
  );
};

export default CopyButton;
