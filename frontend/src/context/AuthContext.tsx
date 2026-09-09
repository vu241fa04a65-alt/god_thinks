import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, setTokens, clearTokens, getAccessToken } from '../services/api';

export interface User {
  id: number;
  email: string;
  name: string;
  phone?: string;
  role: 'farmer' | 'expert' | 'admin';
  points: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<any>;
  register: (payload: any) => Promise<any>;
  logout: () => void;
  isExpert: boolean;
  updatePoints: (newPoints: number) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user_info');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(getAccessToken);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (token && !user) {
      // Attempt to load points / profile if token exists
      api
        .get('/gamification/points')
        .then((res) => {
          if (res.data?.data) {
            const d = res.data.data;
            const updatedUser: User = {
              id: d.user_id,
              email: d.user_email || 'user@example.com',
              name: d.user_name || 'Agri User',
              role: d.user_role || 'farmer',
              points: d.points || 0,
            };
            setUser(updatedUser);
            localStorage.setItem('user_info', JSON.stringify(updatedUser));
          }
        })
        .catch(() => {
          // Token might be invalid
        });
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.post('/auth/login', { email, password });
      const data = res.data.data;
      setTokens(data.access_token, data.refresh_token);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      return data;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: any) => {
    setIsLoading(true);
    try {
      const res = await api.post('/auth/register', payload);
      return res.data.data;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    setToken(null);
  };

  const updatePoints = (newPoints: number) => {
    if (user) {
      const updated = { ...user, points: newPoints };
      setUser(updated);
      localStorage.setItem('user_info', JSON.stringify(updated));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
        isExpert: user?.role === 'expert' || user?.role === 'admin',
        updatePoints,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
