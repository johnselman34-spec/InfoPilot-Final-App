/**
 * InfoPilot Explorer - Auth Context
 */
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../utils/api';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(() => !!localStorage.getItem("token"));

  useEffect(() => {
    let isMounted = true;
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      axios.get(`${API}/auth/me`)
        .then(res => { if (isMounted) setUser(res.data); })
        .catch(() => { if (isMounted) { localStorage.removeItem("token"); setToken(null); } })
        .finally(() => { if (isMounted) setLoading(false); });
    }
    return () => { isMounted = false; };
  }, [token]);

  const login = (data) => {
    localStorage.setItem("token", data.token);
    axios.defaults.headers.common["Authorization"] = `Bearer ${data.token}`;
    setToken(data.token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;
