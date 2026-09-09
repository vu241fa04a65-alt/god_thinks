import React from 'react';
import { MapDashboard } from '../components/MapDashboard';
import { ShieldCheck, Info } from 'lucide-react';

export const Community: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Page Title & Intro */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-100 px-3 py-1 rounded-full">
            GIS Epidemiology & Surveillance
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mt-2">
            Community Outbreak Surveillance Map
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time GeoJSON disease clustering, hotspot intensity heatmaps, and field report inspections.
          </p>
        </div>

        <div className="flex items-center gap-2 p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-2xl text-xs font-semibold">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Surveillance Perimeter: Active</span>
        </div>
      </div>

      {/* MapDashboard Component Embed */}
      <MapDashboard />

      {/* Information Banner */}
      <div className="p-4 bg-white rounded-2xl border border-gray-100 shadow-sm flex items-start gap-3 text-xs text-gray-600">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-gray-800">How Outbreak Clusters Work: </span>
          When farmers upload crop leaf scans with GPS or village metadata, neural predictions are aggregated by spatial radius. Hotspots exceeding 10 verified cases trigger automated SMS alerts to adjacent registered farmers.
        </div>
      </div>
    </div>
  );
};
