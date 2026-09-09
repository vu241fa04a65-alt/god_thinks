import React, { useState } from 'react';
import {
  Award,
  Lock,
  CheckCircle2,
  Sparkles,
  Shield,
  Zap,
  Target,
  Users,
  Compass,
  HeartHandshake,
  Star,
  Info,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export interface BadgeItem {
  id: string;
  name: string;
  category: 'milestone' | 'achievement' | 'special';
  minPoints: number;
  icon: string;
  color: string;
  description: string;
  perk: string;
}

export const ALL_BADGES: BadgeItem[] = [
  {
    id: 'eco_scout',
    name: 'Eco Scout',
    category: 'milestone',
    minPoints: 0,
    icon: '🌱',
    color: 'from-emerald-500 to-green-600',
    description: 'Enrolled in community disease surveillance and completed first field leaf scan.',
    perk: 'Unlocks local village alert notifications & basic IPM guides.',
  },
  {
    id: 'first_responder',
    name: 'First Outbreak Sentinel',
    category: 'achievement',
    minPoints: 10,
    icon: '⚡',
    color: 'from-amber-500 to-yellow-600',
    description: 'Submitted the very first verified disease detection in your village sector.',
    perk: '2x multiplier on community praise points.',
  },
  {
    id: 'plant_doctor',
    name: 'Plant Doctor',
    category: 'milestone',
    minPoints: 50,
    icon: '🌾',
    color: 'from-teal-500 to-emerald-700',
    description: 'Accumulated 50+ points through accurate disease diagnoses and field scans.',
    perk: 'Eligible for 10% Bio-Fertilizer discount co-op vouchers.',
  },
  {
    id: 'bio_defender',
    name: 'Bio-Fungicide Pioneer',
    category: 'achievement',
    minPoints: 75,
    icon: '🛡️',
    color: 'from-blue-500 to-indigo-600',
    description: 'Adopted and shared 5+ organic IPM treatment recommendations with peer farmers.',
    perk: 'Priority agronomy lab referral queues.',
  },
  {
    id: 'master_agronomist',
    name: 'Master Agronomist',
    category: 'milestone',
    minPoints: 150,
    icon: '⭐',
    color: 'from-purple-500 to-indigo-700',
    description: 'Reached 150 points. A veteran scout trusted across multiple crop varieties.',
    perk: 'Free 1-on-1 Agronomist field consultation & soil test coupon.',
  },
  {
    id: 'community_pillar',
    name: 'Community Pillar',
    category: 'achievement',
    minPoints: 200,
    icon: '🤝',
    color: 'from-rose-500 to-pink-600',
    description: 'Helped 20+ neighboring farmers prevent disease spread through early SMS warnings.',
    perk: 'Featured on regional agricultural extension bulletin.',
  },
  {
    id: 'crop_guardian',
    name: 'Village Crop Guardian',
    category: 'milestone',
    minPoints: 300,
    icon: '🏆',
    color: 'from-amber-400 via-yellow-500 to-amber-600',
    description: 'Top-tier rank with 300+ points protecting entire district harvests and food security.',
    perk: 'Certified Hybrid Disease-Resistant Seeds Pack delivered to farm gate.',
  },
];

export const Badges: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { user } = useAuth();
  const currentPoints = user?.points ?? 45;
  const [filter, setFilter] = useState<'all' | 'unlocked' | 'locked'>('all');
  const [selectedBadge, setSelectedBadge] = useState<BadgeItem | null>(null);

  const isUnlocked = (badge: BadgeItem) => currentPoints >= badge.minPoints;

  const filteredBadges = ALL_BADGES.filter((b) => {
    const unlocked = isUnlocked(b);
    if (filter === 'unlocked') return unlocked;
    if (filter === 'locked') return !unlocked;
    return true;
  });

  const totalUnlocked = ALL_BADGES.filter(isUnlocked).length;

  return (
    <div className={`bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-100 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-6 h-6 text-amber-500" />
            <h2 className="text-xl font-extrabold text-gray-900 tracking-tight">
              Milestone Badges & Honors
            </h2>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Earn honor badges and exclusive agricultural perks as your scouting contributions grow.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-50 p-1 rounded-2xl border border-slate-200/70 text-xs font-bold">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              filter === 'all' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            All ({ALL_BADGES.length})
          </button>
          <button
            onClick={() => setFilter('unlocked')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              filter === 'unlocked' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Unlocked ({totalUnlocked})
          </button>
          <button
            onClick={() => setFilter('locked')}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              filter === 'locked' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Locked ({ALL_BADGES.length - totalUnlocked})
          </button>
        </div>
      </div>

      {/* Badges Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBadges.map((badge) => {
          const unlocked = isUnlocked(badge);
          const pointsRemaining = Math.max(0, badge.minPoints - currentPoints);
          const progress = unlocked
            ? 100
            : Math.min(100, Math.round((currentPoints / badge.minPoints) * 100));

          return (
            <div
              key={badge.id}
              onClick={() => setSelectedBadge(badge)}
              className={`cursor-pointer rounded-2xl p-5 border transition-all duration-200 relative overflow-hidden flex flex-col justify-between ${
                unlocked
                  ? 'bg-gradient-to-b from-white to-emerald-50/30 border-emerald-200/80 shadow-sm hover:shadow-md hover:border-emerald-400'
                  : 'bg-slate-50/80 border-slate-200/70 opacity-75 hover:opacity-100 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  {/* Badge Icon */}
                  <div
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-sm ${
                      unlocked
                        ? 'bg-white border-2 border-emerald-200 shadow-emerald-100'
                        : 'bg-slate-200 border border-slate-300 grayscale'
                    }`}
                  >
                    {badge.icon}
                  </div>

                  {/* Status Indicator */}
                  {unlocked ? (
                    <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-100/70 px-2.5 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Unlocked
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[11px] font-bold text-slate-500 bg-slate-200/60 px-2.5 py-0.5 rounded-full">
                      <Lock className="w-3 h-3 text-slate-400" />
                      {badge.minPoints} pts
                    </span>
                  )}
                </div>

                <h3 className="font-extrabold text-sm text-gray-900 mt-3 flex items-center gap-1.5">
                  {badge.name}
                  {badge.category === 'milestone' && (
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-700 bg-amber-100/70 px-1.5 py-0.5 rounded">
                      Tier
                    </span>
                  )}
                </h3>

                <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                  {badge.description}
                </p>
              </div>

              {/* Progress Bar / Perk */}
              <div className="mt-4 pt-3 border-t border-slate-100">
                {unlocked ? (
                  <div className="text-[11px] font-semibold text-emerald-700 truncate">
                    🎁 Perk: {badge.perk}
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between items-center text-[11px] font-medium text-slate-500 mb-1">
                      <span>Progress</span>
                      <span>{pointsRemaining} pts needed</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Badge Detail Modal */}
      {selectedBadge && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 relative">
            <div className="flex items-start justify-between">
              <div className="w-16 h-16 rounded-3xl bg-slate-100 border-2 border-emerald-200 flex items-center justify-center text-3xl shadow-sm">
                {selectedBadge.icon}
              </div>
              <button
                onClick={() => setSelectedBadge(null)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="mt-4">
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-black text-gray-900">{selectedBadge.name}</h3>
                {isUnlocked(selectedBadge) ? (
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    Earned
                  </span>
                ) : (
                  <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                    Locked ({selectedBadge.minPoints} pts)
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-600 mt-2 leading-relaxed font-medium">
                {selectedBadge.description}
              </p>
            </div>

            <div className="mt-4 p-4 rounded-2xl bg-emerald-50/70 border border-emerald-100">
              <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider block mb-1">
                Agricultural Perk Unlocked:
              </span>
              <p className="text-xs text-emerald-800 font-semibold">{selectedBadge.perk}</p>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedBadge(null)}
                className="w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Badges;
