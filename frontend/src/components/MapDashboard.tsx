import React, { useState, useEffect, useMemo } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import {
  MapPin,
  Flame,
  Layers,
  Calendar,
  Filter,
  X,
  ShieldAlert,
  ChevronRight,
  ExternalLink,
  Locate,
  Eye,
  Sliders,
} from 'lucide-react';
import {
  MapService,
  GeoJSONFeature,
  MapTrendsFilter,
} from '../services/mapService';

// Fix default Leaflet icon assets
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Helper component to recenter map view programmatically
const ChangeMapView: React.FC<{ center: [number, number]; zoom: number }> = ({
  center,
  zoom,
}) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
};

// Create custom colored clustered SVG marker icon
const createCustomMarkerIcon = (
  riskLevel: 'Low' | 'Moderate' | 'High',
  count: number
) => {
  let bgColor = '#10b981'; // emerald
  let borderColor = '#059669';
  let pulseColor = 'rgba(16, 185, 129, 0.4)';

  if (riskLevel === 'High' || count >= 10) {
    bgColor = '#ef4444'; // red
    borderColor = '#b91c1c';
    pulseColor = 'rgba(239, 68, 68, 0.5)';
  } else if (riskLevel === 'Moderate' || count >= 4) {
    bgColor = '#f59e0b'; // amber
    borderColor = '#d97706';
    pulseColor = 'rgba(245, 158, 11, 0.4)';
  }

  const size = Math.min(52, Math.max(32, 28 + count * 1.2));

  return L.divIcon({
    className: 'custom-cluster-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background-color: ${bgColor};
        border: 3px solid ${borderColor};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 800;
        font-size: ${size > 36 ? '13px' : '11px'};
        box-shadow: 0 4px 12px ${pulseColor};
        cursor: pointer;
        transition: transform 0.2s ease;
      ">
        ${count}
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
};

const DISEASE_OPTIONS = [
  'All',
  'Tomato Early Blight',
  'Tomato Late Blight',
  'Potato Late Blight',
  'Grape Downy Mildew',
  'Wheat Yellow Rust',
  'Corn Common Rust',
  'Apple Scab',
];

export const MapDashboard: React.FC = () => {
  const [features, setFeatures] = useState<GeoJSONFeature[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filter States
  const [selectedDisease, setSelectedDisease] = useState<string>('All');
  const [dateRange, setDateRange] = useState<string>('all'); // 'all', '7d', '30d'
  const [radiusKm, setRadiusKm] = useState<number>(100);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Layer Toggles
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true);
  const [showMarkers, setShowMarkers] = useState<boolean>(true);

  // Map center and inspection side-panel state
  const [mapCenter, setMapCenter] = useState<[number, number]>([19.7515, 75.7139]); // Maharashtra center
  const [zoomLevel, setZoomLevel] = useState<number>(6);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [reportDetails, setReportDetails] = useState<any | null>(null);

  // Overlay opacity in side-panel
  const [overlayOpacity, setOverlayOpacity] = useState<number>(0.75);

  const loadData = async () => {
    setLoading(true);
    const filter: MapTrendsFilter = {
      disease: selectedDisease,
    };

    if (dateRange === '7d') {
      const d = new Date();
      d.setDate(d.getDate() - 7);
      filter.since = d.toISOString().split('T')[0];
    } else if (dateRange === '30d') {
      const d = new Date();
      d.setDate(d.getDate() - 30);
      filter.since = d.toISOString().split('T')[0];
    }

    try {
      const data = await MapService.getTrendsGeoJSON(filter);
      setFeatures(data.features || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDisease, dateRange]);

  // Filtered by text query
  const filteredFeatures = useMemo(() => {
    if (!searchQuery.trim()) return features;
    const q = searchQuery.toLowerCase();
    return features.filter(
      (f) =>
        f.properties.location.toLowerCase().includes(q) ||
        f.properties.disease.toLowerCase().includes(q) ||
        (f.properties.crop && f.properties.crop.toLowerCase().includes(q))
    );
  }, [features, searchQuery]);

  // Handle Marker Click -> Fetch report & open side panel
  const handleMarkerClick = async (feature: GeoJSONFeature) => {
    setSelectedReport(feature.properties);
    setReportDetails(null);

    // If feature contains valid ID, fetch details from /reports/{id}
    if (feature.properties.id) {
      const details = await MapService.getReportDetails(feature.properties.id);
      setReportDetails(details);
    }
  };

  // Center on User GPS
  const handleLocateMe = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setMapCenter([pos.coords.latitude, pos.coords.longitude]);
          setZoomLevel(9);
        },
        () => {
          // fallback
        }
      );
    }
  };

  return (
    <div className="relative w-full h-[780px] bg-slate-900 rounded-3xl overflow-hidden shadow-2xl border border-slate-800 flex flex-col">
      {/* Top Filter & Control Toolbar */}
      <div className="bg-slate-900/90 backdrop-blur-md p-4 border-b border-slate-800 z-20 flex flex-wrap items-center justify-between gap-4">
        {/* Title & Stats */}
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">
              GIS Outbreak Surveillance
            </h2>
            <div className="text-[11px] text-slate-400">
              {filteredFeatures.length} Active Hotspot Clusters • Auto-refresh
            </div>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Disease Filter */}
          <select
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {DISEASE_OPTIONS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          {/* Date Range Selector */}
          <div className="flex bg-slate-800 rounded-xl p-0.5 border border-slate-700">
            {(['all', '7d', '30d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setDateRange(range)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg capitalize transition-all ${
                  dateRange === range
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {range === 'all' ? 'All Time' : `Last ${range}`}
              </button>
            ))}
          </div>

          {/* Heatmap Layer Toggle */}
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              showHeatmap
                ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            Heatmap {showHeatmap ? 'ON' : 'OFF'}
          </button>

          {/* GPS Locate Button */}
          <button
            onClick={handleLocateMe}
            title="Recenter on My Location"
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-emerald-400 border border-slate-700 rounded-xl transition-all"
          >
            <Locate className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Map Canvas Area */}
      <div className="relative flex-1 w-full h-full">
        <MapContainer
          center={mapCenter}
          zoom={zoomLevel}
          scrollWheelZoom={true}
          className="w-full h-full z-10"
        >
          <ChangeMapView center={mapCenter} zoom={zoomLevel} />

          {/* OpenStreetMap Base Tile Layer */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Heatmap intensity buffers (rendered as semi-transparent GIS circles) */}
          {showHeatmap &&
            filteredFeatures.map((f, idx) => {
              const coords: [number, number] = [
                f.geometry.coordinates[1],
                f.geometry.coordinates[0],
              ];
              const isHigh =
                f.properties.risk_level === 'High' || f.properties.count >= 10;
              const radius = Math.min(
                35000,
                Math.max(12000, f.properties.count * 2000)
              );

              return (
                <Circle
                  key={`heat-${idx}`}
                  center={coords}
                  radius={radius}
                  pathOptions={{
                    fillColor: isHigh ? '#ef4444' : '#f59e0b',
                    fillOpacity: isHigh ? 0.35 : 0.2,
                    color: isHigh ? '#dc2626' : '#d97706',
                    weight: 1.5,
                  }}
                />
              );
            })}

          {/* Clustered / Colored Outbreak Markers */}
          {showMarkers &&
            filteredFeatures.map((f, idx) => {
              const coords: [number, number] = [
                f.geometry.coordinates[1],
                f.geometry.coordinates[0],
              ];
              return (
                <Marker
                  key={`marker-${idx}`}
                  position={coords}
                  icon={createCustomMarkerIcon(
                    f.properties.risk_level,
                    f.properties.count
                  )}
                  eventHandlers={{
                    click: () => handleMarkerClick(f),
                  }}
                >
                  <Popup>
                    <div className="p-1 max-w-[200px]">
                      <div className="font-bold text-xs text-gray-900">
                        {f.properties.disease}
                      </div>
                      <div className="text-[11px] text-gray-600">
                        {f.properties.location}
                      </div>
                      <div className="mt-1 flex items-center justify-between text-[10px]">
                        <span className="font-semibold text-emerald-700">
                          {f.properties.count} reports
                        </span>
                        <span
                          className={`font-bold uppercase ${
                            f.properties.risk_level === 'High'
                              ? 'text-red-600'
                              : 'text-amber-600'
                          }`}
                        >
                          {f.properties.risk_level}
                        </span>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
        </MapContainer>

        {/* Floating Side Panel for Selected Outbreak / Report Details */}
        {selectedReport && (
          <div className="absolute top-4 right-4 bottom-4 w-96 max-w-[92vw] bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 z-30 flex flex-col overflow-hidden animate-in slide-in-from-right duration-300">
            {/* Panel Header */}
            <div className="p-4 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="p-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg text-xs">
                  🔬
                </span>
                <div>
                  <h3 className="font-bold text-sm leading-tight">
                    {selectedReport.disease}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {selectedReport.location}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedReport(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Panel Content Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs text-gray-700">
              {/* Severity & Count Bar */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold">
                    Cluster Size
                  </div>
                  <div className="text-xl font-black text-gray-900">
                    {selectedReport.count} <span className="text-xs font-normal text-gray-500">cases</span>
                  </div>
                </div>

                <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold">
                    Outbreak Severity
                  </div>
                  <div
                    className={`text-xl font-black ${
                      selectedReport.risk_level === 'High'
                        ? 'text-red-600'
                        : 'text-amber-600'
                    }`}
                  >
                    {selectedReport.risk_level}
                  </div>
                </div>
              </div>

              {/* Crop Leaf Photo & Grad-CAM Overlay Visualizer */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-gray-900 text-xs flex items-center gap-1.5">
                    <Eye className="w-3.5 h-3.5 text-emerald-600" />
                    Field Sample & Neural Overlay
                  </span>
                  <span className="text-[10px] text-gray-400 font-mono">
                    Opacity: {Math.round(overlayOpacity * 100)}%
                  </span>
                </div>

                <div className="relative aspect-video bg-gray-950 rounded-xl overflow-hidden shadow-inner border border-gray-200">
                  <img
                    src={
                      selectedReport.image_url ||
                      'https://images.unsplash.com/photo-1592417817098-8f3d6ef23a41?auto=format&fit=crop&w=600&q=80'
                    }
                    alt="Leaf specimen"
                    className="w-full h-full object-cover"
                  />

                  {/* Grad-CAM overlay heatmap if present */}
                  {selectedReport.overlay_url && (
                    <img
                      src={selectedReport.overlay_url}
                      alt="Heatmap Overlay"
                      className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                      style={{ opacity: overlayOpacity, mixBlendMode: 'screen' }}
                    />
                  )}
                </div>

                {/* Opacity slider */}
                {selectedReport.overlay_url && (
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.05"
                    value={overlayOpacity}
                    onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                  />
                )}
              </div>

              {/* Verified Treatment Advisory */}
              {reportDetails?.treatment_advisory && (
                <div className="p-3 bg-emerald-50/80 rounded-xl border border-emerald-200 space-y-1.5">
                  <div className="font-bold text-emerald-950 text-xs">
                    💡 Agronomist Advisory:
                  </div>
                  <p className="text-[11px] text-emerald-900">
                    {reportDetails.treatment_advisory.treatment ||
                      'Foliar spray of organic copper or neem extract recommended.'}
                  </p>
                </div>
              )}

              {/* Last Detection Timestamp */}
              <div className="text-[11px] text-gray-400 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                Latest detection:{' '}
                {selectedReport.last_seen
                  ? new Date(selectedReport.last_seen).toLocaleDateString()
                  : 'Today'}
              </div>
            </div>

            {/* Panel Footer */}
            <div className="p-3 bg-gray-50 border-t border-gray-100 flex gap-2">
              <a
                href="/report"
                className="flex-1 py-2 text-center bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs transition-colors shadow-sm"
              >
                Submit Leaf Sample Here
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Map Footer Legend */}
      <div className="bg-slate-900 p-3 px-6 border-t border-slate-800 text-xs text-slate-400 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <span className="font-semibold text-white">Legend:</span>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500 border border-red-700" />
            <span>High Severity (&gt; 10 cases)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-amber-500 border border-amber-700" />
            <span>Moderate Severity (4-9 cases)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500 border border-emerald-700" />
            <span>Low / Controlled (&lt; 4 cases)</span>
          </div>
        </div>

        <div>Data synchronized with ICAR and state agro-surveillance nodes</div>
      </div>
    </div>
  );
};
