/**
 * InfoPilot Explorer - Reset Password Page
 */
import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Lock, Eye, EyeOff, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { API } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const ResetPasswordPage = () => {
  const showToast = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [success, setSuccess] = useState(false);

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setVerifying(false);
        return;
      }
      
      try {
        const res = await axios.get(`${API}/auth/verify-reset-token?token=${token}`);
        setTokenValid(res.data.valid);
        setUserEmail(res.data.email);
      } catch (err) {
        setTokenValid(false);
      } finally {
        setVerifying(false);
      }
    };
    
    verifyToken();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      showToast("Passwords don't match", "error");
      return;
    }
    
    if (password.length < 6) {
      showToast("Password must be at least 6 characters", "error");
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: password
      });
      setSuccess(true);
      showToast("Password reset successfully!", "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to reset password", "error");
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (verifying) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <StarsBackground />
        <Card className="w-full max-w-md card-glass border-yellow-400/30">
          <CardContent className="py-12 text-center">
            <div className="w-12 h-12 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white/60">Verifying reset link...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Invalid or no token
  if (!token || !tokenValid) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <StarsBackground />
        <Card className="w-full max-w-md card-glass border-red-400/30">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-red-400 to-red-600 flex items-center justify-center mx-auto mb-4">
              <XCircle className="text-white" size={32} />
            </div>
            <CardTitle className="text-2xl text-red-400">Invalid Reset Link</CardTitle>
            <CardDescription className="text-white/60">
              This password reset link is invalid or has expired.
            </CardDescription>
          </CardHeader>
          
          <CardContent className="text-center">
            <p className="text-white/60 text-sm">
              Reset links expire after 1 hour for security reasons.
            </p>
          </CardContent>
          
          <CardFooter className="flex flex-col gap-4">
            <Link to="/forgot-password" className="w-full">
              <Button className="w-full btn-gold" data-testid="request-new-link-btn">
                Request New Reset Link
              </Button>
            </Link>
            <Link to="/login" className="text-yellow-400 hover:underline text-sm flex items-center justify-center gap-1">
              <ArrowLeft size={14} /> Back to Login
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <StarsBackground />
        <Card className="w-full max-w-md card-glass border-green-400/30">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="text-slate-900" size={32} />
            </div>
            <CardTitle className="text-2xl text-green-400">Password Reset!</CardTitle>
            <CardDescription className="text-white/60">
              Your password has been successfully changed.
            </CardDescription>
          </CardHeader>
          
          <CardContent className="text-center">
            <p className="text-white/60 text-sm">
              You can now log in with your new password.
            </p>
          </CardContent>
          
          <CardFooter>
            <Button 
              onClick={() => navigate('/login')} 
              className="w-full btn-gold" 
              data-testid="go-to-login-btn"
            >
              Go to Login
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // Reset form
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <StarsBackground />
      <Card className="w-full max-w-md card-glass border-yellow-400/30">
        <CardHeader className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center mx-auto mb-4">
            <Lock className="text-slate-900" size={32} />
          </div>
          <CardTitle className="text-2xl text-gradient-gold">Reset Password</CardTitle>
          <CardDescription className="text-white/60">
            Enter a new password for <span className="text-white">{userEmail}</span>
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-white">New Password</Label>
              <div className="relative">
                <Input 
                  className="form-input mt-1 pr-10" 
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  data-testid="new-password-input"
                  required
                  minLength={6}
                  autoFocus
                />
                <button 
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <p className="text-white/40 text-xs mt-1">Minimum 6 characters</p>
            </div>
            
            <div>
              <Label className="text-white">Confirm New Password</Label>
              <Input 
                className="form-input mt-1" 
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                data-testid="confirm-password-input"
                required
              />
              {confirmPassword && password !== confirmPassword && (
                <p className="text-red-400 text-xs mt-1">Passwords don&apos;t match</p>
              )}
              {confirmPassword && password === confirmPassword && password.length >= 6 && (
                <p className="text-green-400 text-xs mt-1 flex items-center gap-1">
                  <CheckCircle size={12} /> Passwords match
                </p>
              )}
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col gap-4">
            <Button 
              type="submit" 
              className="w-full btn-gold" 
              disabled={loading || password !== confirmPassword || password.length < 6} 
              data-testid="reset-password-btn"
            >
              {loading ? "Resetting..." : "Reset Password"}
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

export default ResetPasswordPage;
