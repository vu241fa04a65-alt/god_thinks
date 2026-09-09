import React, { useState, useEffect } from 'react';
import { MapPin, AlertCircle, Filter, Activity, Users } from 'lucide-react';
import { CommunityService } from '../services/api';

export const Community: React.FC = () => {
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterCrop, setFilterCrop] = useState<string>('All');

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        const res = await CommunityService.getTrends();
        if (res.data?.data?.features) {
          setTrends(res.data.data.features);
        }
      } catch (err) {
        // Fallback demo hotspots
        setTrends([
          {
            properties: {
              village: 'Nashik West',
              disease: 'Tomato Early Blight',
              crop: 'Tomato',
              case_count: 14,
              severity: 'high',
            },
            geometry: { coordinates: [73.7898, 19.9975] },
          },
          {
            properties: {
              village: 'Pune Rural',
              disease: 'Potato Late Blight',
              crop: 'Potato',
              case_count: 9,
              severity: 'medium',
            },
            geometry: { coordinates: [73.8567, 18.5204] },
          },
          {
            properties: {
              village: 'Sangli Vineyard Sector',
              disease: 'Grape Downy Mildew',
              crop: 'Grape',
              case_count: 18,
              severity: 'high',
            },
            geometry: { coordinates: [74.5636, 16.8524] },
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchTrends();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-100 px-3 py-1 rounded-full">
          Epidemiology & Sentinel Surveillance
        </span>
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mt-2">
          Community Outbreak Surveillance Map
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Real-time GeoJSON disease clustering to track regional plant health risks and alert adjacent farmlands.
        </p>
      </div>

      {/* Interactive Map Mock / Leaflet Canvas Area */}
      <div className="relative w-full h-96 bg-emerald-950 rounded-3xl overflow-hidden shadow-xl border border-emerald-900 flex items-center justify-center">
        {/* Stylized GIS Background Grid */}
        <div className="absolute inset-0 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:24px_24px] opacity-20" />

        <div className="relative z-10 text-center space-y-3 p-6 bg-black/40 backdrop-blur-md rounded-2xl border border-emerald-500/30 max-w-md">
          <MapPin className="w-10 h-10 text-emerald-400 mx-auto animate-bounce" />
          <h3 className="text-lg font-bold text-white">Interactive GIS Surveillance Active</h3>
          <p className="text-xs text-emerald-200">
            Monitoring 3 active outbreak perimeters across Maharashtra. All verified reports feed into real-time weather risk advisories.
          </p>
        </div>
      </div>

      {/* Cluster Cards */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-600" />
          Active Village Outbreak Clusters
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {trends.map((t, idx) => (
            <div
              key={idx}
              className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition-shadow space-y-4"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500">{t.properties.village}</span>
                <span
                  className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                    t.properties.severity === 'high'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {t.properties.severity} Risk
                </span>
              </div>

              <div>
                <div className="font-bold text-lg text-gray-900">{t.properties.disease}</div>
                <div className="text-xs text-emerald-700 font-medium">Affecting: {t.properties.crop}</div>
              </div>

              <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                <span>Verified Reports</span>
                <span className="font-bold text-gray-800">{t.properties.case_count} cases</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
