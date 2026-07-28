"use client";

import { useState, useEffect, useRef, useCallback, useMemo, Suspense } from "react";
import Sidebar from "@/components/Sidebar";
import Map from "@/components/Map";
import SkeletonSidebar from "@/components/SkeletonSidebar";
import SkeletonMap from "@/components/SkeletonMap";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Simple error boundary component
function ErrorBoundary({ children }: { children: React.ReactNode }) {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return (
      <div className="p-6 bg-red-50 text-red-700 rounded">
        <h2 className="text-lg font-bold mb-2">Something went wrong</h2>
        <p className="mb-4">Failed to load route data. Please try again.</p>
        <button
          onClick={() => setHasError(false)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Try Again
        </button>
      </div>
    );
  }

  return children;
}

// Resource for route data with Suspense support
function createRouteResource(source: { lat: number; lng: number }, destination: { lat: number; lng: number }, routeType: "safest" | "balanced" | "fastest") {
  let status: 'pending' | 'success' | 'error' = 'pending';
  let result: { route: any[]; safestSafetyScore: number | null; fastestSafetyScore: number | null } | null = null;
  let error: Error | null = null;
  let promise: Promise<any> | null = null;

  const executor = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source: { latitude: source.lat, longitude: source.lng },
          destination: { latitude: destination.lat, longitude: destination.lng },
          safety_weight: routeType === "safest" ? 0.7 : routeType === "balanced" ? 0.5 : 0.3,
        }),
      });
      const data = await response.json();
      if (response.ok && data.success && data.data) {
        status = 'success';
        result = {
          route: routeType === "safest" ? (data.data.safest_route ?? []) : (data.data.fastest_route ?? []),
          safestSafetyScore: data.data.safest_safety_score ?? null,
          fastestSafetyScore: data.data.fastest_safety_score ?? null,
        };
      } else {
        status = 'error';
        error = new Error(data?.message || data?.error || "Failed to calculate route");
      }
    } catch (err) {
      status = 'error';
      error = err instanceof Error ? err : new Error(String(err));
    }
  };

  // Start fetching immediately
  promise = executor();

  return {
    read() {
      if (status === 'pending') {
        // Throw the promise to trigger Suspense
        if (promise) throw promise;
        // Fallback in case promise is null (shouldn't happen)
        throw new Error("Promise is null");
      } else if (status === 'error') {
        // Throw the error to be caught by error boundary
        if (error) throw error;
        // Fallback in case error is null (shouldn't happen)
        throw new Error("Error is null");
      } else {
        // Return the result
        if (result) return result;
        // Fallback in case result is null (shouldn't happen when status is success)
        return { route: [], safestSafetyScore: null, fastestSafetyScore: null };
      }
    },
    // Allow refetching when inputs change
    refetch() {
      status = 'pending';
      result = null;
      error = null;
      promise = executor();
    }
  };
}

export default function Home() {
  const [source, setSource] = useState({ lat: 28.6315, lng: 77.2167 });
  const [destination, setDestination] = useState({ lat: 28.6350, lng: 77.2200 });
  const [routeType, setRouteType] = useState<"safest" | "balanced" | "fastest">("safest");
  const [crimeHotspots, setCrimeHotspots] = useState<any[]>([]);
  const [currentLocation, setCurrentLocation] = useState({ lat: 28.6315, lng: 77.2167 });
  const [triggerFlyTo, setTriggerFlyTo] = useState(false);
  const [mapClickStep, setMapClickStep] = useState<'source' | 'destination' | 'both'>('source');
  // New state for safety scores and loading (kept for SOS and AI insights)
  const [sosLoading, setSosLoading] = useState(false);
  const [sosError, setSosError] = useState<string | null>(null);
  const [aiInsights, setAiInsights] = useState<any>(null);
  const isMounted = useRef(false);

  // Create resource for route data - will refetch when source/destination/routeType change
  const routeResource = useMemo(() => createRouteResource(source, destination, routeType), [source, destination, routeType]);

  // Attempt to get user's current location on initial load
  useEffect(() => {
    isMounted.current = true;
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

    return () => {
      isMounted.current = false;
    };
  }, []);

  const handleLocationSelect = useCallback((type: 'source' | 'dest', lat: number, lng: number) => {
    if (type === 'source') {
      setSource({ lat, lng });
      setCurrentLocation({ lat, lng });
      setMapClickStep('destination');
    } else {
      setDestination({ lat, lng });
      setMapClickStep('both');
    }
  }, [setSource, setCurrentLocation, setDestination, setMapClickStep]);

  const handleMapClick = useCallback((lng: number, lat: number) => {
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
  }, [setSource, setCurrentLocation, setDestination, setMapClickStep]);

  const handleRouteTypeChange = useCallback((type: "safest" | "balanced" | "fastest") => {
    setRouteType(type);
  }, [setRouteType]);

  const handleSOSTrigger = useCallback(async (coordinates: { lat: number; lng: number }) => {
    setSosLoading(true);
    setSosError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/sos/trigger`, {
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
  }, [setSosLoading, setSosError]);

  // Fetch AI insights when we have route data (from resource)
  useEffect(() => {
    // Try to read route data - if it throws, we'll catch and handle via Suspense/error boundary
    let routeData;
    try {
      routeData = routeResource.read();
    } catch (err) {
      // If it's a promise, Suspense will handle it
      // If it's an error, error boundary will handle it
      return;
    }

    // If we have route data, fetch AI insights for safest route midpoint
    if (routeType === "safest" && routeData.route.length > 0) {
      // Sample midpoint of route for AI insight
      const midPoint = routeData.route[Math.floor(routeData.route.length / 2)];
      const fetchAiInsights = async () => {
        try {
          const aiResponse = await fetch(`${API_BASE_URL}/api/v1/ai/safety-score?latitude=${midPoint.latitude}&longitude=${midPoint.longitude}&radius=500`);
          if (aiResponse.ok) {
            const aiData = await aiResponse.json();
            setAiInsights(aiData.data);
          }
        } catch (e) {
          console.warn("Could not fetch AI insights:", e);
        }
      };

      fetchAiInsights();
    } else {
      setAiInsights(null);
    }
  }, [routeResource, routeType]);

  // Extract route data from resource (will throw if pending/error, handled by boundaries)
  let routeData;
  try {
    routeData = routeResource.read();
  } catch (err) {
    // If we get here, it means the error wasn't caught by Suspense/error boundary
    // This shouldn't happen in normal flow, but we'll set a fallback
    routeData = { route: [], safestSafetyScore: null, fastestSafetyScore: null };
  }

  const { route, safestSafetyScore, fastestSafetyScore } = routeData;

  return (
    <ErrorBoundary>
      <main className="flex h-screen bg-cyber-black overflow-hidden" role="main" aria-label="Main application interface">
        <Suspense fallback={<div className="flex h-screen bg-cyber-black overflow-hidden">
            <SkeletonSidebar />
            <SkeletonMap />
        </div>}>
          <Sidebar
            onRouteCalculate={(src, dest) => {
              // Update source/destination and trigger refetch
              setSource(src);
              setDestination(dest);
              setCurrentLocation(src);
              // Trigger refetch by updating routeType (or we could call refetch on resource)
              // We'll update routeType to trigger refetch via useMemo dependency
              // But we don't want to change routeType, so we'll call refetch directly
              routeResource.refetch();
            }}
            onSOSTrigger={handleSOSTrigger}
            currentLocation={currentLocation}
            onLocationSelect={handleLocationSelect}
            onRouteTypeChange={handleRouteTypeChange}
            routeType={routeType}
            routeData={route}
            sourceCoords={source}
            destCoords={destination}
            safestSafetyScore={safestSafetyScore}
            fastestSafetyScore={fastestSafetyScore}
            sosLoading={sosLoading}
            sosError={sosError}
            aiInsights={aiInsights}
            role="complementary"
            aria-label="Navigation sidebar"
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
        </Suspense>
      </main>
    </ErrorBoundary>
  );
}