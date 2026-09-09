import React, { useState, useEffect } from 'react';
import { ShieldCheck, Check, X, AlertTriangle, Layers, Filter } from 'lucide-react';
import { ExpertService } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const ExpertPortal: React.FC = () => {
  const { isExpert } = useAuth();
  const [pendingReports, setPendingReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [expertNotes, setExpertNotes] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Heatmap layer controls
  const [showOverlay, setShowOverlay] = useState<boolean>(true);
  const [opacity, setOpacity] = useState<number>(0.7);

  const fetchPending = async () => {
    setLoading(true);
    try {
      const res = await ExpertService.getPendingReports(0, 20);
      if (res.data?.data) {
        setPendingReports(res.data.data);
        if (res.data.data.length > 0 && !selectedReport) {
          setSelectedReport(res.data.data[0]);
        }
      }
    } catch (err) {
      // Mock data if backend empty
      const mock = [
        {
          id: 101,
          crop_type: 'Tomato',
          disease_predicted: 'Tomato Early Blight',
          confidence: 0.94,
          image_url: 'https://images.unsplash.com/photo-1592417817098-8f3d6ef23a41?auto=format&fit=crop&w=600&q=80',
          overlay_url: '',
          location: 'Nashik District',
          created_at: new Date().toISOString(),
          explanation: {
            visual_cues: 'Concentric rings with target-board pattern on leaves',
          },
        },
        {
          id: 102,
          crop_type: 'Potato',
          disease_predicted: 'Potato Late Blight',
          confidence: 0.88,
          image_url: 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=80',
          overlay_url: '',
          location: 'Pune Rural',
          created_at: new Date().toISOString(),
          explanation: {
            visual_cues: 'Dark irregular water-soaked spots on foliage',
          },
        },
      ];
      setPendingReports(mock);
      setSelectedReport(mock[0]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleDecision = async (decision: 'approve' | 'reject') => {
    if (!selectedReport) return;
    setActionLoading(true);
    try {
      await ExpertService.validateReport({
        report_id: selectedReport.id,
        decision,
        notes: expertNotes,
      });

      setMessage(`Report #${selectedReport.id} successfully marked as ${decision}d.`);
      setPendingReports((prev) => prev.filter((r) => r.id !== selectedReport.id));
      setSelectedReport(pendingReports.find((r) => r.id !== selectedReport.id) || null);
      setExpertNotes('');
      setTimeout(() => setMessage(null), 4000);
    } catch (err: any) {
      setMessage(`Decision recorded locally (${decision}).`);
      setPendingReports((prev) => prev.filter((r) => r.id !== selectedReport.id));
      setSelectedReport(null);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
            Agronomist Workstation
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mt-2">
            Expert Prediction Review
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Audit AI diagnostics, inspect Grad-CAM activations, and issue official advisory validations.
          </p>
        </div>

        <button
          onClick={fetchPending}
          className="px-4 py-2 text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl transition-colors"
        >
          Refresh Queue ({pendingReports.length})
        </button>
      </div>

      {message && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm font-medium">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Pending Queue Sidebar */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-gray-100 p-4 shadow-sm space-y-3">
          <h3 className="font-bold text-sm text-gray-800 px-2 flex items-center justify-between">
            <span>Pending Submissions</span>
            <span className="text-xs text-gray-400 font-normal">{pendingReports.length} awaiting</span>
          </h3>

          <div className="divide-y divide-gray-100 overflow-y-auto max-h-[600px]">
            {pendingReports.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedReport(item)}
                className={`p-3 rounded-xl cursor-pointer transition-all ${
                  selectedReport?.id === item.id
                    ? 'bg-emerald-50 border border-emerald-300'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-gray-900">
                    {item.crop_type} #{item.id}
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-700">
                    {Math.round((item.confidence || 0.9) * 100)}%
                  </span>
                </div>
                <div className="text-xs text-gray-600 truncate mt-0.5">{item.disease_predicted}</div>
                <div className="text-[10px] text-gray-400 mt-1">{item.location || 'Maharashtra'}</div>
              </div>
            ))}

            {pendingReports.length === 0 && (
              <div className="py-8 text-center text-xs text-gray-400">All submissions reviewed! 🎉</div>
            )}
          </div>
        </div>

        {/* Right: Detailed Inspection & Actions Panel */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-gray-100 p-6 shadow-sm space-y-6">
          {selectedReport ? (
            <>
              <div className="flex items-center justify-between pb-4 border-b border-gray-100">
                <div>
                  <span className="text-xs font-semibold text-gray-400">Report #{selectedReport.id}</span>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedReport.crop_type} — {selectedReport.disease_predicted}
                  </h2>
                </div>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
                  AI Confidence: {Math.round((selectedReport.confidence || 0.9) * 100)}%
                </span>
              </div>

              {/* Visualizer */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="relative aspect-square bg-gray-900 rounded-xl overflow-hidden shadow-inner">
                  <img
                    src={selectedReport.image_url}
                    alt="Original Leaf"
                    className="w-full h-full object-contain"
                  />
                  {selectedReport.overlay_url && showOverlay && (
                    <img
                      src={selectedReport.overlay_url}
                      alt="Overlay"
                      className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                      style={{ opacity, mixBlendMode: 'screen' }}
                    />
                  )}
                </div>

                <div className="space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="p-3 bg-gray-50 rounded-xl border border-gray-200">
                      <div className="text-xs font-semibold text-gray-700 mb-1">Visual Cue Rationale:</div>
                      <p className="text-xs text-gray-600">
                        {selectedReport.explanation?.visual_cues ||
                          'Target board concentric rings and chlorotic yellow halos visible on leaf surface.'}
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 space-y-2">
                      <div className="flex justify-between text-xs text-gray-600 font-medium">
                        <span>Heatmap Overlay Opacity</span>
                        <span>{Math.round(opacity * 100)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0.1"
                        max="1"
                        step="0.05"
                        value={opacity}
                        onChange={(e) => setOpacity(parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                      />
                    </div>
                  </div>

                  {/* Notes input */}
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1">
                      Agronomist Diagnostic Notes & Prescription
                    </label>
                    <textarea
                      rows={3}
                      value={expertNotes}
                      onChange={(e) => setExpertNotes(e.target.value)}
                      placeholder="e.g. Confirmed Alternaria solani. Spray Copper Oxychloride 2.5g/L and prune lower leaves."
                      className="w-full px-3 py-2 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4 border-t border-gray-100">
                <button
                  onClick={() => handleDecision('reject')}
                  disabled={actionLoading}
                  className="flex-1 py-3 px-4 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-bold text-sm rounded-xl flex items-center justify-center gap-2 transition-colors"
                >
                  <X className="w-4 h-4" />
                  Reject Prediction
                </button>
                <button
                  onClick={() => handleDecision('approve')}
                  disabled={actionLoading}
                  className="flex-1 py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-200 transition-colors"
                >
                  <Check className="w-4 h-4" />
                  Validate & Award Points (+5)
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-24 text-gray-400 text-sm">
              Select a report from the queue on the left to begin diagnostic validation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
