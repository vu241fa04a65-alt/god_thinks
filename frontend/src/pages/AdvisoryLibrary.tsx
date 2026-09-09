import React, { useState, useEffect, useMemo } from 'react';
import {
  BookOpen,
  Search,
  Filter,
  Leaf,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Droplets,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  FileText,
  Sparkles,
  Sliders,
  Scale,
  RefreshCw,
  Info,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { AdvisoryService } from '../services/api';

export interface PesticideItem {
  name: string;
  active_ingredient: string;
  crops: string[];
  target_diseases: string[];
  dosage: string;
  dosage_ml_per_liter: number;
  pre_harvest_interval_days: number;
  eco_friendly: boolean;
  eco_friendly_flag?: boolean;
  category: string;
  residue_risk: string;
  residue_level: 'low' | 'moderate' | 'high';
  safety_notes: string;
  regional_status: string;
  regional_warning?: string;
  is_banned?: boolean;
  is_restricted?: boolean;
}

const CROPS_LIST = [
  'All Crops',
  'Tomato',
  'Potato',
  'Grape',
  'Rice',
  'Wheat',
  'Cotton',
  'Chili',
  'Corn',
  'Apple',
  'Soybean',
];

const REGIONAL_JURISDICTIONS = [
  { id: 'all', label: 'All Jurisdictions' },
  { id: 'maharashtra', label: 'Maharashtra (Standard)' },
  { id: 'kerala', label: 'Kerala (Organic Policy Restrictions)' },
  { id: 'punjab', label: 'Punjab (Residue Monitored)' },
  { id: 'andhra pradesh', label: 'Andhra Pradesh (APCNF Zones)' },
  { id: 'european union', label: 'European Union (Strict MRLs)' },
  { id: 'united states', label: 'United States (EPA RUP)' },
];

const FALLBACK_PESTICIDES: PesticideItem[] = [
  {
    name: 'NeemAzal Bio-Shield',
    active_ingredient: 'Azadirachtin 1% EC',
    crops: ['tomato', 'potato', 'chili', 'cotton', 'rice', 'wheat', 'corn', 'grape', 'apple', 'soybean'],
    target_diseases: ['early blight', 'late blight', 'powdery mildew', 'aphids', 'whiteflies'],
    dosage: '3.0 ml/L of water',
    dosage_ml_per_liter: 3.0,
    pre_harvest_interval_days: 1,
    eco_friendly: true,
    category: 'Biological / Bio-Pesticide',
    residue_risk: 'Low / Zero Residue',
    residue_level: 'low',
    safety_notes: 'Certified organic cold-pressed neem botanical extract; safe for beneficial pollinators.',
    regional_status: 'allowed',
  },
  {
    name: 'Tricho-Shield WP',
    active_ingredient: 'Trichoderma viride 1.5% WP',
    crops: ['tomato', 'potato', 'chili', 'wheat', 'rice', 'cotton', 'soybean'],
    target_diseases: ['root rot', 'damping off', 'early blight', 'wilt', 'collar rot'],
    dosage: '5.0 ml/L of water',
    dosage_ml_per_liter: 5.0,
    pre_harvest_interval_days: 0,
    eco_friendly: true,
    category: 'Microbial Antagonist',
    residue_risk: 'Low / Zero Residue',
    residue_level: 'low',
    safety_notes: 'Microbial bio-fungicide that colonizes root rhizosphere and suppresses fungal spores.',
    regional_status: 'allowed',
  },
  {
    name: 'Serenade Bio-Fungicide',
    active_ingredient: 'Bacillus subtilis QST 713',
    crops: ['tomato', 'potato', 'grape', 'apple', 'chili', 'corn', 'wheat'],
    target_diseases: ['early blight', 'late blight', 'bacterial blight', 'powdery mildew', 'anthracnose'],
    dosage: '4.0 ml/L of water',
    dosage_ml_per_liter: 4.0,
    pre_harvest_interval_days: 0,
    eco_friendly: true,
    category: 'Biological / Bio-Pesticide',
    residue_risk: 'Low / Zero Residue',
    residue_level: 'low',
    safety_notes: 'Naturally occurring antagonistic bacteria producing lipopeptides that disrupt pathogen cell membranes.',
    regional_status: 'allowed',
  },
  {
    name: 'Copper-Shield Octanoate',
    active_ingredient: 'Copper Octanoate (Soap)',
    crops: ['tomato', 'potato', 'grape', 'apple', 'chili'],
    target_diseases: ['early blight', 'late blight', 'anthracnose', 'black rot', 'apple scab'],
    dosage: '4.5 ml/L of water',
    dosage_ml_per_liter: 4.5,
    pre_harvest_interval_days: 1,
    eco_friendly: true,
    category: 'Organic Copper Soap',
    residue_risk: 'Low / Zero Residue',
    residue_level: 'low',
    safety_notes: 'Fixed copper fatty acid formulation suitable for organic farming; low soil accumulation.',
    regional_status: 'allowed',
  },
  {
    name: 'Kocide 3000',
    active_ingredient: 'Copper Hydroxide',
    crops: ['tomato', 'potato', 'chili', 'grape', 'apple'],
    target_diseases: ['early blight', 'late blight', 'anthracnose', 'bacterial canker', 'black rot'],
    dosage: '2.0 ml/L of water',
    dosage_ml_per_liter: 2.0,
    pre_harvest_interval_days: 3,
    eco_friendly: false,
    category: 'Synthetic Agro-Chemical',
    residue_risk: 'Low Residue (Standard Wash Off)',
    residue_level: 'low',
    safety_notes: 'Broad-spectrum protective copper fungicide with high particle fineness and rain-fastness.',
    regional_status: 'allowed',
  },
  {
    name: 'Dithane M-45',
    active_ingredient: 'Mancozeb 75% WP',
    crops: ['tomato', 'potato', 'wheat', 'rice', 'grape', 'apple', 'chili'],
    target_diseases: ['early blight', 'late blight', 'rust', 'leaf spot', 'downy mildew', 'apple scab'],
    dosage: '2.5 ml/L of water',
    dosage_ml_per_liter: 2.5,
    pre_harvest_interval_days: 7,
    eco_friendly: false,
    category: 'Synthetic Agro-Chemical',
    residue_risk: 'Low Residue (Standard Wash Off)',
    residue_level: 'low',
    safety_notes: 'Multi-site contact dithiocarbamate fungicide; essential for resistance management.',
    regional_status: 'allowed',
  },
  {
    name: 'Amistar Opti',
    active_ingredient: 'Azoxystrobin + Chlorothalonil',
    crops: ['tomato', 'potato', 'wheat', 'corn', 'chili'],
    target_diseases: ['early blight', 'late blight', 'rust', 'anthracnose', 'leaf blight'],
    dosage: '2.0 ml/L of water',
    dosage_ml_per_liter: 2.0,
    pre_harvest_interval_days: 14,
    eco_friendly: false,
    category: 'Synthetic Agro-Chemical',
    residue_risk: 'Moderate Residue (Adhere to PHI)',
    residue_level: 'moderate',
    safety_notes: 'Systemic strobilurin combined with multi-site chlorothalonil for long preventive persistence.',
    regional_status: 'allowed',
  },
  {
    name: 'Tilt 250 EC',
    active_ingredient: 'Propiconazole 25% EC',
    crops: ['wheat', 'rice', 'corn', 'soybean'],
    target_diseases: ['rust', 'stripe rust', 'sheath blight', 'leaf spot'],
    dosage: '1.0 ml/L of water',
    dosage_ml_per_liter: 1.0,
    pre_harvest_interval_days: 21,
    eco_friendly: false,
    category: 'Synthetic Agro-Chemical',
    residue_risk: 'High Residue Persistence (Strict PHI Required)',
    residue_level: 'high',
    safety_notes: 'Broad-spectrum systemic triazole fungicide inhibiting fungal ergosterol biosynthesis.',
    regional_status: 'allowed',
  },
  {
    name: 'Bavistin 50 WP',
    active_ingredient: 'Carbendazim 50% WP',
    crops: ['wheat', 'rice', 'cotton', 'tomato', 'chili'],
    target_diseases: ['blast', 'anthracnose', 'loose smut', 'powdery mildew'],
    dosage: '1.5 ml/L of water',
    dosage_ml_per_liter: 1.5,
    pre_harvest_interval_days: 14,
    eco_friendly: false,
    category: 'Synthetic Agro-Chemical',
    residue_risk: 'Moderate Residue (Adhere to PHI)',
    residue_level: 'moderate',
    safety_notes: 'Systemic benzimidazole fungicide; banned or restricted in several jurisdictions due to endocrine disruption.',
    regional_status: 'restricted',
    regional_warning: 'RESTRICTED in Punjab & European Union due to endocrine disruption concerns.',
  },
  {
    name: 'ChlorGuard 20 EC',
    active_ingredient: 'Chlorpyrifos 20% EC',
    crops: ['cotton', 'rice', 'wheat'],
    target_diseases: ['termites', 'stem borer', 'aphids'],
    dosage: '2.5 ml/L of water',
    dosage_ml_per_liter: 2.5,
    pre_harvest_interval_days: 21,
    eco_friendly: false,
    category: 'Synthetic Agro-Chemical',
    residue_risk: 'High Residue Persistence (Strict PHI Required)',
    residue_level: 'high',
    safety_notes: 'Broad-spectrum organophosphate; restricted or banned in many regions for acute neurotoxicity.',
    regional_status: 'banned',
    regional_warning: 'BANNED in Kerala & European Union for developmental neurotoxicity.',
    is_banned: true,
  },
];

export const AdvisoryLibrary: React.FC = () => {
  const [pesticides, setPesticides] = useState<PesticideItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCrop, setSelectedCrop] = useState<string>('All Crops');
  const [classificationFilter, setClassificationFilter] = useState<'all' | 'eco' | 'chemical'>('all');
  const [residueFilter, setResidueFilter] = useState<string>('all');
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const [selectedItem, setSelectedItem] = useState<PesticideItem | null>(null);

  // Sprayer calculator state in detail modal
  const [tankSizeLiters, setTankSizeLiters] = useState<number>(15);

  const fetchCatalog = async () => {
    setLoading(true);
    try {
      const regionParam = selectedRegion === 'all' ? undefined : selectedRegion;
      const cropParam = selectedCrop === 'All Crops' ? undefined : selectedCrop;
      const ecoParam =
        classificationFilter === 'eco'
          ? true
          : classificationFilter === 'chemical'
          ? false
          : undefined;

      const res = await AdvisoryService.getPesticides({
        region: regionParam,
        crop: cropParam,
        eco_friendly: ecoParam,
        search: searchQuery || undefined,
      });

      if (res.data?.data?.pesticides && res.data.data.pesticides.length > 0) {
        setPesticides(res.data.data.pesticides);
      } else {
        setPesticides(FALLBACK_PESTICIDES);
      }
    } catch (err) {
      setPesticides(FALLBACK_PESTICIDES);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, [selectedCrop, classificationFilter, selectedRegion]);

  // Client-side filtering
  const filteredList = useMemo(() => {
    return pesticides.filter((item) => {
      // Free text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inName = item.name.toLowerCase().includes(q);
        const inAI = item.active_ingredient.toLowerCase().includes(q);
        const inNotes = item.safety_notes.toLowerCase().includes(q);
        const inDiseases = item.target_diseases.some((d) => d.toLowerCase().includes(q));
        if (!inName && !inAI && !inNotes && !inDiseases) return false;
      }

      // Crop filter
      if (selectedCrop !== 'All Crops') {
        const normCrop = selectedCrop.toLowerCase();
        if (!item.crops.some((c) => c.toLowerCase().includes(normCrop))) return false;
      }

      // Classification filter
      if (classificationFilter === 'eco' && !item.eco_friendly) return false;
      if (classificationFilter === 'chemical' && item.eco_friendly) return false;

      // Residue filter
      if (residueFilter === 'low' && item.residue_level !== 'low') return false;
      if (residueFilter === 'moderate' && item.residue_level !== 'moderate') return false;
      if (residueFilter === 'high' && item.residue_level !== 'high') return false;

      return true;
    });
  }, [pesticides, searchQuery, selectedCrop, classificationFilter, residueFilter]);

  const ecoCount = pesticides.filter((p) => p.eco_friendly).length;
  const chemicalCount = pesticides.filter((p) => !p.eco_friendly).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-slate-200">
        <div>
          <span className="text-xs font-black uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-3.5 py-1.5 rounded-full border border-emerald-200 flex items-center gap-1.5 w-fit">
            <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
            Pharmacopeia & Agro-Chemical Codex
          </span>
          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight mt-3">
            Advisory & Pesticide Library
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-1 max-w-2xl leading-relaxed">
            Searchable regulatory catalog of certified biological controls and conventional
            pesticides. Highlights eco-friendly biological options and issues residue risk warnings.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-emerald-50 border border-emerald-200 px-4 py-2 rounded-2xl text-center">
            <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
              Bio-Controls
            </span>
            <span className="text-lg font-black text-emerald-900">{ecoCount} Formulations</span>
          </div>

          <div className="bg-blue-50 border border-blue-200 px-4 py-2 rounded-2xl text-center">
            <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider block">
              Conventional
            </span>
            <span className="text-lg font-black text-blue-900">{chemicalCount} Chemicals</span>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Search bar */}
          <div className="relative flex-1 max-w-lg">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search active ingredient, commercial brand, or target disease..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-colors font-medium"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Classification Tabs */}
            <div className="flex items-center gap-1.5 bg-slate-50 p-1 rounded-2xl border border-slate-200 text-xs font-bold">
              <button
                onClick={() => setClassificationFilter('all')}
                className={`px-3 py-1.5 rounded-xl transition-all ${
                  classificationFilter === 'all'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setClassificationFilter('eco')}
                className={`px-3 py-1.5 rounded-xl transition-all flex items-center gap-1 ${
                  classificationFilter === 'eco'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-emerald-800 hover:bg-emerald-50'
                }`}
              >
                <span>🌱 Bio-Controls</span>
              </button>
              <button
                onClick={() => setClassificationFilter('chemical')}
                className={`px-3 py-1.5 rounded-xl transition-all flex items-center gap-1 ${
                  classificationFilter === 'chemical'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-blue-800 hover:bg-blue-50'
                }`}
              >
                <span>🧪 Synthetics</span>
              </button>
            </div>

            {/* Jurisdiction selector */}
            <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-2 rounded-2xl border border-slate-200 text-xs font-bold text-slate-700">
              <Scale className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="bg-transparent border-none focus:outline-none cursor-pointer text-xs font-bold text-slate-800"
              >
                {REGIONAL_JURISDICTIONS.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Crop Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-bold scrollbar-none">
          <span className="text-slate-400 text-[11px] flex-shrink-0 uppercase tracking-wider mr-1">
            Target Crop:
          </span>
          {CROPS_LIST.map((crop) => (
            <button
              key={crop}
              onClick={() => setSelectedCrop(crop)}
              className={`px-3 py-1.5 rounded-xl transition-all flex-shrink-0 ${
                selectedCrop === crop
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {crop}
            </button>
          ))}
        </div>
      </div>

      {/* Catalog Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredList.map((item, idx) => {
          const isEco = item.eco_friendly;
          const isBanned = item.is_banned || item.regional_status === 'banned';
          const isRestricted = item.is_restricted || item.regional_status === 'restricted';

          return (
            <div
              key={idx}
              onClick={() => setSelectedItem(item)}
              className={`cursor-pointer rounded-3xl p-6 border transition-all duration-300 flex flex-col justify-between space-y-4 hover:shadow-xl hover:-translate-y-1 ${
                isBanned
                  ? 'bg-gradient-to-b from-rose-50/70 to-white border-rose-300 ring-1 ring-rose-300'
                  : isEco
                  ? 'bg-gradient-to-b from-emerald-50/70 via-teal-50/20 to-white border-emerald-200 hover:border-emerald-400 ring-1 ring-emerald-300/40'
                  : 'bg-white border-slate-200 hover:border-blue-300'
              }`}
            >
              <div>
                {/* Header Pills */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-1.5">
                    {isEco ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-200 text-emerald-900 border border-emerald-300 shadow-sm">
                        <Sparkles className="w-3 h-3 text-emerald-700" />
                        Eco-Friendly Bio-Control
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-blue-100 text-blue-800 border border-blue-200">
                        Synthetic Compound
                      </span>
                    )}
                  </div>

                  {/* Pre-Harvest Interval Pill */}
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black ${
                      item.pre_harvest_interval_days === 0
                        ? 'bg-emerald-100 text-emerald-800'
                        : item.pre_harvest_interval_days <= 7
                        ? 'bg-teal-100 text-teal-800'
                        : 'bg-amber-100 text-amber-900'
                    }`}
                  >
                    <Clock className="w-3 h-3" />
                    <span>{item.pre_harvest_interval_days}D PHI</span>
                  </span>
                </div>

                {/* Name & Active Ingredient */}
                <h3 className="text-lg font-black text-gray-900 leading-snug">{item.name}</h3>
                <div className="text-xs font-semibold text-slate-500 mt-1">
                  Active Ingredient: <span className="text-slate-800 font-bold">{item.active_ingredient}</span>
                </div>

                {/* Residue Risk Warning Alert */}
                <div
                  className={`mt-3 p-3 rounded-2xl border text-xs flex items-start gap-2 ${
                    item.residue_level === 'high'
                      ? 'bg-amber-50 border-amber-300 text-amber-950 font-medium'
                      : item.residue_level === 'moderate'
                      ? 'bg-blue-50 border-blue-200 text-blue-950 font-medium'
                      : 'bg-emerald-50 border-emerald-200 text-emerald-950 font-medium'
                  }`}
                >
                  <AlertTriangle
                    className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                      item.residue_level === 'high'
                        ? 'text-amber-600'
                        : item.residue_level === 'moderate'
                        ? 'text-blue-600'
                        : 'text-emerald-600'
                    }`}
                  />
                  <div>
                    <span className="font-bold text-[10px] uppercase block">Residue Risk Profile:</span>
                    <span>{item.residue_risk}</span>
                  </div>
                </div>

                {/* Regional Ban / Restriction Callout */}
                {(item.regional_warning || isBanned || isRestricted) && (
                  <div className="mt-2.5 p-2.5 rounded-xl bg-rose-100 border border-rose-300 text-rose-900 text-xs font-semibold flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                    <span>{item.regional_warning || 'Restricted or Banned in target jurisdiction.'}</span>
                  </div>
                )}

                {/* Target diseases tags */}
                <div className="mt-3 flex flex-wrap gap-1">
                  {item.target_diseases.slice(0, 3).map((d, dIdx) => (
                    <span
                      key={dIdx}
                      className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-[10px] font-bold capitalize"
                    >
                      {d}
                    </span>
                  ))}
                  {item.target_diseases.length > 3 && (
                    <span className="px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-400 text-[10px]">
                      +{item.target_diseases.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              {/* Card Footer */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5 text-slate-700 font-bold">
                  <Droplets className="w-3.5 h-3.5 text-teal-600" />
                  <span>{item.dosage}</span>
                </div>

                <span className="text-emerald-700 font-black flex items-center gap-1 text-[11px] group-hover:translate-x-1 transition-transform">
                  <span>View Details</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {filteredList.length === 0 && !loading && (
        <div className="bg-white rounded-3xl p-12 text-center border border-slate-100 shadow-sm space-y-3">
          <CheckCircle2 className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="font-extrabold text-base text-gray-800">No formulations found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Try adjusting your search query, crop selection, or classification filters.
          </p>
        </div>
      )}

      {/* Product Detail Modal & Sprayer Dosage Calculator */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl border border-slate-100 space-y-6 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  {selectedItem.eco_friendly ? (
                    <span className="px-3 py-0.5 rounded-full text-xs font-black uppercase bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-emerald-600" />
                      Certified Eco-Friendly Bio-Control
                    </span>
                  ) : (
                    <span className="px-3 py-0.5 rounded-full text-xs font-black uppercase bg-blue-100 text-blue-800 border border-blue-200">
                      Conventional Agro-Chemical
                    </span>
                  )}
                  <span className="text-xs font-bold text-slate-400">
                    PHI: {selectedItem.pre_harvest_interval_days} Days
                  </span>
                </div>
                <h3 className="text-2xl font-black text-gray-900 mt-2">{selectedItem.name}</h3>
                <div className="text-xs font-semibold text-slate-500 mt-0.5">
                  Formula: <span className="text-slate-800 font-bold">{selectedItem.active_ingredient}</span>
                </div>
              </div>

              <button
                onClick={() => setSelectedItem(null)}
                className="p-2 text-slate-400 hover:text-slate-700 rounded-xl hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Residue Risk & Safety Alert */}
            <div
              className={`p-4 rounded-2xl border text-xs space-y-2 ${
                selectedItem.residue_level === 'high'
                  ? 'bg-amber-50 border-amber-300 text-amber-950'
                  : selectedItem.residue_level === 'moderate'
                  ? 'bg-blue-50 border-blue-200 text-blue-950'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-950'
              }`}
            >
              <div className="flex items-center gap-2 font-black text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>Residue Risk & Pre-Harvest Safety</span>
              </div>
              <p className="leading-relaxed font-medium">
                {selectedItem.residue_risk}. Ensure crops are not harvested before the statutory{' '}
                <span className="font-bold">{selectedItem.pre_harvest_interval_days}-day interval</span>{' '}
                to comply with Maximum Residue Limits (MRL).
              </p>
            </div>

            {/* Knapsack Sprayer Dosage Calculator */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-xs text-gray-900 flex items-center gap-1.5">
                  <Droplets className="w-4 h-4 text-teal-600" />
                  Knapsack Sprayer Mixing Calculator
                </span>
                <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                  {selectedItem.dosage_ml_per_liter} ml / Liter
                </span>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-500 font-medium">Tank Volume:</span>
                {[15, 20, 100, 200].map((liters) => (
                  <button
                    key={liters}
                    onClick={() => setTankSizeLiters(liters)}
                    className={`px-3 py-1 rounded-xl font-bold transition-all ${
                      tankSizeLiters === liters
                        ? 'bg-slate-900 text-white shadow-sm'
                        : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {liters}L {liters === 15 ? '(Backpack)' : liters === 200 ? '(Drum)' : ''}
                  </button>
                ))}
              </div>

              <div className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700">Required Chemical Concentrate:</span>
                <span className="text-base font-black text-emerald-800">
                  {(selectedItem.dosage_ml_per_liter * tankSizeLiters).toFixed(1)} ml (or grams)
                </span>
              </div>
            </div>

            {/* Clinical & Safety Notes */}
            <div className="space-y-2 text-xs">
              <span className="font-extrabold text-gray-800 uppercase tracking-wider block">
                Safety & Application Guidance:
              </span>
              <p className="text-slate-600 leading-relaxed font-medium bg-slate-50 p-3 rounded-xl border border-slate-200">
                {selectedItem.safety_notes}
              </p>
            </div>

            {/* Official Documentation & Regulations */}
            <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex flex-wrap items-center gap-4 font-bold">
                <a
                  href="https://agricoop.gov.in/en/Major-Activities"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-800 underline decoration-emerald-300"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>IPM Standard Protocol</span>
                  <ExternalLink className="w-3 h-3" />
                </a>

                <a
                  href="https://cibrc.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 underline decoration-slate-300"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>CIBRC Registration Gazette</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              <button
                onClick={() => setSelectedItem(null)}
                className="py-2 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvisoryLibrary;
