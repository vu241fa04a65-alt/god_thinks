import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Trophy,
  Sparkles,
  TrendingUp,
  Award,
  ArrowRight,
  Share2,
  Camera,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Eye,
  PlusCircle,
  HelpCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { GamificationService } from '../services/api';

interface Transaction {
  reward_id?: number;
  points: number;
  reason: string;
  created_at?: string;
}

interface TierInfo {
  id: string;
  name: string;
  badge: string;
  minPoints: number;
}

const TIERS: TierInfo[] = [
  { id: 'eco_scout', name: 'Eco Scout', badge: '🌱 Eco Scout', minPoints: 0 },
  { id: 'plant_doctor', name: 'Plant Doctor', badge: '🌾 Plant Doctor', minPoints: 50 },
  { id: 'master_agronomist', name: 'Master Agronomist', badge: '⭐ Master Agronomist', minPoints: 150 },
  { id: 'crop_guardian', name: 'Village Crop Guardian', badge: '🏆 Village Crop Guardian', minPoints: 300 },
];

export const PointsCard: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { user, updatePoints } = useAuth();
  const { showPointsToast, showToast } = useToast();

  const currentPoints = user?.points ?? 45;
  const [displayedPoints, setDisplayedPoints] = useState<number>(currentPoints);
  const [pointDelta, setPointDelta] = useState<number | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Animated counter effect when currentPoints changes
  const prevPointsRef = useRef<number>(currentPoints);

  useEffect(() => {
    const prev = prevPointsRef.current;
    if (prev !== currentPoints) {
      const delta = currentPoints - prev;
      setPointDelta(delta);
      setIsAnimating(true);

      const duration = 1000;
      const startTime = performance.now();

      const animate = (time: number) => {
        const elapsed = time - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // easeOutQuad
        const ease = 1 - (1 - progress) * (1 - progress);
        const nextValue = Math.round(prev + delta * ease);
        setDisplayedPoints(nextValue);

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setDisplayedPoints(currentPoints);
          prevPointsRef.current = currentPoints;
          setTimeout(() => {
            setPointDelta(null);
            setIsAnimating(false);
          }, 1200);
        }
      };

      requestAnimationFrame(animate);
    } else {
      setDisplayedPoints(currentPoints);
    }
  }, [currentPoints]);

  // Load points summary & recent rewards ledger
  useEffect(() => {
    let isMounted = true;
    const loadLedger = async () => {
      try {
        const res = await GamificationService.getPoints(user?.id);
        if (isMounted && res.data?.data) {
          const data = res.data.data;
          if (data.recent_transactions && data.recent_transactions.length > 0) {
            setTransactions(data.recent_transactions);
          } else {
            setFallbackTransactions();
          }
        } else if (isMounted) {
          setFallbackTransactions();
        }
      } catch (err) {
        if (isMounted) {
          setFallbackTransactions();
        }
      } finally {
        if (isMounted) setLoadingHistory(false);
      }
    };

    const setFallbackTransactions = () => {
      setTransactions([
        { points: 10, reason: 'First Disease Report in Nashik Sector', created_at: new Date(Date.now() - 3600000 * 2).toISOString() },
        { points: 5, reason: 'Agronomist Validated Leaf Diagnostic', created_at: new Date(Date.now() - 3600000 * 18).toISOString() },
        { points: 2, reason: 'Shared Neem Oil IPM Advisory', created_at: new Date(Date.now() - 3600000 * 42).toISOString() },
        { points: 1, reason: 'Routine Field Health Scout', created_at: new Date(Date.now() - 3600000 * 70).toISOString() },
      ]);
    };

    loadLedger();
    return () => {
      isMounted = false;
    };
  }, [user?.id]);

  // Calculate current tier and progress
  const getCurrentTier = (points: number) => {
    let active = TIERS[0];
    let next: TierInfo | null = TIERS[1];
    for (let i = 0; i < TIERS.length; i++) {
      if (points >= TIERS[i].minPoints) {
        active = TIERS[i];
        next = i + 1 < TIERS.length ? TIERS[i + 1] : null;
      } else {
        break;
      }
    }
    return { active, next };
  };

  const { active: activeTier, next: nextTier } = getCurrentTier(currentPoints);
  const progressPercent = nextTier
    ? Math.min(100, Math.round(((currentPoints - activeTier.minPoints) / (nextTier.minPoints - activeTier.minPoints)) * 100))
    : 100;
  const pointsToNext = nextTier ? Math.max(0, nextTier.minPoints - currentPoints) : 0;

  // Interactive quick action handler
  const handlePerformAction = async (actionKey: string, points: number, reason: string) => {
    setActionLoading(actionKey);
    try {
      try {
        await GamificationService.awardAction(actionKey, user?.id);
      } catch (err) {
        // Fallback for offline or local dev
      }

      const newTotal = currentPoints + points;
      updatePoints(newTotal, reason, activeTier.badge);
      showPointsToast(points, reason, activeTier.badge);

      // Add to front of recent transactions
      setTransactions((prev) => [
        {
          points,
          reason,
          created_at: new Date().toISOString(),
        },
        ...prev.slice(0, 7),
      ]);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Main Points & Rank Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-800 via-teal-900 to-slate-900 text-white p-6 sm:p-8 shadow-xl border border-emerald-500/20">
        {/* Glow ambient effects */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-64 h-64 bg-amber-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 text-emerald-300 text-xs font-bold tracking-wider uppercase">
              <Sparkles className="w-4 h-4 text-amber-400 animate-spin" style={{ animationDuration: '8s' }} />
              Farmer Scout Rewards Ledger
            </div>

            <div className="mt-2 flex items-baseline gap-3">
              <span
                className={`text-5xl sm:text-6xl font-black tracking-tight transition-all duration-300 ${
                  isAnimating ? 'text-amber-300 scale-105 filter drop-shadow-[0_0_12px_rgba(251,191,36,0.5)]' : 'text-white'
                }`}
              >
                {displayedPoints}
              </span>
              <span className="text-xl font-bold text-emerald-300">points</span>

              {/* Floating Delta Badge */}
              {pointDelta !== null && pointDelta > 0 && (
                <span className="animate-bounce inline-flex items-center px-2.5 py-1 rounded-full text-xs font-black bg-amber-400 text-amber-950 shadow-lg ring-2 ring-amber-300">
                  +{pointDelta} PTS!
                </span>
              )}
            </div>

            <div className="mt-2 flex items-center gap-2">
              <span className="px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-xs font-bold text-emerald-200 border border-white/15">
                {activeTier.badge}
              </span>
              <span className="text-xs text-slate-300">
                {user ? user.name : 'Guest Scout'} • {user?.email || 'Verified Field Agent'}
              </span>
            </div>
          </div>

          {/* Progress to Next Tier */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/15 md:w-72 flex flex-col justify-between">
            <div className="flex justify-between items-center text-xs font-bold mb-2">
              <span className="text-slate-200">Next Milestone</span>
              <span className="text-amber-300">{nextTier ? nextTier.name : 'Max Tier Reached!'}</span>
            </div>

            {/* Bar */}
            <div className="w-full bg-slate-900/50 rounded-full h-3 overflow-hidden p-0.5 border border-white/10">
              <div
                className="bg-gradient-to-r from-emerald-400 via-teal-300 to-amber-300 h-full rounded-full transition-all duration-1000 ease-out shadow-sm"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            <div className="flex justify-between items-center text-[11px] text-slate-300 mt-2 font-medium">
              <span>{progressPercent}% Complete</span>
              <span>{nextTier ? `${pointsToNext} pts to unlock` : 'Legendary Scout'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Actions to Earn More Points */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-extrabold text-gray-900 text-base flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            Ways to Earn Points
          </h3>
          <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
            Active Bounties
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Action 1: Upload Diagnosis */}
          <Link
            to="/report"
            className="group p-4 rounded-2xl border border-slate-100 hover:border-emerald-300 bg-slate-50/70 hover:bg-emerald-50/50 transition-all flex items-start gap-3 text-left"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <Camera className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-gray-900 group-hover:text-emerald-800">Diagnose Leaf</span>
                <span className="text-xs font-black text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                  +10 pts
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                Snap leaf photo. First report in village gets maximum points!
              </p>
            </div>
          </Link>

          {/* Action 2: Share Advisory */}
          <button
            onClick={() => handlePerformAction('share_advisory', 2, 'Shared Treatment Advisory with Village Farmers')}
            disabled={actionLoading === 'share_advisory'}
            className="group p-4 rounded-2xl border border-slate-100 hover:border-emerald-300 bg-slate-50/70 hover:bg-emerald-50/50 transition-all flex items-start gap-3 text-left disabled:opacity-60"
          >
            <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <Share2 className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-gray-900 group-hover:text-emerald-800">Share Advisory</span>
                <span className="text-xs font-black text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                  +2 pts
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                Spread bio-fungicide or IPM prevention tips to peer farmers.
              </p>
            </div>
          </button>

          {/* Action 3: Routine Scout Check */}
          <button
            onClick={() => handlePerformAction('routine_scout', 1, 'Completed Routine Field Scouting Patrol')}
            disabled={actionLoading === 'routine_scout'}
            className="group p-4 rounded-2xl border border-slate-100 hover:border-emerald-300 bg-slate-50/70 hover:bg-emerald-50/50 transition-all flex items-start gap-3 text-left disabled:opacity-60"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <Eye className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-gray-900 group-hover:text-emerald-800">Routine Scout</span>
                <span className="text-xs font-black text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                  +1 pt
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                Log daily check-in to confirm healthy crop status.
              </p>
            </div>
          </button>

          {/* Action 4: Outbreak Watch */}
          <Link
            to="/community"
            className="group p-4 rounded-2xl border border-slate-100 hover:border-emerald-300 bg-slate-50/70 hover:bg-emerald-50/50 transition-all flex items-start gap-3 text-left"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-gray-900 group-hover:text-emerald-800">Outbreak Radar</span>
                <span className="text-xs font-black text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                  +5 pts
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                Inspect local disease hotspots and alert neighbors.
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Rewards Ledger */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-extrabold text-gray-900 text-base flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-500" />
            Recent Point Ledger
          </h3>
          <span className="text-xs text-slate-400 font-medium">Last 5 activities</span>
        </div>

        <div className="divide-y divide-slate-100">
          {transactions.slice(0, 5).map((t, idx) => (
            <div key={idx} className="py-3 flex items-center justify-between gap-4 first:pt-0 last:pb-0">
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                    t.points > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                  }`}
                >
                  {t.points > 0 ? `+${t.points}` : t.points}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-gray-800 truncate">{t.reason}</p>
                  <p className="text-[11px] text-gray-400">
                    {t.created_at ? new Date(t.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recently'}
                  </p>
                </div>
              </div>

              <span
                className={`text-xs font-extrabold flex-shrink-0 ${
                  t.points > 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {t.points > 0 ? `+${t.points} pts` : `${t.points} pts`}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PointsCard;
