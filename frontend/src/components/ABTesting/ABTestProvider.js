import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { API } from '../../utils/api';

/**
 * A/B Testing Context
 * Provides variant data to components throughout the app
 */
const ABTestContext = createContext({
  variants: {},
  trackEvent: () => {},
  isLoading: true
});

export const useABTest = () => useContext(ABTestContext);

/**
 * A/B Test Provider
 * Fetches all variant assignments and provides tracking functions
 */
export const ABTestProvider = ({ children, testNames = [] }) => {
  const [variants, setVariants] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [sessionId] = useState(() => 
    localStorage.getItem('ab_session_id') || 
    `session_${Date.now()}_${Math.random().toString(36).slice(2)}`
  );

  // Store session ID
  useEffect(() => {
    localStorage.setItem('ab_session_id', sessionId);
  }, [sessionId]);

  // Fetch variants on mount
  const fetchVariants = useCallback(async () => {
    if (testNames.length === 0) {
      setIsLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/ab-testing/variants/batch?test_names=${testNames.join(',')}`, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          'X-Session-ID': sessionId
        }
      });

      if (res.ok) {
        const data = await res.json();
        setVariants(data.variants || {});
      }
    } catch (e) {
      console.error('Failed to fetch A/B variants:', e);
    }
    setIsLoading(false);
  }, [testNames, sessionId]);

  useEffect(() => {
    // Data fetching on mount - standard React pattern
    let mounted = true;
    const loadVariants = async () => {
      if (mounted) {
        await fetchVariants();
      }
    };
    loadVariants();
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Track event function
  const trackEvent = useCallback(async (testId, variantId, eventType, metadata = {}) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API}/ab-testing/event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          'X-Session-ID': sessionId
        },
        body: JSON.stringify({
          test_id: testId,
          variant_id: variantId,
          event_type: eventType,
          metadata
        })
      });
    } catch (e) {
      console.error('Failed to track A/B event:', e);
    }
  }, [sessionId]);

  return (
    <ABTestContext.Provider value={{ variants, trackEvent, isLoading, sessionId }}>
      {children}
    </ABTestContext.Provider>
  );
};

/**
 * A/B Test Wrapper Component
 * Wraps content and handles variant selection + tracking
 */
export const ABTest = ({ 
  testName, 
  children, 
  onVariantLoad,
  trackImpression = true 
}) => {
  const { variants, trackEvent, isLoading } = useABTest();
  const [variant, setVariant] = useState(null);
  const [hasTrackedImpression, setHasTrackedImpression] = useState(false);

  // Set variant when loaded
  useEffect(() => {
    if (!isLoading && variants[testName]) {
      const currentVariant = variants[testName];
      setVariant(currentVariant);
      onVariantLoad?.(currentVariant);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading, variants, testName]);

  // Track impression once
  useEffect(() => {
    if (variant && trackImpression && !hasTrackedImpression) {
      trackEvent(testName, variant.variant_id, 'impression');
      setHasTrackedImpression(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [variant, trackImpression, hasTrackedImpression]);

  // Provide click tracking helper
  const handleClick = () => {
    if (variant) {
      trackEvent(testName, variant.variant_id, 'click');
    }
  };

  const handleConversion = (metadata = {}) => {
    if (variant) {
      trackEvent(testName, variant.variant_id, 'conversion', metadata);
    }
  };

  if (isLoading) {
    return null;
  }

  // Render children with variant data
  if (typeof children === 'function') {
    return children({ variant, handleClick, handleConversion });
  }

  return children;
};

/**
 * Standalone hook for fetching a single variant
 */
export const useVariant = (testName) => {
  const [variant, setVariant] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionId] = useState(() => 
    localStorage.getItem('ab_session_id') || 
    `session_${Date.now()}_${Math.random().toString(36).slice(2)}`
  );

  useEffect(() => {
    const fetchVariant = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API}/ab-testing/variant/${testName}`, {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            'X-Session-ID': sessionId
          }
        });

        if (res.ok) {
          const data = await res.json();
          setVariant(data);
        }
      } catch (e) {
        console.error(`Failed to fetch variant for ${testName}:`, e);
      }
      setIsLoading(false);
    };

    fetchVariant();
  }, [testName, sessionId]);

  const trackEvent = useCallback(async (eventType, metadata = {}) => {
    if (!variant) return;
    
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API}/ab-testing/event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          'X-Session-ID': sessionId
        },
        body: JSON.stringify({
          test_id: testName,
          variant_id: variant.variant_id,
          event_type: eventType,
          metadata
        })
      });
    } catch (e) {
      console.error('Failed to track event:', e);
    }
  }, [variant, testName, sessionId]);

  return { variant, isLoading, trackEvent };
};

export default ABTestProvider;
