/**
 * InfoPilot Explorer - Login Page
 */
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Sparkles, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { API } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const LoginPage = () => {
  const { login } = useAuth();
  const showToast = useToast();
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", username: "" });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const endpoint = isRegister ? "/auth/register" : "/auth/login";
      const res = await axios.post(`${API}${endpoint}`, form);
      login(res.data);
      showToast(isRegister ? "Welcome to InfoPilot! 🎉" : "Welcome back! 🐻", "success");
      navigate("/search");
    } catch (err) {
      showToast(err.response?.data?.detail || "Authentication failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <StarsBackground />
      <Card className="w-full max-w-md card-glass border-yellow-400/30">
        <CardHeader className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="text-slate-900" size={32} />
          </div>
          <CardTitle className="text-2xl text-gradient-gold">
            {isRegister ? "Create Account" : "Welcome Back"}
          </CardTitle>
          <CardDescription className="text-white/60">
            {isRegister ? "Join the InfoPilot Explorer community" : "Sign in to your account"}
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {isRegister && (
              <div>
                <Label className="text-white">Username</Label>
                <Input 
                  className="form-input mt-1" 
                  placeholder="Choose a username"
                  value={form.username}
                  onChange={e => setForm({...form, username: e.target.value})}
                  data-testid="register-username"
                  required
                />
              </div>
            )}
            
            <div>
              <Label className="text-white">Email</Label>
              <Input 
                className="form-input mt-1" 
                type="email"
                placeholder="your@email.com"
                value={form.email}
                onChange={e => setForm({...form, email: e.target.value})}
                data-testid="login-email"
                required
              />
            </div>
            
            <div>
              <div className="flex items-center justify-between">
                <Label className="text-white">Password</Label>
                {!isRegister && (
                  <Link 
                    to="/forgot-password" 
                    className="text-yellow-400 hover:underline text-xs"
                    data-testid="forgot-password-link"
                  >
                    Forgot password?
                  </Link>
                )}
              </div>
              <div className="relative">
                <Input 
                  className="form-input mt-1 pr-10" 
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm({...form, password: e.target.value})}
                  data-testid="login-password"
                  required
                />
                <button 
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full btn-gold" disabled={loading} data-testid="login-submit">
              {loading ? "Loading..." : isRegister ? "Create Account" : "Sign In"}
            </Button>
            
            <button 
              type="button" 
              onClick={() => setIsRegister(!isRegister)}
              className="text-yellow-400 hover:underline text-sm"
            >
              {isRegister ? "Already have an account? Sign in" : "Need an account? Register"}
            </button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default LoginPage;
