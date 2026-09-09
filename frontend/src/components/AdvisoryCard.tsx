import React, { useState, useEffect } from 'react';
import {
  Leaf,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Droplets,
  BookOpen,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  FileText,
  Sparkles,
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { AdvisoryService } from '../services/api';

export interface TreatmentItem {
  name: string;
  active_ingredient?: string;
  category?: string;
  dosage: string;
  dosage_ml_per_liter?: number;
  pre_harvest_interval_days: number;
  eco_friendly: boolean;
  safety_notes?: string;
  regional_status?: string;
  regional_warning?: string;
  warning?: string;
  residue_risk?: string;
  residue_level?: 'low' | 'moderate' | 'high';
  rank_score?: number;
  docs_url?: string;
  regulation_url?: string;
}

export interface CulturalPractice {
  practice: string;
  description: string;
  impact?: string;
}

interface AdvisoryCardProps {
  crop: string;
  disease: string;
  region?: string;
  treatments?: TreatmentItem[];
  culturalPractices?: CulturalPractice[];
  className?: string;
  onSelectTreatment?: (treatment: TreatmentItem) => void;
}

const DEFAULT_DOCS_URL = 'https://cibrc.gov.in/';
const DEFAULT_IPM_GUIDE_URL = 'https://agricoop.gov.in/en/Major-Activities';

export const AdvisoryCard: React.FC<AdvisoryCardProps> = ({
  crop,
  disease,
  region = 'Maharashtra',
  treatments: propTreatments,
  culturalPractices: propPractices,
  className = '',
  onSelectTreatment,
}) => {
  const [treatments, setTreatments] = useState<TreatmentItem[]>(propTreatments || []);
  const [practices, setPractices] = useState<CulturalPractice[]>(propPractices || []);
  const [loading, setLoading] = useState<boolean>(!propTreatments);
  const [selectedRegion, setSelectedRegion] = useState<string>(region);
  const [expandedTreatment, setExpandedTreatment] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'eco' | 'chemical'>('all');

  // Load advisory recommendations if not passed directly
  useEffect(() => {
    if (propTreatments) {
      setTreatments(propTreatments);
      return;
    }

    let isMounted = true;
    const fetchAdvisory = async () => {
      setLoading(true);
      try {
        const res = await AdvisoryService.getRecommendations(crop, disease, selectedRegion);
        if (isMounted && res.data?.data) {
          const data = res.data.data;
          const combined: TreatmentItem[] = [
            ...(data.biological_controls || []).map((b: any) => ({
              ...b,
              eco_friendly: true,
              residue_risk: 'Low / Zero Residue',
              residue_level: 'low',
              docs_url: DEFAULT_IPM_GUIDE_URL,
              regulation_url: DEFAULT_DOCS_URL,
            })),
            ...(data.chemical_options || []).map((c: any) => {
              const phi = c.pre_harvest_interval_days || 7;
              const level = phi > 14 ? 'high' : phi > 7 ? 'moderate' : 'low';
              const riskText =
                phi > 14
                  ? 'High Residue Persistence (Strict PHI Required)'
                  : phi > 7
                  ? 'Moderate Residue Risk (Observe PHI)'
                  : 'Standard Residue (Short PHI)';

              return {
                ...c,
                eco_friendly: false,
                residue_risk: riskText,
                residue_level: level,
                docs_url: DEFAULT_IPM_GUIDE_URL,
                regulation_url: DEFAULT_DOCS_URL,
              };
            }),
          ];
          setTreatments(combined);
          if (data.cultural_practices) {
            setPractices(data.cultural_practices);
          }
        }
      } catch (err) {
        // Fallback robust treatments
        if (isMounted) {
          setTreatments([
            {
              name: 'NeemAzal Bio-Shield',
              active_ingredient: 'Azadirachtin 1% EC',
              category: 'Biological / Bio-Pesticide',
              dosage: '3.0 ml/L of water',
              dosage_ml_per_liter: 3.0,
              pre_harvest_interval_days: 1,
              eco_friendly: true,
              residue_risk: 'Zero Toxic Residues (Pollinator Safe)',
              residue_level: 'low',
              safety_notes: 'Certified organic cold-pressed neem botanical extract; safe for beneficial pollinators. Spray in late afternoon.',
              docs_url: DEFAULT_IPM_GUIDE_URL,
              regulation_url: DEFAULT_DOCS_URL,
            },
            {
              name: 'Serenade Bio-Fungicide',
              active_ingredient: 'Bacillus subtilis QST 713',
              category: 'Biological Antagonist',
              dosage: '4.0 ml/L of water',
              dosage_ml_per_liter: 4.0,
              pre_harvest_interval_days: 0,
              eco_friendly: true,
              residue_risk: 'Microbial - Zero Chemical Residue',
              residue_level: 'low',
              safety_notes: 'Naturally occurring antagonistic bacteria producing lipopeptides that disrupt pathogen cell membranes.',
              docs_url: DEFAULT_IPM_GUIDE_URL,
              regulation_url: DEFAULT_DOCS_URL,
            },
            {
              name: 'Kocide 3000 Protective Copper',
              active_ingredient: 'Copper Hydroxide 46.1% DF',
              category: 'Chemical Protective',
              dosage: '2.0 ml/L of water',
              dosage_ml_per_liter: 2.0,
              pre_harvest_interval_days: 3,
              eco_friendly: false,
              residue_risk: 'Low-to-Moderate Surface Residue',
              residue_level: 'low',
              safety_notes: 'Broad-spectrum protective copper fungicide with high particle fineness and rain-fastness. Wear gloves and eye protection.',
              docs_url: DEFAULT_IPM_GUIDE_URL,
              regulation_url: DEFAULT_DOCS_URL,
            },
            {
              name: 'Amistar Opti Systematic Blend',
              active_ingredient: 'Azoxystrobin + Chlorothalonil',
              category: 'Synthetic Agro-Chemical',
              dosage: '2.0 ml/L of water',
              dosage_ml_per_liter: 2.0,
              pre_harvest_interval_days: 14,
              eco_friendly: false,
              residue_risk: 'High Residue Persistence (Strict PHI Required)',
              residue_level: 'high',
              safety_notes: 'Systemic strobilurin combined with multi-site chlorothalonil for long preventive persistence. Do not harvest within 14 days of application.',
              warning: selectedRegion.toLowerCase().includes('kerala') || selectedRegion.toLowerCase().includes('eu') ? 'RESTRICTED: Subject to strict regulatory limits in European export consignments.' : undefined,
              docs_url: DEFAULT_IPM_GUIDE_URL,
              regulation_url: DEFAULT_DOCS_URL,
            },
          ]);

          setPractices([
            {
              practice: 'Field Airflow Pruning',
              description: 'Prune bottom senescent leaves up to 20 cm from soil to reduce canopy humidity below 80%.',
              impact: 'High (lowers microclimate humidity)',
            },
            {
              practice: 'Crop Rotation',
              description: 'Rotate with non-host legume or cereal crops for at least 2 seasons to break soil inoculum cycles.',
              impact: 'High (reduces soil spores by 70%)',
            },
          ]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchAdvisory();
    return () => {
      isMounted = false;
    };
  }, [crop, disease, selectedRegion, propTreatments]);

  // Filter treatments
  const filteredTreatments = treatments.filter((t) => {
    if (activeTab === 'eco') return t.eco_friendly;
    if (activeTab === 'chemical') return !t.eco_friendly;
    return true;
  });

  return (
    <div className={`bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-100 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-black uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-3 py-1 rounded-full border border-emerald-200 flex items-center gap-1.5">
              <Leaf className="w-3.5 h-3.5 text-emerald-600" />
              Integrated Pest Management (IPM)
            </span>
            <span className="text-xs font-bold text-slate-500">
              {crop} • {disease}
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-gray-900 tracking-tight mt-2">
            Prescribed Treatment Advisory
          </h3>
          <p className="text-xs text-gray-500 mt-1">
            Prioritizes certified organic bio-controls, field sanitation, and regulated chemical safeguards.
          </p>
        </div>

        {/* Region selector */}
        <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-2xl border border-slate-200">
          <span className="text-[11px] font-bold text-slate-500">Jurisdiction:</span>
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="text-xs font-bold text-emerald-900 bg-transparent border-none focus:outline-none cursor-pointer"
          >
            <option value="Maharashtra">Maharashtra (Standard)</option>
            <option value="Kerala">Kerala (Strict Organic Policy)</option>
            <option value="Punjab">Punjab (Residue Monitored)</option>
            <option value="European Union">European Union (MRL Compliant)</option>
          </select>
        </div>
      </div>

      {/* Tabs Filter */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'all'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          All Recommendations ({treatments.length})
        </button>
        <button
          onClick={() => setActiveTab('eco')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            activeTab === 'eco'
              ? 'bg-emerald-600 text-white shadow-sm'
              : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200/60'
          }`}
        >
          <span>🌱 Eco-Friendly Only</span>
          <span className="px-1.5 py-0.2 bg-white/20 rounded-md text-[10px]">
            {treatments.filter((t) => t.eco_friendly).length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('chemical')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            activeTab === 'chemical'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-blue-50 text-blue-800 hover:bg-blue-100 border border-blue-200/60'
          }`}
        >
          <span>🧪 Conventional Chemical</span>
          <span className="px-1.5 py-0.2 bg-white/20 rounded-md text-[10px]">
            {treatments.filter((t) => !t.eco_friendly).length}
          </span>
        </button>
      </div>

      {/* Treatments List */}
      <div className="space-y-4">
        {filteredTreatments.map((item, idx) => {
          const isEco = item.eco_friendly;
          const isExpanded = expandedTreatment === item.name;
          const isBanned = item.regional_status === 'banned';
          const isRestricted = item.regional_status === 'restricted' || !!item.warning;

          return (
            <div
              key={idx}
              className={`rounded-2xl border transition-all overflow-hidden ${
                isBanned
                  ? 'bg-rose-50/70 border-rose-300 ring-1 ring-rose-300'
                  : isEco
                  ? 'bg-gradient-to-r from-emerald-50/70 via-teal-50/40 to-white border-emerald-200 hover:border-emerald-400 hover:shadow-md'
                  : isRestricted
                  ? 'bg-amber-50/50 border-amber-200 hover:border-amber-300'
                  : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm'
              }`}
            >
              {/* Card Banner / Header */}
              <div className="p-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0 shadow-sm ${
                        isBanned
                          ? 'bg-rose-100 text-rose-700'
                          : isEco
                          ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {isBanned ? '⛔' : isEco ? '🌱' : '🧪'}
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="font-extrabold text-base text-gray-900">
                          {item.name}
                        </h4>

                        {/* Eco-Friendly Highlight Badge */}
                        {isEco && (
                          <span className="inline-flex items-center gap-1 text-[11px] font-black text-emerald-800 bg-emerald-200/80 px-2.5 py-0.5 rounded-full border border-emerald-300 shadow-sm">
                            <Sparkles className="w-3 h-3 text-emerald-600" />
                            ECO-FRIENDLY BIO-CONTROL
                          </span>
                        )}

                        {/* Regional Status Badges */}
                        {isBanned && (
                          <span className="text-[11px] font-black text-rose-800 bg-rose-200 px-2.5 py-0.5 rounded-full border border-rose-300">
                            PROHIBITED IN {selectedRegion.toUpperCase()}
                          </span>
                        )}

                        {!isBanned && isRestricted && (
                          <span className="text-[11px] font-black text-amber-900 bg-amber-200/90 px-2.5 py-0.5 rounded-full border border-amber-300">
                            REGULATORY LIMITS APPLY
                          </span>
                        )}
                      </div>

                      {item.active_ingredient && (
                        <div className="text-xs text-slate-500 font-medium mt-0.5">
                          Active Ingredient: <span className="font-bold text-slate-700">{item.active_ingredient}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Pre-Harvest Interval Pill */}
                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    <span
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black shadow-sm ${
                        item.pre_harvest_interval_days === 0
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : item.pre_harvest_interval_days <= 3
                          ? 'bg-teal-100 text-teal-800 border border-teal-300'
                          : item.pre_harvest_interval_days <= 7
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : 'bg-amber-100 text-amber-900 border border-amber-300'
                      }`}
                    >
                      <Clock className="w-3.5 h-3.5" />
                      <span>
                        {item.pre_harvest_interval_days === 0
                          ? '0-Day PHI (Zero Wait)'
                          : `PHI: ${item.pre_harvest_interval_days} Days`}
                      </span>
                    </span>
                  </div>
                </div>

                {/* Key Metrics Grid: Dosage & Residue Risk */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 pt-3 border-t border-slate-100 text-xs">
                  {/* Dosage */}
                  <div className="flex items-center gap-2 p-2.5 rounded-xl bg-white/80 border border-slate-200/70">
                    <Droplets className="w-4 h-4 text-teal-600 flex-shrink-0" />
                    <div>
                      <span className="text-slate-400 font-bold block text-[10px] uppercase">
                        Recommended Application Rate
                      </span>
                      <span className="font-extrabold text-gray-900">{item.dosage}</span>
                    </div>
                  </div>

                  {/* Residue Risk Warning */}
                  <div
                    className={`flex items-center gap-2 p-2.5 rounded-xl border ${
                      item.residue_level === 'high'
                        ? 'bg-amber-50 border-amber-300 text-amber-950'
                        : item.residue_level === 'moderate'
                        ? 'bg-blue-50 border-blue-200 text-blue-950'
                        : 'bg-emerald-50 border-emerald-200 text-emerald-950'
                    }`}
                  >
                    <AlertTriangle
                      className={`w-4 h-4 flex-shrink-0 ${
                        item.residue_level === 'high'
                          ? 'text-amber-600'
                          : item.residue_level === 'moderate'
                          ? 'text-blue-600'
                          : 'text-emerald-600'
                      }`}
                    />
                    <div>
                      <span className="text-[10px] font-bold block uppercase opacity-75">
                        Residue Risk Level
                      </span>
                      <span className="font-extrabold">{item.residue_risk || 'Low Residue'}</span>
                    </div>
                  </div>
                </div>

                {/* Regional Warning Callout */}
                {(item.regional_warning || item.warning) && (
                  <div className="mt-3 p-3 rounded-xl bg-rose-100/70 border border-rose-200 text-xs text-rose-900 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                    <div className="font-semibold">
                      {item.regional_warning || item.warning}
                    </div>
                  </div>
                )}

                {/* Safety notes & expandable details */}
                {item.safety_notes && (
                  <div className="mt-3 text-xs text-slate-600 font-medium leading-relaxed">
                    <span className="font-bold text-slate-800">Safety & Application Notes: </span>
                    {item.safety_notes}
                  </div>
                )}

                {/* Read More Links to Official Docs & Local Regulations */}
                <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="flex flex-wrap items-center gap-4 font-bold">
                    <a
                      href={item.docs_url || DEFAULT_IPM_GUIDE_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-800 underline decoration-emerald-300 hover:decoration-emerald-600 transition-colors"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>Read Treatment Guidelines</span>
                      <ExternalLink className="w-3 h-3 ml-0.5" />
                    </a>

                    <a
                      href={item.regulation_url || DEFAULT_DOCS_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 underline decoration-slate-300 hover:decoration-slate-600 transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>CIBRC & Regional Regulations</span>
                      <ExternalLink className="w-3 h-3 ml-0.5" />
                    </a>
                  </div>

                  {onSelectTreatment && (
                    <button
                      onClick={() => onSelectTreatment(item)}
                      className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs shadow-sm transition-all"
                    >
                      Select Treatment
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Cultural Practices & Field Sanitation */}
      {practices.length > 0 && (
        <div className="pt-6 border-t border-slate-100">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h4 className="font-extrabold text-base text-gray-900">
              Agronomic Cultural Practices & Sanitation
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {practices.map((p, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-xs text-gray-900">{p.practice}</span>
                  {p.impact && (
                    <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                      {p.impact}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 leading-relaxed font-medium">
                  {p.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvisoryCard;
