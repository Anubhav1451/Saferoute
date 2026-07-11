"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Map from "@/components/Map";

export default function Home() {
  const [source, setSource] = useState({ lat: 28.6315, lng: 77.2167 });
  const [destination, setDestination] = useState({ lat: 28.6350, lng: 77.2200 });
  const [routeType, setRouteType] = useState<"safest" | "fastest">("safest");
  const [crimeHotspots, setCrimeHotspots] = useState<any[]>([]);
  const [route, setRoute] = useState<any[]>([]);
  const [currentLocation, setCurrentLocation] = useState({ lat: 28.6315, lng: 77.2167 });
  const [triggerFlyTo, setTriggerFlyTo] = useState(false);
  const [mapClickStep, setMapClickStep] = useState<'source' | 'destination' | 'both'>('source');
  // New state for safety scores and loading
  const [safestSafetyScore, setSafestSafetyScore] = useState<number | null>(null);
  const [fastestSafetyScore, setFastestSafetyScore] = useState<number | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [sosLoading, setSosLoading] = useState(false);
  const [sosError, setSosError] = useState<string | null>(null);
  const [aiInsights, setAiInsights] = useState<any>(null);

  // Attempt to get user's current location on initial load
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setSource({ lat: latitude, lng: longitude });
          setCurrentLocation({ lat: latitude, lng: longitude });
        },
        (error) => {
          console.warn("Geolocation failed, using fallback location:", error);
          // Keep fallback (hardcoded Connaught Place)
        }
      );
    } else {
      console.warn("Geolocation not supported by browser");
    }
  }, []);

  const handleLocationSelect = (type: 'source' | 'dest', lat: number, lng: number) => {
    if (type === 'source') {
      setSource({ lat, lng });
      setCurrentLocation({ lat, lng });
      setMapClickStep('destination');
    } else {
      setDestination({ lat, lng });
      setMapClickStep('both');
    }
  };

  const handleMapClick = (lng: number, lat: number) => {
    if (mapClickStep === 'source') {
      setSource({ lat, lng });
      setCurrentLocation({ lat, lng });
      setMapClickStep('destination');
    } else if (mapClickStep === 'destination') {
      setDestination({ lat, lng });
      setMapClickStep('both');
    } else {
      // Both are set, reset to source and set new source
      setSource({ lat, lng });
      setCurrentLocation({ lat, lng });
      setMapClickStep('destination');
    }
  };

  const handleRouteCalculate = async (src: { lat: number; lng: number }, dest: { lat: number; lng: number }) => {
    setRouteLoading(true);
    setRouteError(null);
    setSource(src);
    setDestination(dest);
    setCurrentLocation(src);

    try {
      // Call backend API to calculate route
      const response = await fetch("http://localhost:8000/api/v1/calculate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source: { latitude: src.lat, longitude: src.lng },
          destination: { latitude: dest.lat, longitude: dest.lng },
          safety_weight: routeType === "safest" ? 0.7 : 0.3,
        }),
      });

      const data = await response.json();
      console.log('[FRONTEND] Raw API response:', JSON.stringify(data, null, 2));

      if (response.ok && data.success && data.data) {
        const routeData = data.data;
        console.log('[FRONTEND] routeData keys:', Object.keys(routeData));
        console.log('[FRONTEND] safest_route length:', routeData.safest_route?.length);
        console.log('[FRONTEND] fastest_route length:', routeData.fastest_route?.length);

        setRoute(routeType === "safest"
          ? (routeData.safest_route ?? [])
          : (routeData.fastest_route ?? []));
        setSafestSafetyScore(routeData.safest_safety_score ?? null);
        setFastestSafetyScore(routeData.fastest_safety_score ?? null);

        // Get real crime hotspots from AI safety score for route points (sample a few points)
        // For demo, we'll get safety scores for a few points along the route to show AI insights
        if (routeType === "safest" && routeData.safest_route?.length > 0) {
          // Sample midpoint of route for AI insight
          const midPoint = routeData.safest_route[Math.floor(routeData.safest_route.length / 2)];
          const aiResponse = await fetch(`http://localhost:8000/api/v1/ai/safety-score?latitude=${midPoint.latitude}&longitude=${midPoint.longitude}&radius=500`);
          if (aiResponse.ok) {
            const aiData = await aiResponse.json();
            setAiInsights(aiData.data);
          }
        }

        // Trigger flyTo animation after route is calculated
        setTriggerFlyTo(true);
        setTimeout(() => setTriggerFlyTo(false), 3000);
      } else {
        const errorMsg = data?.message || data?.error || "Failed to calculate route";
        console.error('[FRONTEND] API error response:', data);
        setRouteError(errorMsg);
      }
    } catch (error) {
      console.error("Error calculating route:", error);
      setRouteError("Network error. Please check your connection.");
    } finally {
      setRouteLoading(false);
    }
  };

  const handleSOSTrigger = async (coordinates: { lat: number; lng: number }) => {
    setSosLoading(true);
    setSosError(null);
    try {
      const response = await fetch("http://localhost:8000/api/v1/sos/trigger", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          latitude: coordinates.lat,
          longitude: coordinates.lng,
          timestamp: new Date().toISOString(),
        }),
      });

      if (response.ok) {
        console.log("SOS alert sent successfully");
      } else {
        const errorData = await response.json();
        setSosError(errorData.message || "Failed to send SOS alert");
        console.error("Failed to send SOS alert");
      }
    } catch (error) {
      console.error("Error sending SOS:", error);
      setSosError("Network error. Please check your connection.");
    } finally {
      setSosLoading(false);
    }
  };

  return (
    <main className="flex h-screen bg-cyber-black overflow-hidden">
      <Sidebar
        onRouteCalculate={handleRouteCalculate}
        onSOSTrigger={handleSOSTrigger}
        currentLocation={currentLocation}
        onLocationSelect={handleLocationSelect}
        routeType={routeType}
        routeData={route}
        sourceCoords={source}
        destCoords={destination}
        safestSafetyScore={safestSafetyScore}
        fastestSafetyScore={fastestSafetyScore}
        routeLoading={routeLoading}
        routeError={routeError}
        sosLoading={sosLoading}
        sosError={sosError}
        aiInsights={aiInsights}
      />
      <Map
        source={source}
        destination={destination}
        routeType={routeType}
        crimeHotspots={crimeHotspots}
        route={route}
        triggerFlyTo={triggerFlyTo}
        onMapClick={handleMapClick}
        safestSafetyScore={safestSafetyScore}
        fastestSafetyScore={fastestSafetyScore}
      />
    </main>
  );
}