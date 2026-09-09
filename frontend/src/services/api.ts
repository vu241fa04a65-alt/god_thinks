import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Storage token helpers
export const getAccessToken = (): string | null => localStorage.getItem('access_token');
export const getRefreshToken = (): string | null => localStorage.getItem('refresh_token');
export const setTokens = (access: string, refresh?: string) => {
  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
};
export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_info');
};

// Request Interceptor: Attach Bearer JWT
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Token Refresh on 401
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If 401 Unauthorized and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
        return Promise.reject(error);
      }

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearTokens();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const data = response.data.data;
        const newAccessToken = data.access_token;
        setTokens(newAccessToken, data.refresh_token);

        processQueue(null, newAccessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// High-level API Service Handlers
export const ReportService = {
  uploadReport: async (
    formData: FormData,
    onUploadProgress?: (progressEvent: any) => void
  ) => {
    return api.post('/reports/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
  },
  listReports: async (skip = 0, limit = 20) => {
    return api.get(`/reports/?skip=${skip}&limit=${limit}`);
  },
  getReportById: async (id: number | string) => {
    return api.get(`/reports/${id}`);
  },
};

export const ExpertService = {
  getPendingReports: async (skip = 0, limit = 20) => {
    return api.get(`/expert/pending?skip=${skip}&limit=${limit}`);
  },
  validateReport: async (payload: { report_id: number; decision: 'approve' | 'reject'; notes?: string }) => {
    return api.post('/expert/validate', payload);
  },
  getAuditTrail: async (limit = 50) => {
    return api.get(`/expert/audit-trail?limit=${limit}`);
  },
};

export const CommunityService = {
  submitReport: async (payload: any) => {
    return api.post('/community/report', payload);
  },
  getTrends: async (params?: { bbox?: string; disease?: string; since?: string }) => {
    return api.get('/community/trends', { params });
  },
  getNearbyReports: async (lat: number, lng: number, radius = 50) => {
    return api.get(`/community/nearby?lat=${lat}&lng=${lng}&radius=${radius}`);
  },
};

export const GamificationService = {
  getPoints: async (userId?: number) => {
    return api.get('/gamification/points', { params: userId ? { user_id: userId } : undefined });
  },
  getLeaderboard: async (limit = 50) => {
    return api.get(`/gamification/leaderboard?limit=${limit}`);
  },
  getCatalog: async () => {
    return api.get('/gamification/catalog');
  },
  claimReward: async (rewardItemId: string, userId?: number) => {
    return api.post('/gamification/claim', { reward_item_id: rewardItemId, user_id: userId });
  },
  awardAction: async (action: string, userId?: number) => {
    return api.post('/gamification/action', { action, user_id: userId });
  },
  awardPoints: async (points: number, reason: string, userId?: number) => {
    return api.post('/gamification/reward', { points, reason, user_id: userId });
  },
};

export const WeatherService = {
  getRisk: async (lat: number, lng: number, crop: string) => {
    return api.get(`/weather/risk?lat=${lat}&lng=${lng}&crop=${crop}`);
  },
};

export const AdvisoryService = {
  getRecommendations: async (crop: string, disease: string, region?: string) => {
    return api.get('/advisory/recommend', { params: { crop, disease, region } });
  },
};

export const ChatbotService = {
  getAdvice: async (payload: {
    message: string;
    language: string;
    context?: Record<string, any>;
  }) => {
    return api.post('/chatbot/advice', payload);
  },
};
