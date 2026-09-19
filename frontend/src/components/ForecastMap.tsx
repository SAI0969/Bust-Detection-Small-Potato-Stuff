import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Rectangle, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { LocationOption, ALL_LOCATIONS } from '../services/api';
import { 
  Layers, 
  MapPin, 
  Building2, 
  Compass, 
  Droplets, 
  Thermometer, 
  Wind, 
  ShieldAlert, 
  ShieldCheck,
  Maximize2
} from 'lucide-react';

export type WeatherMapLayer = 'rain' | 'temp' | 'wind' | 'bust' | 'confidence';

interface Props {
  center: [number, number];
  regionName: string;
  confidence: number;
  regions?: LocationOption[];
  onSelectRegion?: (regionName: string) => void;
  isCity?: boolean;
  rainForecast?: number;
  temperature?: number;
  viewMode?: string;
}

// Controller for smooth cinematic fly-to transitions
const MapPanController: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 1.4, easeLinearity: 0.25 });
  }, [center, zoom, map]);
  return null;
};

// Resize Watcher to prevent gray tiles or clipped canvas upon tab/mode changes
const MapResizeReloader: React.FC<{ activeLayer: string; viewMode?: string }> = ({ activeLayer, viewMode }) => {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);
    return () => clearTimeout(timer);
  }, [map, activeLayer, viewMode]);
  return null;
};

export const ForecastMap: React.FC<Props> = ({
  center,
  regionName,
  confidence,
  regions = ALL_LOCATIONS,
  onSelectRegion,
  isCity = false,
  rainForecast = 85.0,
  temperature = 29.5,
  viewMode = 'integrated'
}) => {
  const [activeLayer, setActiveLayer] = useState<WeatherMapLayer>('rain');
  const containerRef = useRef<HTMLDivElement>(null);

  // Zoom levels: tighter for cities, wider for states
  const deltaLat = isCity ? 0.45 : 1.8;
  const deltaLon = isCity ? 0.55 : 2.2;
  const zoomLevel = isCity ? 8 : 6;

  const bounds: [[number, number], [number, number]] = [
    [center[0] - deltaLat, center[1] - deltaLon],
    [center[0] + deltaLat, center[1] + deltaLon]
  ];

  // Helper to approximate regional values for all Indian locations
  const getLocationLayerValue = (r: LocationOption, layer: WeatherMapLayer) => {
    const name = r.name.toLowerCase();
    const isHighRain = name.includes('mumbai') || name.includes('dehradun') || name.includes('kochi') || name.includes('konkan') || name.includes('kerala') || name.includes('shillong');
    const isHot = name.includes('delhi') || name.includes('jaipur') || name.includes('rajasthan') || name.includes('ahmedabad');
    const isCoastal = name.includes('visakhapatnam') || name.includes('chennai') || name.includes('kolkata') || name.includes('bhubaneswar') || name.includes('puri');

    switch (layer) {
      case 'rain':
        if (isHighRain) return { val: 145.0, text: '145.0 mm/day (Heavy Deluge)' };
        if (isCoastal) return { val: 105.0, text: '105.0 mm/day (Depression Inflow)' };
        if (isHot) return { val: 32.0, text: '32.0 mm/day (Scattered)' };
        return { val: 65.0, text: '65.0 mm/day (Moderate)' };

      case 'temp':
        if (isHot) return { val: 37.5, text: '37.5°C (Heat Wave)' };
        if (isCoastal) return { val: 32.0, text: '32.0°C (Humid Tropical)' };
        if (name.includes('bengaluru') || name.includes('dehradun')) return { val: 24.5, text: '24.5°C (Pleasant)' };
        return { val: 29.5, text: '29.5°C (Seasonal)' };

      case 'wind':
        if (isCoastal || isHighRain) return { val: 28.0, text: '28.0 km/h (Squally Surge)' };
        return { val: 14.0, text: '14.0 km/h (Gentle Breeze)' };

      case 'bust':
        const bustRate = r.historical_bust_rate_pct || 32.0;
        return { val: bustRate, text: `${bustRate}% Bust Probability` };

      case 'confidence':
      default:
        const confVal = 100 - (r.historical_bust_rate_pct || 32.0);
        return { val: confVal, text: `${confVal}% Forecast Confidence` };
    }
  };

  // Color selector based on layer
  const getLayerColor = (layer: WeatherMapLayer, conf: number, precip: number, temp: number) => {
    switch (layer) {
      case 'rain':
        if (precip >= 120) return '#38bdf8'; // Heavy deluge (Bright cyan)
        if (precip >= 60) return '#0284c7';  // Moderate rain (Royal blue)
        if (precip >= 20) return '#0ea5e9';  // Light-moderate (Sky blue)
        return '#7dd3fc';
      case 'temp':
        if (temp >= 36) return '#f43f5e';    // Severe heat (Rose-red)
        if (temp >= 30) return '#f97316';    // Warm (Orange)
        if (temp >= 25) return '#eab308';    // Pleasant (Yellow)
        return '#06b6d4';                    // Cool
      case 'wind':
        return '#a855f7';
      case 'bust':
        const bustOdds = 100 - conf;
        if (bustOdds >= 40) return '#f43f5e'; // High bust risk (Red)
        if (bustOdds >= 25) return '#f59e0b'; // Moderate (Amber)
        return '#10b981';                     // Safe (Emerald)
      case 'confidence':
      default:
        if (conf < 40) return '#f43f5e';
        if (conf < 70) return '#f59e0b';
        return '#10b981';
    }
  };

  const currentColor = getLayerColor(activeLayer, confidence, rainForecast, temperature);

  return (
    <div ref={containerRef} className="relative w-full h-[430px] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950 isolate z-0">
      {/* Top Floating Weather Layer Toolbar (Windy/Ventusky Style) */}
      <div className="absolute top-3 left-3 z-10 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 p-1 rounded-xl shadow-2xl flex items-center gap-1">
        <button
          onClick={() => setActiveLayer('rain')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
            activeLayer === 'rain'
              ? 'bg-sky-600 text-white shadow-md shadow-sky-600/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
          title="NWP Precipitation Radar Field"
        >
          <Droplets size={12} />
          <span>Rain Radar</span>
        </button>

        <button
          onClick={() => setActiveLayer('temp')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
            activeLayer === 'temp'
              ? 'bg-orange-600 text-white shadow-md shadow-orange-600/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
          title="Surface 2m Temperature Field"
        >
          <Thermometer size={12} />
          <span>Temperature</span>
        </button>

        <button
          onClick={() => setActiveLayer('wind')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
            activeLayer === 'wind'
              ? 'bg-purple-600 text-white shadow-md shadow-purple-600/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
          title="Wind Vectors & MSLP"
        >
          <Wind size={12} />
          <span>Wind & MSLP</span>
        </button>

        <button
          onClick={() => setActiveLayer('bust')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
            activeLayer === 'bust'
              ? 'bg-rose-600 text-white shadow-md shadow-rose-600/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
          title="AI Forecast Bust Probability Zones"
        >
          <ShieldAlert size={12} />
          <span>Bust Zones</span>
        </button>

        <button
          onClick={() => setActiveLayer('confidence')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
            activeLayer === 'confidence'
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
          title="Forecast Confidence Map"
        >
          <ShieldCheck size={12} />
          <span>Confidence</span>
        </button>
      </div>

      {/* Floating Layer-Sensitive Legend Overlay */}
      <div className="absolute top-3 right-3 z-10 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 p-2.5 rounded-xl shadow-2xl text-xs space-y-1.5 pointer-events-auto">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
          <Compass size={12} className="text-sky-400" />
          <span>
            {activeLayer === 'rain' && 'Precipitation Radar (mm/day)'}
            {activeLayer === 'temp' && 'Surface Temperature (°C)'}
            {activeLayer === 'wind' && 'Wind Vectors (km/h)'}
            {activeLayer === 'bust' && 'Bust Breakdown Odds (%)'}
            {activeLayer === 'confidence' && 'Model Confidence Score (%)'}
          </span>
        </div>

        {activeLayer === 'rain' && (
          <div className="space-y-1 text-[10px]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50"></span>
              <span className="text-slate-300">Extreme Deluge (&ge;120 mm)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500 shadow-sm shadow-sky-500/50"></span>
              <span className="text-slate-300">Heavy Rain (60-119 mm)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600 shadow-sm shadow-blue-600/50"></span>
              <span className="text-slate-300">Moderate Showers (&lt;60 mm)</span>
            </div>
          </div>
        )}

        {activeLayer === 'temp' && (
          <div className="space-y-1 text-[10px]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50"></span>
              <span className="text-slate-300">Severe Heat Wave (&ge;36°C)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50"></span>
              <span className="text-slate-300">Tropical Warm (28-35°C)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50"></span>
              <span className="text-slate-300">Pleasant / Hills (&lt;28°C)</span>
            </div>
          </div>
        )}

        {activeLayer === 'bust' && (
          <div className="space-y-1 text-[10px]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50"></span>
              <span className="text-slate-300">Critical Bust Zone (&ge;40%)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50"></span>
              <span className="text-slate-300">Moderate Uncertainty (25-39%)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
              <span className="text-slate-300">Controlled Predictability (&lt;25%)</span>
            </div>
          </div>
        )}

        {(activeLayer === 'confidence' || activeLayer === 'wind') && (
          <div className="space-y-1 text-[10px]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
              <span className="text-slate-300">High Confidence (&ge;70%)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50"></span>
              <span className="text-slate-300">Caution (40-69%)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50"></span>
              <span className="text-slate-300">Critical Bust Risk (&lt;40%)</span>
            </div>
          </div>
        )}
      </div>

      {/* Floating Selected Focal Station Tag */}
      <div className="absolute bottom-3 left-3 z-10 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 px-3.5 py-2 rounded-xl shadow-2xl text-xs flex items-center gap-2.5 pointer-events-auto">
        <div className="w-2.5 h-2.5 rounded-full bg-sky-400 animate-ping"></div>
        {isCity ? <Building2 size={15} className="text-sky-400" /> : <MapPin size={15} className="text-emerald-400" />}
        <div>
          <div className="font-bold text-white text-xs flex items-center gap-1.5">
            <span>{regionName}</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
              {isCity ? 'City Station' : 'Region'}
            </span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            {center[0].toFixed(2)}°N, {center[1].toFixed(2)}°E &nbsp;•&nbsp; 
            {activeLayer === 'rain' && ` ${rainForecast.toFixed(1)} mm/day`}
            {activeLayer === 'temp' && ` ${temperature.toFixed(1)}°C`}
            {activeLayer === 'bust' && ` ${(100 - confidence)}% Bust Risk`}
            {activeLayer === 'confidence' && ` ${confidence}% Stability`}
          </div>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <MapContainer
        center={center}
        zoom={zoomLevel}
        scrollWheelZoom={false}
        attributionControl={false}
        className="w-full h-full"
      >
        <MapPanController center={center} zoom={zoomLevel} />
        <MapResizeReloader activeLayer={activeLayer} viewMode={viewMode} />

        {/* Esri World Dark Gray Basemap & Reference Layers (Crisp, High-Res, No Watermarks) */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
        />
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
        />

        {/* Selected Sector Bounding Polygon */}
        <Rectangle
          bounds={bounds}
          pathOptions={{
            color: currentColor,
            weight: 2.5,
            fillColor: currentColor,
            fillOpacity: 0.26
          }}
        >
          <Popup>
            <div className="font-sans text-xs text-slate-900 p-1.5 min-w-[190px]">
              <div className="flex items-center justify-between mb-1">
                <strong className="text-slate-950 font-bold text-sm">{regionName}</strong>
                <span className="text-[9px] px-1.5 py-0.5 rounded font-bold bg-sky-100 text-sky-800">
                  {isCity ? 'City Station' : 'Region'}
                </span>
              </div>
              <div className="space-y-0.5 text-slate-600 text-[11px] pt-1 border-t border-slate-200">
                <div>Model Confidence: <strong className="text-slate-900">{confidence}%</strong></div>
                <div>Bust Probability: <strong className="text-slate-900">{100 - confidence}%</strong></div>
                <div>Rainfall Estimate: <strong className="text-slate-900">{rainForecast.toFixed(1)} mm</strong></div>
                <div>Surface Temp: <strong className="text-slate-900">{temperature.toFixed(1)}°C</strong></div>
              </div>
            </div>
          </Popup>
        </Rectangle>

        {/* Active Selected Location Radar Center Marker */}
        <CircleMarker
          center={center}
          radius={isCity ? 11 : 9}
          pathOptions={{ 
            color: '#38bdf8', 
            fillColor: '#0284c7', 
            fillOpacity: 0.95, 
            weight: 3 
          }}
        />

        {/* Markers for all other Indian cities & states with Layer-Specific Data */}
        {regions.map((r) => {
          const isSelected = r.name.toLowerCase() === regionName.toLowerCase();
          if (isSelected) return null;

          const isMarkerCity = r.type === "city";
          const layerData = getLocationLayerValue(r, activeLayer);
          const markerColor = getLayerColor(activeLayer, layerData.val, layerData.val, layerData.val);

          return (
            <CircleMarker
              key={r.id}
              center={[r.lat, r.lon]}
              radius={isMarkerCity ? 5.5 : 7}
              pathOptions={{
                color: markerColor,
                fillColor: markerColor,
                fillOpacity: 0.85,
                weight: 1.5
              }}
              eventHandlers={{
                click: () => onSelectRegion && onSelectRegion(r.name)
              }}
            >
              <Popup>
                <div className="font-sans text-xs text-slate-900 min-w-[200px] p-1">
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <strong className="text-slate-950 font-bold">{r.name}</strong>
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold ${isMarkerCity ? 'bg-sky-100 text-sky-800' : 'bg-slate-200 text-slate-700'}`}>
                      {isMarkerCity ? 'City' : 'State'}
                    </span>
                  </div>
                  {r.state && isMarkerCity && (
                    <div className="text-[10px] text-slate-500 mb-1">State: {r.state}</div>
                  )}

                  {/* Active Layer Dynamic Reading */}
                  <div className="p-1.5 rounded bg-slate-100 border border-slate-200 text-[11px] mb-2 font-mono">
                    <span className="text-slate-500 block text-[9px] uppercase font-sans">Active Layer Value:</span>
                    <strong className="text-slate-900">{layerData.text}</strong>
                  </div>

                  <div className="text-[10px] text-slate-600 mb-2 line-clamp-2 leading-snug">
                    {r.risk_profile}
                  </div>

                  <button
                    onClick={() => onSelectRegion && onSelectRegion(r.name)}
                    className="w-full bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white px-2 py-1.5 rounded-lg text-xs font-bold transition-colors shadow-sm"
                  >
                    Select {isMarkerCity ? 'City' : 'Region'}
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default ForecastMap;
