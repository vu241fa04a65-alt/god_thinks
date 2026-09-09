import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, Sparkles, MapPin, Award, CheckCircle2, ArrowRight, Activity, CloudSun } from 'lucide-react';
import { UploadForm } from '../components/UploadForm';
import { DiseaseResult } from '../components/DiseaseResultCard';

export const Home: React.FC = () => {
  const navigate = useNavigate();

  const handleQuickUploadComplete = (result: DiseaseResult) => {
    // Navigate to report page or pass result via state
    navigate('/report', { state: { initialResult: result } });
  };

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-900 via-emerald-800 to-teal-900 text-white px-8 py-16 lg:py-24 shadow-2xl">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-6">
          <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
            🌱 Next-Gen Agro AI & Computer Vision
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            Protecting Harvests with <span className="text-emerald-400">Explainable AI</span>
          </h1>
          <p className="text-lg text-emerald-100/90 leading-relaxed">
            Diagnose plant diseases from leaf photos in seconds. View Grad-CAM neural overlays, hyper-local microclimate risk forecasts, and receive expert-validated eco-friendly treatment plans.
          </p>

          <div className="flex flex-wrap gap-4 pt-4">
            <Link
              to="/report"
              className="px-6 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-emerald-950 font-bold text-sm shadow-lg shadow-emerald-900/40 transition-all flex items-center gap-2"
            >
              Start Leaf Scout
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/community"
              className="px-6 py-3.5 rounded-xl bg-emerald-800/80 hover:bg-emerald-800 text-white font-semibold text-sm border border-emerald-600/50 transition-all flex items-center gap-2"
            >
              <MapPin className="w-4 h-4 text-emerald-400" />
              Outbreak Surveillance Map
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Upload Widget Container */}
      <section className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Instant Field Diagnosis</h2>
          <p className="text-sm text-gray-500 mt-1">Try the AI vision model directly right now</p>
        </div>
        <UploadForm onDiagnosisComplete={handleQuickUploadComplete} />
      </section>

      {/* Value Pillars */}
      <section className="max-w-6xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">Explainable AI (Grad-CAM)</h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            Transparent neural networks visualize infected leaf lesions via heatmaps, pinpointing concentric rings and chlorosis cues.
          </p>
        </div>

        <div className="p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center mb-4">
            <CloudSun className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">Hyper-Local Weather Risk</h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            Microclimate humidity, leaf-wetness, and precipitation models forecast fungal and pest susceptibility before outbreaks occur.
          </p>
        </div>

        <div className="p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center mb-4">
            <Award className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2">Gamified Community Sentinel</h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            Earn points and agricultural vouchers by scouting first reports in your village and validating regional surveillance data.
          </p>
        </div>
      </section>
    </div>
  );
};
