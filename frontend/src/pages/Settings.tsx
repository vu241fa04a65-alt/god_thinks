import React, { useState, useEffect } from 'react';
import {
  Bell,
  BellOff,
  Phone,
  Globe,
  Radio,
  MapPin,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Shield,
  Send,
} from 'lucide-react';
import { AlertService } from '../services/alerts';
import { useAuth } from '../context/AuthContext';

const LANGUAGES = [
  { code: 'hi', label: 'हिंदी (Hindi)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'en', label: 'English' },
];

export const Settings: React.FC = () => {
  const { user } = useAuth();

  const [phone, setPhone] = useState<string>(user?.phone || '+919876543210');
  const [preferredLanguage, setPreferredLanguage] = useState<string>('hi');
  const [geofenceRadius, setGeofenceRadius] = useState<number>(25);
  const [locationName, setLocationName] = useState<string>('Nashik Rural, Maharashtra');
  const [smsOptIn, setSmsOptIn] = useState<boolean>(true);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [optInConfirmationCode, setOptInConfirmationCode] = useState<string | null>(null);

  // Load existing status on mount
  useEffect(() => {
    const loadStatus = async () => {
      try {
        const data = await AlertService.getStatus(user?.phone || phone, user?.id);
        if (data) {
          if (data.phone) setPhone(data.phone);
          if (data.preferred_language) setPreferredLanguage(data.preferred_language);
          if (data.geofence_radius_km) setGeofenceRadius(data.geofence_radius_km);
          if (data.location) setLocationName(data.location);
          if (data.subscribed !== undefined) setSmsOptIn(data.subscribed);
        }
      } catch (err) {
        // Fallback to defaults
      }
    };

    loadStatus();
  }, [user]);

  // Handle Subscribe / Update Preferences
  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setStatusMessage(null);
    setOptInConfirmationCode(null);

    try {
      if (smsOptIn) {
        const res = await AlertService.subscribe({
          phone,
          preferred_language: preferredLanguage,
          geofence_radius_km: geofenceRadius,
          location: locationName,
          user_id: user?.id,
        });

        setOptInConfirmationCode(res.opt_in_code);
        setStatusMessage({
          type: 'success',
          text: `Preferences saved! Confirmation SMS dispatched to ${phone} with opt-in code ${res.opt_in_code}.`,
        });
      } else {
        await AlertService.unsubscribe(phone, user?.id);
        setStatusMessage({
          type: 'success',
          text: `You have successfully unsubscribed ${phone} from SMS outbreak notifications.`,
        });
      }
    } catch (err: any) {
      const errDetail =
        err.response?.data?.error?.message || err.message || 'Failed to update alert subscription.';
      setStatusMessage({ type: 'error', text: errDetail });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
          Farmer Profile & Alert Settings
        </span>
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mt-2">
          SMS Outbreak Notifications & Geo-Fence
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Configure hyper-local cellular alerts to receive immediate disease outbreak warnings and treatment advice in your native language.
        </p>
      </div>

      {/* Notification Banner */}
      {statusMessage && (
        <div
          className={`p-4 rounded-2xl border text-sm font-medium flex items-center gap-3 animate-in slide-in-from-top-2 ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Form Container */}
      <form
        onSubmit={handleSavePreferences}
        className="bg-white rounded-3xl border border-gray-100 shadow-xl p-8 space-y-8"
      >
        {/* Toggle SMS Opt-in */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-gray-50 border border-gray-200">
          <div className="space-y-1">
            <div className="font-bold text-sm text-gray-900 flex items-center gap-2">
              {smsOptIn ? (
                <Bell className="w-4 h-4 text-emerald-600" />
              ) : (
                <BellOff className="w-4 h-4 text-gray-400" />
              )}
              Cellular SMS Disease Outbreak Alerts
            </div>
            <p className="text-xs text-gray-500">
              Receive automated SMS alerts when regional disease clusters exceed outbreak thresholds in your perimeter.
            </p>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={smsOptIn}
              onChange={(e) => setSmsOptIn(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600" />
          </label>
        </div>

        {/* Form Fields: Phone & Language */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Phone className="w-3.5 h-3.5 text-emerald-600" />
              Mobile Number for Alerts
            </label>
            <input
              type="tel"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 98765 43210"
              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
            />
            <p className="text-[11px] text-gray-400 mt-1">
              Include country code (e.g. +91 for India).
            </p>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-blue-600" />
              Preferred Advisory Language
            </label>
            <select
              value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value)}
              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-gray-400 mt-1">
              SMS messages and dosages will be translated to this language.
            </p>
          </div>
        </div>

        {/* Geo-Fence Perimeter Controls */}
        <div className="p-6 bg-slate-50 rounded-2xl border border-gray-200 space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-1.5">
              <Radio className="w-4 h-4 text-emerald-600" />
              Surveillance Geo-Fence Radius
            </label>
            <span className="text-sm font-extrabold text-emerald-700 px-3 py-1 bg-emerald-100 rounded-full">
              {geofenceRadius} km
            </span>
          </div>

          <input
            type="range"
            min="5"
            max="150"
            step="5"
            value={geofenceRadius}
            onChange={(e) => setGeofenceRadius(parseInt(e.target.value, 10))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
          />

          <div className="flex justify-between text-[11px] text-gray-400">
            <span>5 km (Local Village)</span>
            <span>50 km (Sub-district)</span>
            <span>150 km (Regional Sector)</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-gray-400" />
              Primary Farm Location / Village
            </label>
            <input
              type="text"
              value={locationName}
              onChange={(e) => setLocationName(e.target.value)}
              placeholder="e.g. Nashik Valley, Maharashtra"
              className="w-full px-3.5 py-2.5 bg-white border border-gray-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Opt-In Code Preview (if newly generated) */}
        {optInConfirmationCode && (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-amber-600" />
              <span>
                Confirmation code issued: <strong className="font-mono text-sm">{optInConfirmationCode}</strong>
              </span>
            </div>
            <span className="text-[10px] text-amber-700 uppercase font-bold bg-amber-200/80 px-2 py-0.5 rounded-full">
              Verified Opt-In
            </span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-2xl text-sm transition-all shadow-lg shadow-emerald-200 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Updating Subscription...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Save Alert Preferences & Dispatch Confirmation
            </>
          )}
        </button>
      </form>
    </div>
  );
};
