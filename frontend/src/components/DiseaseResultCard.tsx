import React, { useState } from 'react';
import { Layers, ShieldCheck, Share2, AlertTriangle, CheckCircle2, ChevronRight, ExternalLink, Leaf } from 'lucide-react';
import { AdvisoryCard } from './AdvisoryCard';

export interface DiseaseResult {
  report_id?: number;
  crop_type: string;
  disease_predicted: string;
  confidence: number;
  status?: string;
  image_url: string;
  thumbnail_url?: string;
  overlay_url?: string;
  overlay_base64?: string;
  explanation?: {
    visual_cues?: string;
    infected_boxes?: Array<{
      x_min: number;
      y_min: number;
      x_max: number;
      y_max: number;
      confidence?: number;
    }>;
  };
  recommendations?: Array<{
    category: string;
    name: string;
    dosage?: string;
    phi_days?: number;
    eco_friendly?: boolean;
    instructions?: string;
  }>;
}

interface DiseaseResultCardProps {
  result: DiseaseResult;
  onRequestValidation?: (reportId: number) => void;
}

export const DiseaseResultCard: React.FC<DiseaseResultCardProps> = ({
  result,
  onRequestValidation,
}) => {
  const [showOverlay, setShowOverlay] = useState<boolean>(true);
  const [opacity, setOpacity] = useState<number>(0.75);
  const [blendMode, setBlendMode] = useState<'screen' | 'multiply' | 'overlay' | 'normal'>('screen');
  const [copied, setCopied] = useState<boolean>(false);
  const [validationRequested, setValidationRequested] = useState<boolean>(false);

  // Confidence percentage display
  const confidencePercent = Math.round((result.confidence || 0) * 100);

  // Resolve overlay source (direct overlay URL or base64 data)
  const overlaySrc =
    result.overlay_url ||
    (result.overlay_base64 ? `data:image/png;base64,${result.overlay_base64}` : null);

  const handleShare = async () => {
    const text = `CropHealthAI Alert: Detected ${result.disease_predicted} on ${result.crop_type} (${confidencePercent}% confidence).`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Crop Disease Diagnosis',
          text,
          url: window.location.href,
        });
      } catch (err) {
        // Fallback to clipboard
      }
    } else {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleValidation = () => {
    if (result.report_id && onRequestValidation) {
      onRequestValidation(result.report_id);
      setValidationRequested(true);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden transition-all duration-300 hover:shadow-2xl">
      {/* Header banner */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 p-6 text-white flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/30 text-emerald-100 border border-emerald-400/30 mb-2">
            🌿 {result.crop_type} Diagnosis
          </span>
          <h2 className="text-2xl font-bold tracking-tight">{result.disease_predicted}</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs uppercase tracking-wider text-emerald-200">AI Confidence</div>
            <div className="text-3xl font-extrabold">{confidencePercent}%</div>
          </div>
          <div className="w-14 h-14 rounded-full border-4 border-emerald-400/50 flex items-center justify-center font-bold text-lg bg-emerald-800/40">
            {confidencePercent >= 80 ? '🎯' : '⚠️'}
          </div>
        </div>
      </div>

      {/* Main Grid: Image & Explainability View + Advisory */}
      <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Interactive Image & Grad-CAM Heatmap Viewer */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-600" />
              Visual Inspection & Grad-CAM
            </h3>
            <button
              onClick={() => setShowOverlay(!showOverlay)}
              className={`text-xs px-3 py-1 rounded-lg font-medium transition-all ${
                showOverlay
                  ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {showOverlay ? 'Overlay: ON' : 'Overlay: OFF'}
            </button>
          </div>

          {/* Layered Image Canvas Container */}
          <div className="relative w-full aspect-square bg-gray-900 rounded-xl overflow-hidden shadow-inner border border-gray-200">
            {/* Base Crop Image */}
            <img
              src={result.image_url}
              alt="Analyzed crop sample"
              className="absolute inset-0 w-full h-full object-contain select-none"
            />

            {/* Grad-CAM Heatmap Overlay Layer with CSS Blend Mode & Opacity */}
            {overlaySrc && showOverlay && (
              <img
                src={overlaySrc}
                alt="Grad-CAM heatmap overlay"
                className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-200"
                style={{
                  opacity: opacity,
                  mixBlendMode: blendMode,
                }}
              />
            )}

            {/* Bounding Box Annotations if present */}
            {result.explanation?.infected_boxes?.map((box, idx) => (
              <div
                key={idx}
                className="absolute border-2 border-red-500 bg-red-500/10 pointer-events-none rounded"
                style={{
                  left: `${(box.x_min / 500) * 100}%`,
                  top: `${(box.y_min / 500) * 100}%`,
                  width: `${((box.x_max - box.x_min) / 500) * 100}%`,
                  height: `${((box.y_max - box.y_min) / 500) * 100}%`,
                }}
              >
                <span className="absolute -top-5 left-0 bg-red-600 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
                  Infection #{idx + 1}
                </span>
              </div>
            ))}
          </div>

          {/* Heatmap Controls: Opacity Slider & Blend Modes */}
          {overlaySrc && showOverlay && (
            <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-3">
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span className="font-medium">Heatmap Opacity</span>
                <span className="font-mono">{Math.round(opacity * 100)}%</span>
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

              <div className="flex items-center justify-between pt-1">
                <span className="text-xs text-gray-500 font-medium">Blend Mode:</span>
                <div className="flex gap-1">
                  {(['screen', 'multiply', 'overlay', 'normal'] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setBlendMode(mode)}
                      className={`text-[11px] px-2.5 py-1 rounded capitalize font-medium transition-colors ${
                        blendMode === mode
                          ? 'bg-emerald-600 text-white shadow-sm'
                          : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Visual Cues Sentence */}
          {result.explanation?.visual_cues && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Visual Explanation: </span>
                {result.explanation.visual_cues}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Diagnosis Summary, Recommendations & Actions */}
        <div className="lg:col-span-6 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-1">Prescribed Action Plan</h3>
              <p className="text-sm text-gray-500">
                Integrated Pest Management (IPM) recommendations tailored for {result.crop_type}.
              </p>
            </div>

            {/* Recommendation Cards */}
            <div className="space-y-3">
              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-200/80 px-2 py-0.5 rounded-full">
                    🌱 Biological & Cultural Control
                  </span>
                  <span className="text-xs text-emerald-700 font-medium">Eco-Friendly</span>
                </div>
                <h4 className="font-bold text-emerald-950 text-sm">Trichoderma Viride / Neem Foliar Spray</h4>
                <p className="text-xs text-emerald-900">
                  Spray in the evening hours at 5g/L water. Prune lower infected leaves showing chlorotic rings to stop spore dispersion.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/40 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-blue-800 bg-blue-200/80 px-2 py-0.5 rounded-full">
                    🧪 Chemical Preventive (If Severe)
                  </span>
                  <span className="text-xs text-blue-700 font-medium">PHI: 7 Days</span>
                </div>
                <h4 className="font-bold text-blue-950 text-sm">Mancozeb 75% WP or Copper Oxychloride</h4>
                <p className="text-xs text-blue-900">
                  Dosage: 2.5g/L water. Apply protective spray before incoming rain showers. Observe pre-harvest interval before picking.
                </p>
              </div>
            </div>
          </div>

          {/* Action Button Strip */}
          <div className="pt-4 border-t border-gray-100 flex flex-wrap gap-3">
            <button
              onClick={handleShare}
              className="flex-1 min-w-[130px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 font-medium text-sm transition-all shadow-sm"
            >
              <Share2 className="w-4 h-4 text-gray-500" />
              {copied ? 'Link Copied!' : 'Share Alert'}
            </button>

            {result.report_id && (
              <button
                onClick={handleValidation}
                disabled={validationRequested || result.status === 'validated'}
                className={`flex-1 min-w-[170px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all shadow-sm ${
                  validationRequested || result.status === 'validated'
                    ? 'bg-emerald-100 text-emerald-800 cursor-not-allowed border border-emerald-300'
                    : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-200'
                }`}
              >
                {validationRequested || result.status === 'validated' ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Pending Validation
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4 text-white" />
                    Request Expert Review
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Comprehensive IPM Treatment Advisory */}
      <div className="p-6 sm:p-8 bg-slate-50 border-t border-gray-100">
        <AdvisoryCard
          crop={result.crop_type}
          disease={result.disease_predicted}
          className="shadow-none border border-slate-200"
        />
      </div>
    </div>
  );
};
