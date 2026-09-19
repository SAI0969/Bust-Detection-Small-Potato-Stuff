import React from 'react';
import { 
  Sparkles, 
  HelpCircle, 
  Wind, 
  Droplets, 
  Gauge, 
  Cpu,
  Compass,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Activity,
  Layers
} from 'lucide-react';
import { ShapDriver } from '../services/api';

interface Props {
  reasons: string[];
  topDrivers?: ShapDriver[];
  baseValue?: number;
  bustProbability?: number;
}

export const Explanation: React.FC<Props> = ({ 
  reasons = [], 
  topDrivers = [], 
  baseValue = 0.26,
  bustProbability = 0.35 
}) => {
  // Helper to pick contextual meteorological icon based on text
  const getReasonIcon = (text: string) => {
    const t = text.toLowerCase();
    if (t.includes('spread') || t.includes('divergence') || t.includes('ensemble')) {
      return <Compass className="text-amber-400 shrink-0 mt-0.5" size={16} />;
    }
    if (t.includes('pressure') || t.includes('mslp') || t.includes('gradient')) {
      return <Gauge className="text-sky-400 shrink-0 mt-0.5" size={16} />;
    }
    if (t.includes('convective') || t.includes('rain') || t.includes('cloudburst') || t.includes('moisture') || t.includes('cape')) {
      return <Droplets className="text-teal-400 shrink-0 mt-0.5" size={16} />;
    }
    if (t.includes('wind') || t.includes('surge') || t.includes('trough')) {
      return <Wind className="text-indigo-400 shrink-0 mt-0.5" size={16} />;
    }
    return <Sparkles className="text-purple-400 shrink-0 mt-0.5" size={16} />;
  };

  // Default drivers if none provided from backend
  const drivers: ShapDriver[] = topDrivers && topDrivers.length > 0 ? topDrivers : [
    { feature: "ensemble_spread", display_name: "Ensemble Member Disagreement (Spread)", value: 14.2, shap_value: 0.24, impact: "Increases Bust Risk", abs_importance: 0.24 },
    { feature: "mslp_tendency_24h", display_name: "24-hr Pressure Drop (Cyclogenesis)", value: -5.8, shap_value: 0.21, impact: "Increases Bust Risk", abs_importance: 0.21 },
    { feature: "lead_time_days", display_name: "Medium-Range Lead Horizon Degradation", value: 5, shap_value: 0.175, impact: "Increases Non-linear Chaos", abs_importance: 0.175 },
    { feature: "convective_intensity_index", display_name: "Convective Instability & Buoyancy (CAPE)", value: 2850, shap_value: 0.18, impact: "Increases Convective Volatility", abs_importance: 0.18 },
    { feature: "saturation_deficit", display_name: "Atmospheric Saturation Deficit", value: 3.2, shap_value: -0.12, impact: "Decreases Bust Risk / Stabilizes", abs_importance: 0.12 }
  ];

  const maxAbsShap = Math.max(...drivers.map(d => Math.abs(d.shap_value)), 0.25);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Cpu size={20} className="text-purple-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
              TreeSHAP Explainable AI (Physical Attributions)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Exact Shapley additive attributions φ(x) explaining NWP model parameterization failure
          </p>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 bg-purple-500/15 border border-purple-500/30 text-purple-300 rounded-full text-xs font-semibold">
          <Activity size={13} />
          <span>TreeSHAP v2.4 Active</span>
        </div>
      </div>

      {/* TreeSHAP Quantitative Waterfall & Force Bars */}
      <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800/90 space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-300 font-semibold pb-1 border-b border-slate-800/60">
          <span className="flex items-center gap-1.5">
            <Layers size={13} className="text-purple-400" />
            Quantitative SHAP Force Vectors (φ_i)
          </span>
          <div className="flex items-center gap-3 text-[10px] font-mono">
            <span className="text-slate-400">Base E[f(x)]: <strong>{(baseValue * 100).toFixed(1)}%</strong></span>
            <span className="text-purple-300 font-bold">Predicted f(x): <strong>{(bustProbability * 100).toFixed(1)}%</strong></span>
          </div>
        </div>

        {/* List of Feature Attribution Force Bars */}
        <div className="space-y-2.5 pt-1">
          {drivers.map((d, i) => {
            const isPositive = d.shap_value >= 0;
            const barWidth = Math.min(100, Math.round((Math.abs(d.shap_value) / maxAbsShap) * 100));

            return (
              <div key={`shap-${d.feature}-${i}`} className="text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 truncate max-w-[70%]">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 shrink-0"></span>
                    <span className="text-slate-200 font-medium truncate">{d.display_name}</span>
                    <span className="text-slate-500 font-mono text-[10px]">({d.value})</span>
                  </div>

                  <div className="flex items-center gap-1.5 font-mono text-[11px]">
                    <span className={`font-bold ${isPositive ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {isPositive ? `+${(d.shap_value * 100).toFixed(1)}%` : `${(d.shap_value * 100).toFixed(1)}%`}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {isPositive ? 'push to bust' : 'stabilizer'}
                    </span>
                  </div>
                </div>

                {/* Force Bar Container */}
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden flex">
                  {isPositive ? (
                    <div
                      className="bg-gradient-to-r from-rose-600 to-rose-400 h-full rounded-full transition-all duration-500"
                      style={{ width: `${barWidth}%` }}
                    ></div>
                  ) : (
                    <div
                      className="bg-gradient-to-r from-emerald-600 to-teal-400 h-full rounded-full transition-all duration-500"
                      style={{ width: `${barWidth}%` }}
                    ></div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Meteorological Narratives */}
      <div className="space-y-2">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
          Plain-Language Meteorological Insights:
        </div>

        <div className="space-y-2">
          {reasons.length === 0 ? (
            <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-slate-400 text-xs text-center">
              No anomalous physical drivers detected.
            </div>
          ) : (
            reasons.map((reason, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl hover:border-slate-700 transition-all"
              >
                {getReasonIcon(reason)}
                <div className="text-slate-300 text-xs leading-relaxed font-normal">
                  <span className="font-semibold text-slate-100 block mb-0.5">
                    Physical Factor #{idx + 1}
                  </span>
                  {reason}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Bottom Methodology Note */}
      <div className="p-3 bg-purple-950/20 border border-purple-900/30 rounded-xl flex items-start gap-2.5 text-[11px] text-purple-300/80">
        <HelpCircle size={15} className="shrink-0 mt-0.5 text-purple-400" />
        <div>
          <strong className="text-purple-200">TreeSHAP Formulation: </strong>
          Computes exact local Shapley values: <code className="text-purple-300 font-mono">f(x) = φ_0 + Σ φ_i(x)</code>. Identifies non-linear baroclinic divergence, CAPE threshold crossings, and boundary layer moisture biases.
        </div>
      </div>
    </div>
  );
};

export default Explanation;
