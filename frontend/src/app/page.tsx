"use client";

import { useState } from "react";
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

  const handleLocationSelect = (type: 'source' | 'dest', lat: number, lng: number) => {
    if (type === 'source') {
      setSource({ lat, lng });
      setCurrentLocation({ lat, lng });
    } else {
      setDestination({ lat, lng });
    }
  };

  const handleRouteCalculate = async (src: { lat: number; lng: number }, dest: { lat: number; lng: number }) => {
    setSource(src);
    setDestination(dest);
    setCurrentLocation(src);

    try {
      // Call backend API to calculate route
      const response = await fetch("http://localhost:8000/api/v1/route/calculate", {
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

      if (response.ok) {
        const data = await response.json();
        setRoute(routeType === "safest" ? data.safest_route : data.fastest_route);
        
        // Mock crime hotspots for demo (in real app, fetch from backend)
        setCrimeHotspots([
          { latitude: 28.6325, longitude: 77.2177, radius: 200, severity: "HIGH" },
          { latitude: 28.6340, longitude: 77.2190, radius: 150, severity: "MEDIUM" },
          { latitude: 28.6300, longitude: 77.2185, radius: 180, severity: "LOW" },
        ]);

        // Trigger flyTo animation after route is calculated
        setTriggerFlyTo(true);
        setTimeout(() => setTriggerFlyTo(false), 3000);
      }
    } catch (error) {
      console.error("Error calculating route:", error);
    }
  };

  const handleSOSTrigger = async (coordinates: { lat: number; lng: number }) => {
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
        console.error("Failed to send SOS alert");
      }
    } catch (error) {
      console.error("Error sending SOS:", error);
    }
  };

  return (
    <main className="flex h-screen bg-cyber-black overflow-hidden">
      <Sidebar 
        onRouteCalculate={handleRouteCalculate} 
        onSOSTrigger={handleSOSTrigger}
        currentLocation={currentLocation}
        onLocationSelect={handleLocationSelect}
      />
      <Map
        source={source}
        destination={destination}
        routeType={routeType}
        crimeHotspots={crimeHotspots}
        route={route}
        triggerFlyTo={triggerFlyTo}
      />
    </main>
  );
}
