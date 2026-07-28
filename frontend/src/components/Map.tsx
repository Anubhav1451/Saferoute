"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { default as MapGL, Source, Layer, Marker } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";

interface MapProps {
  source: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  routeType: "safest" | "balanced" | "fastest";
  crimeHotspots?: Array<{ latitude: number; longitude: number; radius: number; severity: string }>;
  route?: Array<{ latitude: number; longitude: number }>;
  triggerFlyTo?: boolean;
  onMapClick?: (lng: number, lat: number) => void;
  safestSafetyScore?: number | null;
  fastestSafetyScore?: number | null;
}

export default function Map({
  source,
  destination,
  routeType,
  crimeHotspots = [],
  route = [],
  triggerFlyTo,
  onMapClick,
  safestSafetyScore,
  fastestSafetyScore
}: MapProps) {
  const mapRef = useRef<any>(null);
  const [viewState, setViewState] = useState({
    longitude: 77.2167,
    latitude: 28.6315,
    zoom: 14,
  });
  const [mapMode, setMapMode] = useState<'cyberpunk' | 'satellite'>('cyberpunk');

  // Fly to route center with 3D view when route is calculated
  useEffect(() => {
    if (triggerFlyTo && mapRef.current && route.length > 0) {
      const centerLng = (source.lng + destination.lng) / 2;
      const centerLat = (source.lat + destination.lat) / 2;

      mapRef.current.flyTo({
        center: [centerLng, centerLat],
        zoom: 15,
        pitch: 60,
        bearing: -20,
        duration: 2500,
      });
    }
  }, [triggerFlyTo, route, source, destination]);

  // Update view state when source changes (without flyTo)
  useEffect(() => {
    if (source.lat && source.lng && !triggerFlyTo) {
      setViewState({
        longitude: source.lng,
        latitude: source.lat,
        zoom: 14,
      });
    }
  }, [source, triggerFlyTo]);

  // Memoize layer objects to prevent unnecessary recreations
  const buildingLayer = useMemo(() => ({
    id: "3d-buildings",
    source: "composite",
    "source-layer": "building",
    filter: ["==", "extrude", "true"],
    type: "fill-extrusion",
    minzoom: 14,
    paint: {
      "fill-extrusion-color": "#1a1a2e",
      "fill-extrusion-height": ["get", "height"],
      "fill-extrusion-base": ["get", "min_height"],
      "fill-extrusion-opacity": 0.8,
    },
  }), []);

// Heatmap Layer for Crime Hotspots
  const heatmapLayer = {
    id: "crime-heatmap",
    type: "heatmap",
    paint: {
      "heatmap-weight": 1,
      "heatmap-intensity": 2,
      "heatmap-color": [
        "interpolate",
        ["linear"],
        ["heatmap-density"],
        0,
        "rgba(0, 0, 255, 0)",
        0.2,
        "rgba(239, 68, 68, 0.5)",
        0.4,
        "rgba(249, 115, 22, 0.7)",
        0.6,
        "rgba(234, 179, 8, 0.8)",
        0.8,
        "rgba(239, 68, 68, 1)",
      ],
      "heatmap-radius": 50,
      "heatmap-opacity": 0.7,
    },
  };

  // Route Line Layer
  const routeLayer = useMemo(() => ({
    id: "route-line",
    type: "line",
    paint: {
      "line-color": routeType === "safest" ? "#10b981" : "#06b6d4",
      "line-width": 4,
      "line-opacity": 0.9,
      "line-blur": 0.5,
    },
  }), [routeType]);

  // Route Glow Layer
  const routeGlowLayer = useMemo(() => ({
    id: "route-glow",
    type: "line",
    paint: {
      "line-color": routeType === "safest" ? "#10b981" : "#06b6d4",
      "line-width": 8,
      "line-opacity": 0.3,
      "line-blur": 2,
    },
  }), [routeType]);

  // Safety Score Indicator Layer (small dots along route showing safety)
  const safetyPointsLayer = useMemo(() => ({
    id: "safety-points",
    type: "circle",
    paint: {
      "circle-radius": 4,
      "circle-color": [
        "interpolate",
        ["linear"],
        ["get", "safetyScore"],
        0,
        "#ef4444", // red for unsafe
        0.5,
        "#fbbf24", // yellow for moderate
        1,
        "#10b981"   // green for safe
      ],
      "circle-stroke-width": 1,
      "circle-stroke-color": "#ffffff",
      "circle-opacity": 0.8
    }
  }), []);

  // Memoize GeoJSON objects to prevent unnecessary recreations
  const routeGeoJSON = useMemo(() => route.length > 0 ? {
    type: "Feature",
    geometry: {
      type: "LineString",
      coordinates: route.map(point => [point.longitude, point.latitude]),
    },
  } : null, [route]);

  const safetyPointsGeoJSON = useMemo(() => route.length > 0 ? {
    type: "FeatureCollection",
    features: route.map((point, index) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [point.longitude, point.latitude],
      },
      properties: {
        // For demo, we'll vary safety score along the route
        // In a real app, this would come from actual safety data
        safetyScore: 0.5 + 0.5 * Math.sin(index / route.length * Math.PI)
      }
    }))
  } : null, [route]);

  const crimeGeoJSON = useMemo(() => ({
    type: "FeatureCollection",
    features: crimeHotspots.map(hotspot => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [hotspot.longitude, hotspot.latitude],
      },
      properties: {
        radius: hotspot.radius,
        severity: hotspot.severity,
      },
    })),
  }), [crimeHotspots]);

  return (
    <div className="flex-1 h-screen relative focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyber-purple/50" tabIndex={0} role="img" aria-label="Interactive map showing route, safety scores, and location markers">
      <MapGL
        ref={mapRef}
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        onClick={(evt) => {
          if (onMapClick) {
            onMapClick(evt.lngLat.lng, evt.lngLat.lat);
          }
        }}
        onContextMenu={(evt) => {
          evt.preventDefault();
          if (onMapClick) {
            onMapClick(evt.lngLat.lng, evt.lngLat.lat);
          }
        }}
        style={{ width: "100%", height: "100%" }}
        mapStyle={mapMode === 'satellite' ? 'mapbox://styles/mapbox/satellite-streets-v12' : 'mapbox://styles/mapbox/dark-v11'}
        mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN}
        attributionControl={false}
        terrain={mapMode === 'satellite' ? { source: 'mapbox://mapbox.mapbox-terrain-dem-v1', exaggeration: 1.5 } : undefined}
        cursor="crosshair"
      >
        {/* 3D Buildings Layer */}
        <Layer {...buildingLayer as any} />

        {/* Crime Heatmap Layer */}
        {crimeHotspots.length > 0 && (
          <Source id="crime-data" type="geojson" data={crimeGeoJSON}>
            <Layer {...heatmapLayer as any} />
          </Source>
        )}

        {/* Safety Points Layer (shows safety along route) */}
        {route.length > 0 && safetyPointsGeoJSON && (
          <Source id="safety-data" type="geojson" data={safetyPointsGeoJSON}>
            <Layer {...safetyPointsLayer as any} />
          </Source>
        )}

        {/* Route Glow Layer */}
        {routeGeoJSON && (
          <Source id="route-data" type="geojson" data={routeGeoJSON}>
            <Layer {...routeGlowLayer as any} />
          </Source>
        )}

        {/* Route Line Layer */}
        {routeGeoJSON && (
          <Source id="route-data-line" type="geojson" data={routeGeoJSON}>
            <Layer {...routeLayer as any} />
          </Source>
        )}

        {/* Source Marker - using Mapbox Marker component for geographic positioning */}
        {source.lat && source.lng && (
          <Marker
            longitude={source.lng}
            latitude={source.lat}
            anchor="center"
            draggable={false}
          >
            <div
              tabIndex={0}
              role="img"
              aria-label="Source location marker"
              className="relative focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyber-green focus-visible:ring-offset-2"
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  // Trigger click action if needed
                }
              }}
            >
              <div className="w-6 h-6 bg-cyber-green rounded-full shadow-neon-green animate-pulse border-2 border-white flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full" />
              </div>
              <div className="absolute -inset-2 bg-cyber-green/30 rounded-full animate-ping" />
            </div>
          </Marker>
        )}

        {/* Destination Marker - using Mapbox Marker component for geographic positioning */}
        {destination.lat && destination.lng && (
          <Marker
            longitude={destination.lng}
            latitude={destination.lat}
            anchor="center"
            draggable={false}
          >
            <div
              tabIndex={0}
              role="img"
              aria-label="Destination location marker"
              className="relative focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyber-pink focus-visible:ring-offset-2"
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  // Trigger click action if needed
                }
              }}
            >
              <div className="w-6 h-6 bg-cyber-pink rounded-full shadow-neon-pink animate-pulse border-2 border-white flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full" />
              </div>
              <div className="absolute -inset-2 bg-cyber-pink/30 rounded-full animate-ping" />
            </div>
          </Marker>
        )}

        {/* Enhanced Route Comparison Legend */}
        {(safestSafetyScore !== null || fastestSafetyScore !== null) && (
          <div className="absolute bottom-20 left-4 flex flex-col items-start gap-3 bg-cyber-black/90 backdrop-blur-xl rounded-xl p-5 border border-cyber-purple/40 shadow-2xl">
            <div className="text-white text-sm font-bold mb-1">Route Comparison</div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-4 h-4 bg-cyber-green rounded-full shadow-neon-green" />
              <span className="text-gray-300">Safest: {(safestSafetyScore !== null && safestSafetyScore !== undefined ? (safestSafetyScore * 100).toFixed(0) : 'N/A')}%</span>
            </div>
            {fastestSafetyScore !== null && fastestSafetyScore !== undefined && (
              <div className="flex items-center gap-2 text-xs">
                <div className="w-4 h-4 bg-cyber-red rounded-full shadow-neon-red" />
                <span className="text-gray-300">Fastest: {(fastestSafetyScore * 100).toFixed(0)}%</span>
              </div>
            )}
            <div className="mt-2 pt-2 border-t border-cyber-purple/30">
              <div className="text-gray-400 text-xs">AI Safety Score</div>
              <div className="text-cyber-green text-lg font-bold">
                {safestSafetyScore !== null && safestSafetyScore !== undefined ? (safestSafetyScore * 100).toFixed(0) : 'N/A'}%
              </div>
            </div>
          </div>
        )}
      </MapGL>

      {/* Map Controls Overlay */}
      <div className="absolute top-4 right-4 bg-cyber-dark/80 backdrop-blur-xl rounded-xl p-4 border border-cyber-purple/30">
        <div className="text-white text-sm font-semibold mb-2">Map Controls</div>
        <div className="space-y-2 text-gray-400 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-cyber-green rounded-full" />
            <span className="text-white">Safest Route</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-cyber-cyan rounded-full" />
            <span className="text-white">Fastest Route</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-cyber-red rounded-full" />
            <span className="text-white">Crime Hotspots</span>
          </div>
          <div className="flex items-center gap-2 py-2 border-t border-cyber-purple/20">
            <div className="flex items-center gap-2 w-full">
              <div className="w-3 h-3 bg-cyber-yellow rounded-full" />
              <span className="text-white">Satellite Mode</span>
            </div>
            <div className="flex items-center gap-2 w-full justify-end">
              <label className="relative inline-flex items-center w-8 h-4">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={mapMode === 'satellite'}
                  onChange={(e) => setMapMode(e.target.checked ? 'satellite' : 'cyberpunk')}
                  aria-label="Toggle satellite map view"
                />
                <div className="w-8 h-4 bg-gray-200 rounded-full peer peer-checked:bg-gray-200 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:h-3 after:w-3 after:rounded-full after:transition-all peer-checked:after:translate-x-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyber-purple/50"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Zoom Instructions */}
      <div className="absolute bottom-4 right-4 bg-cyber-dark/80 backdrop-blur-xl rounded-xl p-4 border border-cyber-purple/30">
        <div className="text-white text-xs space-y-1">
          <div>Zoom in to see 3D buildings</div>
          <div className="text-cyber-cyan">Click map to set Source/Destination</div>
        </div>
      </div>
    </div>
  );
}