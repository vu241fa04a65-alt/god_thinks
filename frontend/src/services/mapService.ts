import { api } from './api';

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number]; // [lng, lat]
  };
  properties: {
    id: number;
    disease: string;
    crop?: string;
    count: number;
    location: string;
    risk_level: 'Low' | 'Moderate' | 'High';
    last_seen?: string;
    severity?: string;
    image_url?: string;
    overlay_url?: string;
  };
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface MapTrendsFilter {
  disease?: string;
  since?: string; // ISO date format YYYY-MM-DD
  bbox?: string; // min_lng,min_lat,max_lng,max_lat
  location?: string;
  radius?: number;
  lat?: number;
  lng?: number;
}

export interface NearbyReportItem {
  id: number;
  report_id: number;
  crop_type: string;
  disease_name?: string;
  location: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  status: string;
  notes?: string;
  image_url?: string;
  overlay_url?: string;
  created_at?: string;
}

export const MapService = {
  /**
   * Fetch GeoJSON clusters & disease trends with optional filters
   */
  getTrendsGeoJSON: async (filters: MapTrendsFilter = {}): Promise<GeoJSONFeatureCollection> => {
    const params: Record<string, any> = {};
    if (filters.disease && filters.disease !== 'All') {
      params.disease = filters.disease;
    }
    if (filters.since) {
      params.since = filters.since;
    }
    if (filters.bbox) {
      params.bbox = filters.bbox;
    }
    if (filters.location) {
      params.location = filters.location;
    }

    try {
      const response = await api.get('/community/trends', { params });
      const data = response.data?.data;
      if (data?.geojson_clusters?.features) {
        return data.geojson_clusters;
      }
    } catch (err) {
      console.warn('MapService.getTrendsGeoJSON fallback triggered:', err);
    }

    // Default fallback hotspots across major agricultural centers in India
    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [73.7898, 19.9975] },
          properties: {
            id: 1,
            disease: 'Tomato Early Blight',
            crop: 'Tomato',
            count: 15,
            location: 'Nashik Valley District',
            risk_level: 'High',
            last_seen: '2026-09-09T08:00:00Z',
            image_url: 'https://images.unsplash.com/photo-1592417817098-8f3d6ef23a41?auto=format&fit=crop&w=600&q=80',
            overlay_url: '',
          },
        },
        {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [74.5636, 16.8524] },
          properties: {
            id: 2,
            disease: 'Grape Downy Mildew',
            crop: 'Grape',
            count: 18,
            location: 'Sangli Vineyard Belt',
            risk_level: 'High',
            last_seen: '2026-09-08T14:30:00Z',
            image_url: 'https://images.unsplash.com/photo-1537640538966-79f369143f8f?auto=format&fit=crop&w=600&q=80',
          },
        },
        {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [73.8567, 18.5204] },
          properties: {
            id: 3,
            disease: 'Potato Late Blight',
            crop: 'Potato',
            count: 8,
            location: 'Pune Agriculture Sector',
            risk_level: 'Moderate',
            last_seen: '2026-09-07T11:20:00Z',
            image_url: 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=80',
          },
        },
        {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [75.3412, 31.1471] },
          properties: {
            id: 4,
            disease: 'Wheat Yellow Rust',
            crop: 'Wheat',
            count: 22,
            location: 'Ludhiana North Basin',
            risk_level: 'High',
            last_seen: '2026-09-09T06:45:00Z',
            image_url: 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=600&q=80',
          },
        },
        {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [78.4867, 17.385] },
          properties: {
            id: 5,
            disease: 'Corn Common Rust',
            crop: 'Corn',
            count: 3,
            location: 'Hyderabad Rural Perimeter',
            risk_level: 'Low',
            last_seen: '2026-09-06T09:15:00Z',
            image_url: 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=600&q=80',
          },
        },
      ],
    };
  },

  /**
   * Fetch nearby individual reports within a radius in km
   */
  getNearbyReports: async (
    lat: number,
    lng: number,
    radiusKm: number = 50,
    limit: number = 25
  ): Promise<NearbyReportItem[]> => {
    try {
      const response = await api.get('/community/nearby', {
        params: { lat, lng, radius_km: radiusKm, limit },
      });
      return response.data?.data?.reports || [];
    } catch (err) {
      console.warn('MapService.getNearbyReports fallback triggered:', err);
      return [];
    }
  },

  /**
   * Fetch specific report details for side-panel inspection
   */
  getReportDetails: async (reportId: number) => {
    try {
      const response = await api.get(`/reports/${reportId}`);
      return response.data?.data;
    } catch (err) {
      return null;
    }
  },
};
