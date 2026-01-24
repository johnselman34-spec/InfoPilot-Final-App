import React, { useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../utils/api";

const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = location.hash;
      const sessionId = new URLSearchParams(hash.substring(1)).get("session_id");

      if (sessionId) {
        try {
          const response = await api.post("/auth/session", { session_id: sessionId });
          setUser(response.data);
          navigate("/dashboard", { replace: true, state: { user: response.data } });
        } catch (error) {
          console.error("Auth error:", error);
          navigate("/", { replace: true });
        }
      } else {
        navigate("/", { replace: true });
      }
    };

    processAuth();
  }, [location, navigate, setUser]);

  return (
    <div className="min-h-screen bg-ivory flex items-center justify-center">
      <div className="spinner"></div>
    </div>
  );
};

export default AuthCallback;
