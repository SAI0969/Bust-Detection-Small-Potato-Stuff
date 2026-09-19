"""
backend/app/api/regions.py
API router for Indian meteorological regions and major cities with quick search support.
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional

router = APIRouter(tags=["Regions"])

INDIAN_METEOROLOGICAL_REGIONS = [
    {
        "id": "AP",
        "region_id": "AP",
        "name": "Andhra Pradesh",
        "type": "state",
        "lat": 15.9129,
        "lon": 79.7400,
        "lat_center": 15.9129,
        "lon_center": 79.7400,
        "risk_profile": "Coastal Cyclones & Depression Landfall",
        "primary_risks": ["Tropical Cyclone Landfall", "Monsoon Depression Track Shift", "Storm Surge"],
        "historical_bust_rate_pct": 36.4,
        "typical_nwp_weakness": "Rapid cyclone intensification busts and 72-96hr landfall point track deviations."
    },
    {
        "id": "MH",
        "region_id": "MH",
        "name": "Maharashtra (Konkan & Vidarbha)",
        "type": "state",
        "lat": 19.7515,
        "lon": 75.7139,
        "lat_center": 19.7515,
        "lon_center": 75.7139,
        "risk_profile": "Western Ghats Orographic Extreme Rain",
        "primary_risks": ["Extreme Orographic Rainfall", "Cloudbursts", "Monsoon Depressions"],
        "historical_bust_rate_pct": 38.8,
        "typical_nwp_weakness": "Underestimating localized orographic rainfall peaks by 50-150 mm/day due to grid smoothing."
    },
    {
        "id": "GJ",
        "region_id": "GJ",
        "name": "Gujarat & Saurashtra",
        "type": "state",
        "lat": 22.2587,
        "lon": 71.1924,
        "lat_center": 22.2587,
        "lon_center": 71.1924,
        "risk_profile": "Arabian Sea Cyclones & Heat Waves",
        "primary_risks": ["Cyclonic Storms", "Pre-monsoon Heat Waves", "Heavy Monsoon Spells"],
        "historical_bust_rate_pct": 31.2,
        "typical_nwp_weakness": "Recurving Arabian Sea storm tracks and extreme summer thermal advection."
    },
    {
        "id": "OD",
        "region_id": "OD",
        "name": "Odisha Coast & Interior",
        "type": "state",
        "lat": 20.9517,
        "lon": 85.0985,
        "lat_center": 20.9517,
        "lon_center": 85.0985,
        "risk_profile": "Monsoon Depression Track Shift",
        "primary_risks": ["Monsoon Depressions", "Intense Flooding", "Bay of Bengal LPS"],
        "historical_bust_rate_pct": 39.5,
        "typical_nwp_weakness": "Displacement of monsoon depression vortex track & precipitation core shift."
    },
    {
        "id": "RJ",
        "region_id": "RJ",
        "name": "Rajasthan & Northwest India",
        "type": "state",
        "lat": 27.0238,
        "lon": 74.2179,
        "lat_center": 27.0238,
        "lon_center": 74.2179,
        "risk_profile": "Western Disturbance & Severe Heat Waves",
        "primary_risks": ["Western Disturbance", "Pre-monsoon Heat Wave", "Dust Storms"],
        "historical_bust_rate_pct": 28.4,
        "typical_nwp_weakness": "Delayed Western Disturbance onset & underpredicted maximum temperatures during heat waves."
    },
    {
        "id": "AS",
        "region_id": "AS",
        "name": "Assam & Northeast Foothills",
        "type": "state",
        "lat": 26.2006,
        "lon": 92.9376,
        "lat_center": 26.2006,
        "lon_center": 92.9376,
        "risk_profile": "Monsoon Trough Foothill Shift & Floods",
        "primary_risks": ["Monsoon Trough Foothill Shift", "Flash Floods", "Orographic Rain"],
        "historical_bust_rate_pct": 33.1,
        "typical_nwp_weakness": "Misplacing monsoon trough axis towards Himalayan foothills during break phase."
    },
    {
        "id": "KL",
        "region_id": "KL",
        "name": "Kerala & South Peninsula",
        "type": "state",
        "lat": 10.8505,
        "lon": 76.2711,
        "lat_center": 10.8505,
        "lon_center": 76.2711,
        "risk_profile": "Monsoon Onset Surges & Convective Busts",
        "primary_risks": ["Southwest Monsoon Surge", "Orographic Deluges", "Easterly Waves"],
        "historical_bust_rate_pct": 29.8,
        "typical_nwp_weakness": "Offshore trough surges poorly resolved at Day 5+ lead times."
    }
]

MAJOR_INDIAN_CITIES = [
    {
        "id": "MUM",
        "city_id": "MUM",
        "name": "Mumbai",
        "state": "Maharashtra",
        "type": "city",
        "lat": 19.0760,
        "lon": 72.8777,
        "risk_profile": "Coastal High-Density Cloudburst & Urban Flash Floods",
        "primary_risks": ["Extreme Precipitation (>150mm)", "Offshore Trough Surges", "High Tide Inundation"],
        "historical_bust_rate_pct": 42.1,
        "typical_nwp_weakness": "Underpredicting mesoscale convective cloudburst peaks along the coastline."
    },
    {
        "id": "DEL",
        "city_id": "DEL",
        "name": "New Delhi",
        "state": "Delhi NCR",
        "type": "city",
        "lat": 28.6139,
        "lon": 77.2090,
        "risk_profile": "Severe Summer Heat Waves & Winter Western Disturbances",
        "primary_risks": ["Heat Wave (>45°C)", "Dust Storm Squalls", "Unseasonal WD Hail & Rain"],
        "historical_bust_rate_pct": 29.5,
        "typical_nwp_weakness": "Underestimating peak urban heat island effect and timing of dust squall fronts."
    },
    {
        "id": "BLR",
        "city_id": "BLR",
        "name": "Bengaluru",
        "state": "Karnataka",
        "type": "city",
        "lat": 12.9716,
        "lon": 77.5946,
        "risk_profile": "Plateau Thunderstorms & Convective Waterlogging",
        "primary_risks": ["Pre-monsoon Cloudbursts", "Sudden Convective Downdrafts", "Urban Flooding"],
        "historical_bust_rate_pct": 26.2,
        "typical_nwp_weakness": "Localized evening convective cells not resolved at medium range (Day 4+)."
    },
    {
        "id": "MAA",
        "city_id": "MAA",
        "name": "Chennai",
        "state": "Tamil Nadu",
        "type": "city",
        "lat": 13.0827,
        "lon": 80.2707,
        "risk_profile": "Northeast Monsoon Deluges & Cyclonic Spells",
        "primary_risks": ["Tropical Cyclones", "Extreme NE Monsoon Rainfall", "Coastal Surge"],
        "historical_bust_rate_pct": 37.8,
        "typical_nwp_weakness": "Sudden coastal convergence zones dumping 200+ mm/day missed by coarse grids."
    },
    {
        "id": "CCU",
        "city_id": "CCU",
        "name": "Kolkata",
        "state": "West Bengal",
        "type": "city",
        "lat": 22.5726,
        "lon": 88.3639,
        "risk_profile": "Ganges Delta Cyclonic Landfall & Nor'westers",
        "primary_risks": ["Severe Kalbaishakhi (Gales)", "Cyclone Landfall Track Shift", "Delta Inundation"],
        "historical_bust_rate_pct": 35.4,
        "typical_nwp_weakness": "Deviation in Bay of Bengal cyclone track curvature and landfall point."
    },
    {
        "id": "HYD",
        "city_id": "HYD",
        "name": "Hyderabad",
        "state": "Telangana",
        "type": "city",
        "lat": 17.3850,
        "lon": 78.4867,
        "risk_profile": "Deccan Shear Vortex & Heavy Monsoon Bursts",
        "primary_risks": ["Short-duration Intense Downpours", "Pre-monsoon Heat Spikes", "Lake Inundation"],
        "historical_bust_rate_pct": 27.9,
        "typical_nwp_weakness": "Mesoscale shear lines causing localized torrential bursts missed."
    },
    {
        "id": "VTZ",
        "city_id": "VTZ",
        "name": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "type": "city",
        "lat": 17.6868,
        "lon": 83.2185,
        "risk_profile": "East Coast Cyclone Direct Landfall & Gale Winds",
        "primary_risks": ["Rapid Cyclonic Intensification", "Extreme Coastal Winds", "Storm Surge"],
        "historical_bust_rate_pct": 41.3,
        "typical_nwp_weakness": "Catastrophic central pressure fall busts during rapid cyclone intensification."
    },
    {
        "id": "AMD",
        "city_id": "AMD",
        "name": "Ahmedabad",
        "state": "Gujarat",
        "type": "city",
        "lat": 23.0225,
        "lon": 72.5714,
        "risk_profile": "Scorching Pre-Monsoon Heat Waves & Flash Floods",
        "primary_risks": ["Severe Heat Waves (>46°C)", "Sabarmati Basin Cloudbursts", "Depression Landfall"],
        "historical_bust_rate_pct": 30.1,
        "typical_nwp_weakness": "Severe underestimation of consecutive dry heatwave persistence."
    },
    {
        "id": "PNQ",
        "city_id": "PNQ",
        "name": "Pune",
        "state": "Maharashtra",
        "type": "city",
        "lat": 18.5204,
        "lon": 73.8567,
        "risk_profile": "Western Ghats Rain Shadow Spillover",
        "primary_risks": ["Ghat Orographic Catchment Floods", "Lightning Storms", "Urban Waterlogging"],
        "historical_bust_rate_pct": 28.5,
        "typical_nwp_weakness": "Miscalculating whether ghat rainfall spills over the crest into city limits."
    },
    {
        "id": "JAI",
        "city_id": "JAI",
        "name": "Jaipur",
        "state": "Rajasthan",
        "type": "city",
        "lat": 26.9124,
        "lon": 75.7873,
        "risk_profile": "Desert Margin Heat Waves & Dust Squalls (Andhi)",
        "primary_risks": ["Extreme Heat Wave (>45°C)", "Dust Storm Squalls", "Monsoon Trough Shift"],
        "historical_bust_rate_pct": 27.2,
        "typical_nwp_weakness": "Delayed onset of Western Disturbance cooling and unseasonal hail."
    },
    {
        "id": "BBI",
        "city_id": "BBI",
        "name": "Bhubaneswar",
        "state": "Odisha",
        "type": "city",
        "lat": 20.2961,
        "lon": 85.8245,
        "risk_profile": "Monsoon Low Pressure Center & Flood Deluges",
        "primary_risks": ["Monsoon Depressions", "Heavy Downpours (>120mm)", "Coastal Gale Winds"],
        "historical_bust_rate_pct": 39.8,
        "typical_nwp_weakness": "Displacement of monsoon depression center tracking across north Odisha."
    },
    {
        "id": "COK",
        "city_id": "COK",
        "name": "Kochi",
        "state": "Kerala",
        "type": "city",
        "lat": 9.9312,
        "lon": 76.2673,
        "risk_profile": "Arabian Sea Monsoon Onset & Orographic Deluges",
        "primary_risks": ["Prolonged Torrential Spells", "Coastal Surge", "High Relative Humidity Stress"],
        "historical_bust_rate_pct": 36.7,
        "typical_nwp_weakness": "Underpredicting monsoon low-level jet moisture flux hitting coast."
    },
    {
        "id": "GAU",
        "city_id": "GAU",
        "name": "Guwahati",
        "state": "Assam",
        "type": "city",
        "lat": 26.1445,
        "lon": 91.7362,
        "risk_profile": "Monsoon Trough Foothill Shift & Riverine Flash Floods",
        "primary_risks": ["Brahmaputra Flooding", "Break Monsoon Heavy Rain Spells", "Landslides"],
        "historical_bust_rate_pct": 34.0,
        "typical_nwp_weakness": "Misjudging monsoon break phase when rainfall shifts completely to foothills."
    },
    {
        "id": "LKO",
        "city_id": "LKO",
        "name": "Lucknow",
        "state": "Uttar Pradesh",
        "type": "city",
        "lat": 26.8467,
        "lon": 80.9462,
        "risk_profile": "Central Gangetic Plains Heat & Monsoon Oscillations",
        "primary_risks": ["Prolonged Heat Waves", "Heavy Monsoon Downpours", "Dense Winter Fog"],
        "historical_bust_rate_pct": 28.1,
        "typical_nwp_weakness": "Fluctuations in monsoon trough position across the Indo-Gangetic belt."
    },
    {
        "id": "SXR",
        "city_id": "SXR",
        "name": "Srinagar",
        "state": "Jammu & Kashmir",
        "type": "city",
        "lat": 34.0837,
        "lon": 74.7973,
        "risk_profile": "Himalayan Western Disturbance & Severe Cold Waves",
        "primary_risks": ["Intense Snow/Rain Storms", "Cold Waves (< -4°C)", "Avalanche / Landslide Risk"],
        "historical_bust_rate_pct": 38.2,
        "typical_nwp_weakness": "Orographic complex terrain errors in precipitable water and snow level."
    },
    {
        "id": "PAT",
        "city_id": "PAT",
        "name": "Patna",
        "state": "Bihar",
        "type": "city",
        "lat": 25.5941,
        "lon": 85.1376,
        "risk_profile": "Mid-Gangetic Monsoon Floods & Severe Lightning",
        "primary_risks": ["Lightning Cloudbursts", "Ganga Basin Inundation", "Heat Waves"],
        "historical_bust_rate_pct": 32.5,
        "typical_nwp_weakness": "Severe convective lightning complexes poorly resolved at Day 5+."
    },
    {
        "id": "STV",
        "city_id": "STV",
        "name": "Surat",
        "state": "Gujarat",
        "type": "city",
        "lat": 21.1702,
        "lon": 72.8311,
        "risk_profile": "Tapi River Basin Flooding & Coastal Surges",
        "primary_risks": ["Intense Monsoon Downpours", "Upstream Dam Spillover", "Coastal Squalls"],
        "historical_bust_rate_pct": 33.4,
        "typical_nwp_weakness": "Catchment rainfall vs coastal rainfall distribution errors."
    },
    {
        "id": "NAG",
        "city_id": "NAG",
        "name": "Nagpur",
        "state": "Maharashtra",
        "type": "city",
        "lat": 21.1458,
        "lon": 79.0882,
        "risk_profile": "Central India Core Monsoon Depression Passage",
        "primary_risks": ["Depression Vortex Deluges", "Pre-monsoon Extreme Heat (>47°C)"],
        "historical_bust_rate_pct": 31.0,
        "typical_nwp_weakness": "Monsoon depression track passing north or south of Vidarbha."
    },
    {
        "id": "BHO",
        "city_id": "BHO",
        "name": "Bhopal",
        "state": "Madhya Pradesh",
        "type": "city",
        "lat": 23.2599,
        "lon": 77.4126,
        "risk_profile": "Central Trough Oscillations & Catchment Deluges",
        "primary_risks": ["Heavy Monsoon Spells", "Summer Heat Spikes", "Reservoir Catchment Surges"],
        "historical_bust_rate_pct": 29.3,
        "typical_nwp_weakness": "Underpredicting depression rainfall intensification over central hills."
    },
    {
        "id": "TRV",
        "city_id": "TRV",
        "name": "Thiruvananthapuram",
        "state": "Kerala",
        "type": "city",
        "lat": 8.5241,
        "lon": 76.9366,
        "risk_profile": "South Peninsula Dual Monsoon Convergence",
        "primary_risks": ["Southwest & Northeast Monsoon Surges", "Coastal Gale Gusts"],
        "historical_bust_rate_pct": 26.8,
        "typical_nwp_weakness": "Equatorial easterly waves triggering unexpected downpours."
    },
    {
        "id": "IXC",
        "city_id": "IXC",
        "name": "Chandigarh",
        "state": "Punjab & Haryana",
        "type": "city",
        "lat": 30.7333,
        "lon": 76.7794,
        "risk_profile": "Sub-Mountain Foothill Cloudbursts & Western Disturbances",
        "primary_risks": ["Unseasonal Hail", "Foothill Flash Floods", "Summer Heat"],
        "historical_bust_rate_pct": 27.6,
        "typical_nwp_weakness": "Trough interaction with foothills creating localized deluges."
    },
    {
        "id": "DED",
        "city_id": "DED",
        "name": "Dehradun",
        "state": "Uttarakhand",
        "type": "city",
        "lat": 30.3165,
        "lon": 78.0322,
        "risk_profile": "Shivalik Orographic Cloudbursts & Flash Floods",
        "primary_risks": ["Cloudburst (>100mm/hr)", "Hill Slope Runoff", "Himalayan Troughs"],
        "historical_bust_rate_pct": 42.8,
        "typical_nwp_weakness": "Severe underestimation of orographic cloudburst magnitude."
    }
]

ALL_LOCATIONS = INDIAN_METEOROLOGICAL_REGIONS + MAJOR_INDIAN_CITIES

@router.get("/api/regions", response_model=List[Dict[str, Any]])
@router.get("/api/regions/", response_model=List[Dict[str, Any]])
@router.get("/api/v1/regions", response_model=List[Dict[str, Any]])
@router.get("/api/v1/regions/", response_model=List[Dict[str, Any]])
def get_regions(search: Optional[str] = Query(default=None, description="Quick search query for state or city")):
    """
    Returns the list of meteorological regions and major cities with optional search filtering.
    """
    if search:
        q = search.lower().strip()
        filtered = [
            loc for loc in ALL_LOCATIONS
            if q in loc["name"].lower() or q in loc.get("state", "").lower() or q in loc["risk_profile"].lower()
        ]
        return filtered
    return ALL_LOCATIONS

@router.get("/api/v1/cities", response_model=List[Dict[str, Any]])
@router.get("/api/v1/cities/", response_model=List[Dict[str, Any]])
def get_cities(search: Optional[str] = Query(default=None, description="Search query for Indian cities")):
    """
    Returns only major Indian cities with optional fuzzy search.
    """
    if search:
        q = search.lower().strip()
        return [c for c in MAJOR_INDIAN_CITIES if q in c["name"].lower() or q in c["state"].lower()]
    return MAJOR_INDIAN_CITIES

@router.get("/api/regions/{region_id}")
@router.get("/api/v1/regions/{region_id}")
def get_region_detail(region_id: str):
    """
    Returns detailed configuration and historical vulnerabilities for a specific region or city.
    """
    for r in ALL_LOCATIONS:
        if r["id"].upper() == region_id.upper() or r["name"].lower() == region_id.lower():
            return r
    return {"error": f"Location {region_id} not found."}
