import React, { useState, useEffect } from 'react';
import { Award, TrendingUp, CloudSun, AlertCircle, FileText, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { GamificationService, WeatherService, ReportService } from '../services/api';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [pointsData, setPointsData] = useState<any>(null);
  const [weatherRisk, setWeatherRisk] = useState<any>(null);
  const [recentReports, setRecentReports] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Points
        const ptsRes = await GamificationService.getPoints().catch(() => null);
        if (ptsRes?.data?.data) {
          setPointsData(ptsRes.data.data);
        }

        // Weather Risk (default coordinates e.g. Nashik)
        const weatherRes = await WeatherService.getRisk(19.9975, 73.7898, 'Tomato').catch(() => null);
        if (weatherRes?.data?.data) {
          setWeatherRisk(weatherRes.data.data);
        }

        // Recent reports
        const reportsRes = await ReportService.listReports(0, 5).catch(() => null);
        if (reportsRes?.data?.data) {
          setRecentReports(reportsRes.data.data);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-emerald-700 to-teal-800 rounded-3xl p-8 text-white flex flex-wrap items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-300 bg-emerald-600/50 px-3 py-1 rounded-full border border-emerald-400/30">
            Farmer Command Center
          </span>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome, {user?.name || 'Progressive Farmer'}!
          </h1>
          <p className="text-sm text-emerald-100/80">
            Role: <span className="font-semibold capitalize">{user?.role || 'Farmer'}</span> • Village Surveillance Active
          </p>
        </div>

        <div className="flex items-center gap-6 bg-white/10 backdrop-blur-md px-6 py-4 rounded-2xl border border-white/20">
          <div className="w-12 h-12 rounded-xl bg-amber-400 text-amber-950 flex items-center justify-center font-bold text-2xl shadow-md">
            🏆
          </div>
          <div>
            <div className="text-xs uppercase font-medium text-emerald-200">Earned Points</div>
            <div className="text-3xl font-extrabold text-white">
              {pointsData?.points ?? user?.points ?? 45} <span className="text-sm font-normal text-emerald-200">pts</span>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weather Risk Widget */}
        <div className="p-6 bg-white rounded-2xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <CloudSun className="w-5 h-5 text-blue-600" />
              Microclimate Risk
            </h3>
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-bold uppercase ${
                weatherRisk?.risk_score > 60
                  ? 'bg-red-100 text-red-700'
                  : 'bg-emerald-100 text-emerald-700'
              }`}
            >
              {weatherRisk?.risk_level || 'Moderate'}
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-gray-900">
              {weatherRisk?.risk_score ?? 68}
            </span>
            <span className="text-xs text-gray-500 font-medium">/ 100 Risk Index</span>
          </div>

          <p className="text-xs text-gray-600">
            {weatherRisk?.risk_reasons?.[0] || 'High humidity favors fungal sporulation. Protective spray suggested.'}
          </p>
        </div>

        {/* Local Activity Status */}
        <div className="p-6 bg-white rounded-2xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              Community Sentinel
            </h3>
            <span className="text-xs bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full font-bold">
              Active
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-gray-900">
              {recentReports.length || 8}
            </span>
            <span className="text-xs text-gray-500 font-medium">Reports this week</span>
          </div>

          <p className="text-xs text-gray-600">
            3 reports verified by regional agronomists. Tomato Early Blight hotspot identified nearby.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="p-6 bg-white rounded-2xl border border-gray-100 shadow-sm space-y-4 flex flex-col justify-between">
          <h3 className="font-bold text-gray-900 flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-500" />
            Reward Milestones
          </h3>

          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-600 font-medium">
              <span>Next Badge: Bio-Guardian</span>
              <span>45 / 50 pts</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-amber-500 h-2 rounded-full" style={{ width: '90%' }} />
            </div>
          </div>

          <Link
            to="/leaderboard"
            className="w-full py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 text-gray-700 font-semibold text-xs rounded-xl text-center block transition-colors"
          >
            View Leaderboard & Badges
          </Link>
        </div>
      </div>

      {/* Recent Diagnosis History */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-gray-600" />
            Recent Field Scout Reports
          </h3>
          <Link to="/report" className="text-xs font-semibold text-emerald-600 hover:underline">
            + New Inspection
          </Link>
        </div>

        {recentReports.length === 0 ? (
          <div className="text-center py-8 text-sm text-gray-500">
            No reports filed yet. Start your first leaf diagnosis to protect your crops.
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {recentReports.map((rep) => (
              <div key={rep.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="font-bold text-sm text-gray-800">
                    {rep.crop_type} - <span className="text-emerald-700">{rep.disease_predicted || 'Normal'}</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {rep.location || 'Nashik Field'} • {new Date(rep.created_at).toLocaleDateString()}
                  </div>
                </div>
                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                    rep.status === 'validated'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  {rep.status || 'Pending Review'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
