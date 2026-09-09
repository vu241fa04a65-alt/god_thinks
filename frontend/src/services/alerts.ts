import { api } from './api';

export interface AlertSubscriptionPayload {
  phone: string;
  preferred_language?: string;
  geofence_radius_km?: number;
  location?: string;
  lat?: number;
  lng?: number;
  user_id?: number;
}

export interface AlertSubscriptionResponse {
  user_id: number;
  phone: string;
  sms_opt_in: boolean;
  preferred_language: string;
  geofence_radius_km: number;
  location?: string;
  opt_in_code: string;
  confirmation_dispatched: boolean;
  message: string;
}

export const AlertService = {
  /**
   * Subscribe farmer to hyper-local SMS outbreak alerts
   */
  subscribe: async (payload: AlertSubscriptionPayload): Promise<AlertSubscriptionResponse> => {
    const response = await api.post('/alerts/subscribe', payload);
    return response.data?.data;
  },

  /**
   * Unsubscribe phone number or user from alerts
   */
  unsubscribe: async (phone: string, userId?: number): Promise<any> => {
    const response = await api.post('/alerts/unsubscribe', {
      phone,
      user_id: userId,
    });
    return response.data?.data;
  },

  /**
   * Get current subscription settings
   */
  getStatus: async (phone?: string, userId?: number): Promise<any> => {
    const response = await api.get('/alerts/status', {
      params: { phone, user_id: userId },
    });
    return response.data?.data;
  },
};
