import React from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  Activity, 
  CalendarClock, 
  Compass, 
  Info,
  TrendingUp,
  AlertOctagon
} from 'lucide-react';

interface Props {
  bustProbability: number;
  forecastConfidence: number;
  expectedError: number;
  regime?: string;
  validDateFormatted?: string;
  leadHours?: number;
}

export const ConfidenceCard: React.FC<Props> = ({
  bustProbability,
  forecastConfidence,
  expectedError,
  regime = "Monsoon Depression / Heavy Rain",
  validDateFormatted,
  leadHours = 120
}) => {
  const isCritical = forecastConfidence < 40;
  const isModerate = forecastConfidence >= 40 && forecastConfidence < 70;

  const statusColor = isCritical ? "text-rose-400" : isModerate ? "text-amber-400" : "text-emerald-400";
  const statusBg = isCritical ? "bg-rose-500/15 border-rose-500/30 text-rose-300" : isModerate ? "bg-amber-500/15 border-amber-500/30 text-amber-300" : "bg-emerald-500/15 border-emerald-500/30 text-emerald-300";
  const statusBadge = isCritical ? "CRITICAL BUST RISK" : isModerate ? "MODERATE UNCERTAINTY" : "HIGH CONFIDENCE";

  const getOperationalAdvice = () => {
    if (isCritical) {
      return "High probability of model track/intensity divergence. Cross-check with ensemble cluster consensus & satellite nowcasting before issuing red alerts.";
    }
    if (isModerate) {
      return "Noticeable spread in convective initiation. Monitor 12-hourly NWP updates as boundary layer parameters evolve.";
    }
    return "High deterministic consensus across ensemble members. Forecast trajectory is robust for operational planning.";
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
      {/* Background ambient accent */}
      <div className={`absolute top-0 right-0 w-48 h-48 rounded-full blur-3xl opacity-10 pointer-events-none ${isCritical ? 'bg-rose-500' : isModerate ? 'bg-amber-500' : 'bg-emerald-500'}`}></div>

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            {isCritical ? (
              <ShieldAlert className="text-rose-400" size={20} />
            ) : isModerate ? (
              <AlertTriangle className="text-amber-400" size={20} />
            ) : (
              <ShieldCheck className="text-emerald-400" size={20} />
            )}
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
              Forecast Reliability & Bust Risk
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            AI assessment of raw NWP deterministic stability
          </p>
        </div>

        <span className={`px-3 py-1 rounded-full text-xs font-bold border tracking-wide flex items-center gap-1.5 ${statusBg}`}>
          <span className="w-2 h-2 rounded-full animate-pulse bg-current"></span>
          {statusBadge}
        </span>
      </div>

      {/* Target Date Pill */}
      {validDateFormatted && (
        <div className="mb-4 px-3 py-2 bg-slate-950/80 border border-slate-800/80 rounded-lg flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <CalendarClock size={15} className="text-sky-400" />
            <span>Target Verification Date:</span>
          </div>
          <div className="font-semibold text-slate-200 flex items-center gap-1.5">
            <span className="text-sky-300 font-bold">{validDateFormatted}</span>
            <span className="text-slate-400 font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-800">
              +{leadHours}h
            </span>
          </div>
        </div>
      )}

      {/* Primary Visual Confidence Meter */}
      <div className="mb-4 bg-slate-950/60 p-4 rounded-lg border border-slate-800/60">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-300">Model Confidence Indicator</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-2xl font-black font-mono ${statusColor}`}>{forecastConfidence}%</span>
            <span className="text-xs text-slate-500 font-mono">/ 100%</span>
          </div>
        </div>

        {/* Multi-segment Gauge Bar */}
        <div className="w-full bg-slate-800/90 rounded-full h-3 p-0.5 overflow-hidden flex">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${
              isCritical
                ? "bg-gradient-to-r from-rose-600 to-rose-400 shadow-lg shadow-rose-500/50"
                : isModerate
                ? "bg-gradient-to-r from-amber-500 to-amber-400 shadow-lg shadow-amber-500/50"
                : "bg-gradient-to-r from-emerald-500 to-emerald-400 shadow-lg shadow-emerald-500/50"
            }`}
            style={{ width: `${Math.max(5, forecastConfidence)}%` }}
          ></div>
        </div>

        <div className="flex justify-between text-[10px] text-slate-500 mt-1.5 font-mono">
          <span>0% (Bust Imminent)</span>
          <span>50% (Uncertain)</span>
          <span>100% (Robust)</span>
        </div>
      </div>

      {/* Dual Diagnosis Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        {/* Bust Probability */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Forecast Bust Probability</span>
            <AlertOctagon size={14} className={isCritical ? "text-rose-400" : "text-slate-500"} />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-xl font-bold font-mono ${statusColor}`}>
              {(bustProbability * 100).toFixed(1)}%
            </span>
            <span className="text-[11px] text-slate-400">
              {bustProbability >= 0.4 ? "High Failure Odds" : "Controlled"}
            </span>
          </div>
          <p className="text-[10px] text-slate-500 mt-1">
            Historical chance that NWP error exceeds operational safety limits
          </p>
        </div>

        {/* Expected NWP Bias */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Expected NWP Bias</span>
            <TrendingUp size={14} className="text-sky-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-sky-400">
              {expectedError >= 0 ? `+${expectedError.toFixed(1)}` : expectedError.toFixed(1)} mm
            </span>
            <span className="text-[11px] text-sky-300/80">Overprediction</span>
          </div>
          <p className="text-[10px] text-slate-500 mt-1">
            Systematic model wet bias corrected by AI regression
          </p>
        </div>
      </div>

      {/* Operational Bust Threshold Criteria Matrix */}
      <div className="mb-4 p-3 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
          <span>Operational Forecast Bust Thresholds:</span>
          <span className="text-slate-500 font-mono">Critical Limits</span>
        </div>
        <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
          <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span className="text-slate-400 block text-[9px] uppercase font-sans">Rainfall Limit</span>
            <span className="font-bold text-rose-400">&ge; 25 mm/day</span>
          </div>
          <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span className="text-slate-400 block text-[9px] uppercase font-sans">Temp Limit</span>
            <span className="font-bold text-amber-400">&ge; 3.0°C</span>
          </div>
          <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span className="text-slate-400 block text-[9px] uppercase font-sans">MSLP Limit</span>
            <span className="font-bold text-sky-400">&ge; 4.0 hPa</span>
          </div>
        </div>
      </div>

      {/* Synoptic Weather Regime & Operational Advice */}
      <div className="space-y-2">
        <div className="px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Activity size={14} className="text-teal-400" />
            <span>Dominant Weather Regime:</span>
          </div>
          <span className="font-semibold text-teal-300">{regime}</span>
        </div>

        <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg text-xs flex items-start gap-2.5">
          <Info size={16} className="text-sky-400 flex-shrink-0 mt-0.5" />
          <div className="text-slate-300 leading-relaxed text-[11px]">
            <strong className="text-slate-200">Operational Guidance: </strong>
            {getOperationalAdvice()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfidenceCard;
