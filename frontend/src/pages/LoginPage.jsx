/**
 * Login Page Component
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { Plane, Lock, Mail, User, Eye, EyeOff, Loader2, Star, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { GOOGLE_CLIENT_ID, BOOK_INFO, IMAGES } from '../utils/constants';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, register, googleLogin } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (isLogin) {
        await login(formData.email, formData.password);
        toast.success("Welcome back, Pilot!");
      } else {
        await register(formData.username, formData.email, formData.password);
        toast.success("Registration successful!");
      }
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setLoading(true);
    try {
      await googleLogin(credentialResponse.credential);
      toast.success("Google authentication successful!");
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || "Google authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-950 flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 relative overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-purple-500/20 rounded-full animate-pulse"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${1 + Math.random()}s`
              }}
            />
          ))}
        </div>
        
        <div className="relative z-10 text-center">
          <div className="w-24 h-24 bg-gradient-to-br from-pink-500/20 to-purple-500/20 border-2 border-pink-500 rounded-xl flex items-center justify-center mx-auto mb-6 relative">
            <Plane className="w-12 h-12 text-pink-400" />
            <div className="absolute -top-2 -right-2 w-4 h-4 bg-blue-400 rounded-full animate-pulse"></div>
          </div>
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono tracking-wider mb-4">
            INFOPILOT EXPLORER
          </h1>
          <p className="text-purple-300/70 font-mono text-lg mb-8">TACTICAL SEARCH v2.0</p>
          
          {/* Book Promo */}
          <div className="mt-8 p-6 bg-slate-900/50 border border-purple-500/30 rounded-xl max-w-md">
            <img src={IMAGES.bookCoverMain} alt="Letters to Evelyn" className="w-32 h-44 object-cover rounded-lg shadow-xl mx-auto mb-4" />
            <h3 className="text-xl font-bold text-pink-400 font-mono">LETTERS TO EVELYN</h3>
            <div className="flex justify-center gap-1 my-2">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              ))}
            </div>
            <p className="text-purple-300/70 font-mono text-sm">{BOOK_INFO.genre}</p>
            <a
              href={BOOK_INFO.amazonUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono text-sm rounded hover:scale-105 transition-transform"
            >
              <ExternalLink className="w-4 h-4" />
              GET ON AMAZON
            </a>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-pink-500/20 to-purple-500/20 border-2 border-pink-500 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Plane className="w-8 h-8 text-pink-400" />
            </div>
            <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">
              INFOPILOT EXPLORER
            </h1>
          </div>

          <div className="bg-slate-900/80 border border-purple-500/30 rounded-xl p-8">
            <h2 className="text-2xl font-bold text-pink-400 font-mono mb-6 text-center">
              {isLogin ? "PILOT LOGIN" : "NEW PILOT REGISTRATION"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div>
                  <label className="block text-purple-400 font-mono text-sm mb-2">CALLSIGN</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400" />
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full bg-slate-800/50 border border-purple-500/50 rounded-lg pl-10 pr-4 py-3 text-purple-200 font-mono focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-500/30"
                      placeholder="Your callsign"
                      required={!isLogin}
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-purple-400 font-mono text-sm mb-2">EMAIL</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-slate-800/50 border border-purple-500/50 rounded-lg pl-10 pr-4 py-3 text-purple-200 font-mono focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-500/30"
                    placeholder="pilot@example.com"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-purple-400 font-mono text-sm mb-2">PASSWORD</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full bg-slate-800/50 border border-purple-500/50 rounded-lg pl-10 pr-12 py-3 text-purple-200 font-mono focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-500/30"
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-purple-400 hover:text-pink-400"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-pink-600 to-purple-600 text-white font-bold font-mono py-3 rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Lock className="w-5 h-5" />
                    {isLogin ? "AUTHENTICATE" : "REGISTER"}
                  </>
                )}
              </button>
            </form>

            {/* Google OAuth */}
            {GOOGLE_CLIENT_ID && (
              <>
                <div className="flex items-center gap-4 my-6">
                  <div className="flex-1 h-px bg-purple-500/30"></div>
                  <span className="text-purple-400/70 font-mono text-sm">OR</span>
                  <div className="flex-1 h-px bg-purple-500/30"></div>
                </div>

                <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
                  <div className="flex justify-center">
                    <GoogleLogin
                      onSuccess={handleGoogleSuccess}
                      onError={() => toast.error("Google login failed")}
                      theme="filled_black"
                      shape="pill"
                      text={isLogin ? "signin_with" : "signup_with"}
                      width="300"
                    />
                  </div>
                </GoogleOAuthProvider>
              </>
            )}

            {/* Toggle */}
            <p className="text-center mt-6 text-purple-400/70 font-mono text-sm">
              {isLogin ? "New pilot?" : "Already registered?"}{" "}
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-pink-400 hover:text-pink-300 underline"
              >
                {isLogin ? "Register here" : "Login here"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
