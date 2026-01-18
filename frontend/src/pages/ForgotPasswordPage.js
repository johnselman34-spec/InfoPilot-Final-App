/**
 * InfoPilot Explorer - Forgot Password Page
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { API } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const ForgotPasswordPage = () => {
  const showToast = useToast();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setSubmitted(true);
      showToast("Reset link sent! Check your email.", "success");
    } catch (err) {
      // Still show success to prevent email enumeration
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <StarsBackground />
        <Card className="w-full max-w-md card-glass border-green-400/30">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="text-slate-900" size={32} />
            </div>
            <CardTitle className="text-2xl text-green-400">Check Your Email</CardTitle>
            <CardDescription className="text-white/60">
              If an account exists with <span className="text-white">{email}</span>, we&apos;ve sent a password reset link.
            </CardDescription>
          </CardHeader>
          
          <CardContent className="text-center space-y-4">
            <p className="text-white/60 text-sm">
              The link will expire in 1 hour. Check your spam folder if you don&apos;t see it.
            </p>
            <div className="p-4 bg-yellow-400/10 border border-yellow-400/30 rounded-lg">
              <p className="text-yellow-400 text-sm">
                💡 Tip: Make sure to check your spam or junk folder if the email doesn&apos;t arrive within a few minutes.
              </p>
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col gap-4">
            <Link to="/login" className="w-full">
              <Button variant="outline" className="w-full" data-testid="back-to-login-btn">
                <ArrowLeft size={16} className="mr-2" /> Back to Login
              </Button>
            </Link>
            <button 
              type="button" 
              onClick={() => setSubmitted(false)}
              className="text-yellow-400 hover:underline text-sm"
            >
              Didn&apos;t receive the email? Try again
            </button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <StarsBackground />
      <Card className="w-full max-w-md card-glass border-yellow-400/30">
        <CardHeader className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center mx-auto mb-4">
            <Mail className="text-slate-900" size={32} />
          </div>
          <CardTitle className="text-2xl text-gradient-gold">Forgot Password?</CardTitle>
          <CardDescription className="text-white/60">
            No worries! Enter your email and we&apos;ll send you a reset link.
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-white">Email Address</Label>
              <Input 
                className="form-input mt-1" 
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                data-testid="forgot-password-email"
                required
                autoFocus
              />
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full btn-gold" disabled={loading} data-testid="send-reset-link-btn">
              {loading ? "Sending..." : "Send Reset Link"}
            </Button>
            
            <Link to="/login" className="text-yellow-400 hover:underline text-sm flex items-center justify-center gap-1">
              <ArrowLeft size={14} /> Back to Login
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default ForgotPasswordPage;
