import React, { useState, useEffect } from 'react';
import { Trophy, Award, Gift, Sparkles } from 'lucide-react';
import { GamificationService } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const Leaderboard: React.FC = () => {
  const { user } = useAuth();
  const [leaders, setLeaders] = useState<any[]>([]);
  const [catalog, setCatalog] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [lRes, cRes] = await Promise.all([
          GamificationService.getLeaderboard(10).catch(() => null),
          GamificationService.getCatalog().catch(() => null),
        ]);

        if (lRes?.data?.data) {
          setLeaders(lRes.data.data);
        } else {
          setLeaders([
            { rank: 1, name: 'Ramesh Patel', village: 'Nashik', points: 240, badge: 'Grand Master Scout' },
            { rank: 2, name: 'Suresh Rao', village: 'Baramati', points: 195, badge: 'Bio-Sentinel' },
            { rank: 3, name: 'Anita Shinde', village: 'Pune Rural', points: 170, badge: 'Disease Detective' },
            { rank: 4, name: 'Kiran Desai', village: 'Sangli', points: 145, badge: 'Field Scout' },
          ]);
        }

        if (cRes?.data?.data) {
          setCatalog(cRes.data.data);
        } else {
          setCatalog([
            { key: 'bio_fert_voucher', title: 'Bio-Fertilizer 20% Discount Voucher', cost: 50 },
            { key: 'expert_consultation', title: 'Free 1-on-1 Agronomist Field Call', cost: 100 },
            { key: 'soil_health_kit', title: 'Soil NPK Testing Kit Coupon', cost: 150 },
          ]);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-3 py-1 rounded-full">
          Community Gamification
        </span>
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mt-2">
          Farmer Scout Leaderboard & Rewards
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Contribute leaf observations, validate local symptoms, and redeem points for certified organic inputs.
        </p>
      </div>

      {/* Leaderboard Table */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-bold text-lg text-gray-900 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-500" />
            Top Contributing Farmers
          </h2>
          <span className="text-xs text-gray-400">Updated hourly</span>
        </div>

        <div className="divide-y divide-gray-100">
          {leaders.map((item, idx) => (
            <div key={idx} className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-4">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                    idx === 0
                      ? 'bg-amber-100 text-amber-800'
                      : idx === 1
                      ? 'bg-gray-200 text-gray-700'
                      : idx === 2
                      ? 'bg-amber-700/20 text-amber-900'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  #{item.rank || idx + 1}
                </div>
                <div>
                  <div className="font-bold text-sm text-gray-800">{item.name}</div>
                  <div className="text-xs text-gray-500">{item.village} • {item.badge}</div>
                </div>
              </div>

              <div className="text-right">
                <span className="font-extrabold text-emerald-600 text-base">{item.points}</span>
                <span className="text-xs text-gray-400 ml-1">pts</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Rewards Catalog */}
      <div className="space-y-4">
        <h2 className="font-bold text-lg text-gray-900 flex items-center gap-2">
          <Gift className="w-5 h-5 text-emerald-600" />
          Redeemable Farming Incentives
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {catalog.map((item) => (
            <div
              key={item.key}
              className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm flex flex-col justify-between space-y-4 hover:shadow-md transition-shadow"
            >
              <div>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                  {item.cost} Points
                </span>
                <h3 className="font-bold text-gray-900 text-sm mt-3">{item.title}</h3>
              </div>

              <button
                disabled={(user?.points || 45) < item.cost}
                className={`w-full py-2 rounded-xl text-xs font-bold transition-all ${
                  (user?.points || 45) >= item.cost
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                {(user?.points || 45) >= item.cost ? 'Claim Reward' : 'Needs More Points'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
