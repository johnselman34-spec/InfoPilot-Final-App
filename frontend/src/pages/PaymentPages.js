import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { CheckCircle, XCircle, ArrowRight, RefreshCw, CreditCard } from 'lucide-react';
import { API } from '../utils/api';

export const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  // Determine initial status based on sessionId
  const getInitialStatus = () => {
    if (!sessionId) return 'error';
    return 'checking';
  };
  
  const [status, setStatus] = useState(getInitialStatus);
  const [paymentData, setPaymentData] = useState(null);
  const [attempts, setAttempts] = useState(0);
  const maxAttempts = 5;

  useEffect(() => {
    if (!sessionId || status === 'error') {
      return;
    }

    const pollPaymentStatus = async () => {
      if (attempts >= maxAttempts) {
        setStatus('timeout');
        return;
      }

      try {
        const response = await axios.get(`${API}/stripe/status/${sessionId}`);
        const data = response.data;
        setPaymentData(data);

        if (data.payment_status === 'paid') {
          setStatus('success');
        } else if (data.status === 'expired') {
          setStatus('expired');
        } else {
          // Continue polling
          setAttempts(prev => prev + 1);
          setTimeout(pollPaymentStatus, 2000);
        }
      } catch (error) {
        console.error('Error checking payment status:', error);
        setAttempts(prev => prev + 1);
        if (attempts < maxAttempts - 1) {
          setTimeout(pollPaymentStatus, 2000);
        } else {
          setStatus('error');
        }
      }
    };

    pollPaymentStatus();
  }, [sessionId, attempts]);

  return (
    <div className="min-h-screen pt-20 px-4 flex items-center justify-center">
      <StarsBackground />
      <Card className="card-glass p-8 max-w-md text-center" data-testid="payment-success">
        {status === 'checking' && (
          <>
            <RefreshCw className="mx-auto text-yellow-400 mb-4 animate-spin" size={64} />
            <h1 className="text-2xl font-bold text-white mb-4">Processing Payment...</h1>
            <p className="text-white/70 mb-6">Please wait while we verify your payment.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="mx-auto text-green-400 mb-4" size={64} />
            <h1 className="text-2xl font-bold text-gradient-gold mb-4">Payment Successful! 🎉</h1>
            <p className="text-white/70 mb-4">
              Thank you for your purchase! Your payment has been processed successfully.
            </p>
            {paymentData && (
              <p className="text-white/50 text-sm mb-6">
                Amount: ${paymentData.amount?.toFixed(2)} {paymentData.currency?.toUpperCase()}
              </p>
            )}
            <div className="flex flex-col gap-3">
              <Link to="/search">
                <Button className="btn-gold w-full">
                  <ArrowRight className="mr-2" size={16} /> Go to Ultimate Search
                </Button>
              </Link>
              <Link to="/marketplace">
                <Button variant="outline" className="w-full">Browse More Protocols</Button>
              </Link>
            </div>
          </>
        )}

        {status === 'expired' && (
          <>
            <XCircle className="mx-auto text-orange-400 mb-4" size={64} />
            <h1 className="text-2xl font-bold text-white mb-4">Session Expired</h1>
            <p className="text-white/70 mb-6">Your payment session has expired. Please try again.</p>
            <Link to="/marketplace">
              <Button className="btn-gold w-full">Return to Marketplace</Button>
            </Link>
          </>
        )}

        {status === 'timeout' && (
          <>
            <RefreshCw className="mx-auto text-yellow-400 mb-4" size={64} />
            <h1 className="text-2xl font-bold text-white mb-4">Taking Longer Than Expected</h1>
            <p className="text-white/70 mb-6">
              Payment verification is taking longer than expected. 
              Please check your email for confirmation.
            </p>
            <Link to="/marketplace">
              <Button className="btn-gold w-full">Return to Marketplace</Button>
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="mx-auto text-red-400 mb-4" size={64} />
            <h1 className="text-2xl font-bold text-white mb-4">Error</h1>
            <p className="text-white/70 mb-6">
              There was an error verifying your payment. Please contact support if you were charged.
            </p>
            <Link to="/marketplace">
              <Button className="btn-gold w-full">Return to Marketplace</Button>
            </Link>
          </>
        )}
      </Card>
    </div>
  );
};

export const PaymentCancel = () => {
  return (
    <div className="min-h-screen pt-20 px-4 flex items-center justify-center">
      <StarsBackground />
      <Card className="card-glass p-8 max-w-md text-center" data-testid="payment-cancelled">
        <XCircle className="mx-auto text-red-400 mb-4" size={64} />
        <h1 className="text-2xl font-bold text-white mb-4">Payment Cancelled</h1>
        <p className="text-white/70 mb-6">
          Your payment was cancelled. No charges have been made.
        </p>
        <div className="flex flex-col gap-3">
          <Link to="/marketplace">
            <Button className="btn-gold w-full">Return to Marketplace</Button>
          </Link>
          <Link to="/">
            <Button variant="outline" className="w-full">Go Home</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

// Subscription checkout component
export const SubscriptionCheckout = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubscribe = async (packageType) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/stripe/create-checkout`, {
        package_type: packageType,
        origin_url: window.location.origin
      });
      
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start checkout');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">Subscribe to InfoPilot</h1>
          <p className="text-white/60">Unlock premium features and support our mission!</p>
        </div>

        {error && (
          <Card className="bg-red-500/20 border-red-500/30 p-4 mb-6">
            <p className="text-red-300">{error}</p>
          </Card>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {/* Monthly Plan */}
          <Card className="card-glass p-6 hover:border-yellow-400/50 transition" data-testid="monthly-plan">
            <div className="text-center">
              <h3 className="text-xl font-bold text-white mb-2">Monthly</h3>
              <p className="text-4xl font-bold text-gradient-gold mb-4">$1.00<span className="text-lg text-white/60">/mo</span></p>
              <ul className="text-white/70 text-sm space-y-2 mb-6">
                <li>✓ Unlimited searches</li>
                <li>✓ All protocol templates</li>
                <li>✓ Priority support</li>
                <li>✓ Cancel anytime</li>
              </ul>
              <Button 
                onClick={() => handleSubscribe('monthly')} 
                className="btn-gold w-full"
                disabled={loading}
                data-testid="subscribe-monthly-btn"
              >
                <CreditCard className="mr-2" size={16} />
                {loading ? 'Processing...' : 'Subscribe Monthly'}
              </Button>
            </div>
          </Card>

          {/* Yearly Plan */}
          <Card className="card-glass p-6 border-2 border-green-400/50 relative" data-testid="yearly-plan">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full">
              SAVE 17%
            </div>
            <div className="text-center">
              <h3 className="text-xl font-bold text-white mb-2">Yearly</h3>
              <p className="text-4xl font-bold text-gradient-gold mb-4">$9.98<span className="text-lg text-white/60">/yr</span></p>
              <ul className="text-white/70 text-sm space-y-2 mb-6">
                <li>✓ Everything in Monthly</li>
                <li>✓ 2 months FREE</li>
                <li>✓ Early access to features</li>
                <li>✓ VIP support</li>
              </ul>
              <Button 
                onClick={() => handleSubscribe('yearly')} 
                className="bg-green-500 hover:bg-green-600 text-white w-full"
                disabled={loading}
                data-testid="subscribe-yearly-btn"
              >
                <CreditCard className="mr-2" size={16} />
                {loading ? 'Processing...' : 'Subscribe Yearly'}
              </Button>
            </div>
          </Card>
        </div>

        <p className="text-center text-white/50 text-sm mt-6">
          Secure payment powered by Stripe. Cancel anytime.
        </p>
      </div>
    </div>
  );
};

export default PaymentSuccess;
