"use client";

import { useEffect, useRef, useState } from "react";
import { default as MapGL, Source, Layer, Marker } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";

interface MapProps {
  source: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  routeType: "safest" | "fastest";
  crimeHotspots?: Array<{ latitude: number; longitude: number; radius: number; severity: string }>;
  route?: Array<{ latitude: number; longitude: number }>;
  triggerFlyTo?: boolean;
}

export default function Map({ source, destination, routeType, crimeHotspots = [], route = [], triggerFlyTo }: MapProps) {
  const mapRef = useRef<any>(null);
  const [viewState, setViewState] = useState({
    longitude: 77.2167,
    latitude: 28.6315,
    zoom: 14,
  });

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

  // 3D Buildings Layer
  const buildingLayer = {
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
  };

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
  const routeLayer = {
    id: "route-line",
    type: "line",
    paint: {
      "line-color": routeType === "safest" ? "#10b981" : "#06b6d4",
      "line-width": 4,
      "line-opacity": 0.9,
      "line-blur": 0.5,
    },
  };

  // Route Glow Layer
  const routeGlowLayer = {
    id: "route-glow",
    type: "line",
    paint: {
      "line-color": routeType === "safest" ? "#10b981" : "#06b6d4",
      "line-width": 8,
      "line-opacity": 0.3,
      "line-blur": 2,
    },
  };

  // Convert route coordinates to GeoJSON
  const routeGeoJSON = route.length > 0 ? {
    type: "Feature",
    geometry: {
      type: "LineString",
      coordinates: route.map(point => [point.longitude, point.latitude]),
    },
  } : null;

  // Convert crime hotspots to GeoJSON
  const crimeGeoJSON = {
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
  };

  return (
    <div className="flex-1 h-screen relative">
      <MapGL
        ref={mapRef}
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/mapbox/dark-v11"
        mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN}
        attributionControl={false}
      >
        {/* 3D Buildings Layer */}
        <Layer {...buildingLayer} />

        {/* Crime Heatmap Layer */}
        {crimeHotspots.length > 0 && (
          <Source id="crime-data" type="geojson" data={crimeGeoJSON}>
            <Layer {...heatmapLayer} />
          </Source>
        )}

        {/* Route Glow Layer */}
        {routeGeoJSON && (
          <Source id="route-data" type="geojson" data={routeGeoJSON}>
            <Layer {...routeGlowLayer} />
          </Source>
        )}

        {/* Route Line Layer */}
        {routeGeoJSON && (
          <Source id="route-data-line" type="geojson" data={routeGeoJSON}>
            <Layer {...routeLayer} />
          </Source>
        )}

        {/* Source Marker - using Mapbox Marker component for geographic positioning */}
        {source.lat && source.lng && (
          <Marker longitude={source.lng} latitude={source.lat} anchor="center">
            <div className="w-4 h-4 bg-cyber-green rounded-full shadow-neon-green animate-pulse border-2 border-white" />
          </Marker>
        )}

        {/* Destination Marker - using Mapbox Marker component for geographic positioning */}
        {destination.lat && destination.lng && (
          <Marker longitude={destination.lng} latitude={destination.lat} anchor="center">
            <div className="w-4 h-4 bg-cyber-pink rounded-full shadow-neon-pink animate-pulse border-2 border-white" />
          </Marker>
        )}
      </MapGL>

      {/* Map Controls Overlay */}
      <div className="absolute top-4 right-4 bg-cyber-dark/80 backdrop-blur-xl rounded-xl p-4 border border-cyber-purple/30">
        <div className="text-white text-sm font-semibold mb-2">Map Controls</div>
        <div className="space-y-2 text-gray-400 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-cyber-green rounded-full" />
            <span>Safest Route</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-cyber-cyan rounded-full" />
            <span>Fastest Route</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-cyber-red rounded-full" />
            <span>Crime Hotspots</span>
          </div>
        </div>
      </div>

      {/* Zoom Instructions */}
      <div className="absolute bottom-4 right-4 bg-cyber-dark/80 backdrop-blur-xl rounded-xl p-4 border border-cyber-purple/30">
        <div className="text-gray-400 text-xs">
          Zoom in to see 3D buildings
        </div>
      </div>
    </div>
  );
}
