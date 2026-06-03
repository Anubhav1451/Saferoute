"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Shield, Zap, AlertTriangle, Navigation, Phone, X } from "lucide-react";

interface SidebarProps {
  onRouteCalculate: (source: { lat: number; lng: number }, dest: { lat: number; lng: number }) => void;
  onSOSTrigger: (coordinates: { lat: number; lng: number }) => void;
  currentLocation: { lat: number; lng: number };
}

export default function Sidebar({ onRouteCalculate, onSOSTrigger, currentLocation }: SidebarProps) {
  const [routeType, setRouteType] = useState<"safest" | "fastest">("safest");
  const [sourceLat, setSourceLat] = useState("28.6315");
  const [sourceLng, setSourceLng] = useState("77.2167");
  const [destLat, setDestLat] = useState("28.6350");
  const [destLng, setDestLng] = useState("77.2200");
  const [sosActive, setSOSActive] = useState(false);

  const handleCalculate = () => {
    onRouteCalculate(
      { lat: parseFloat(sourceLat), lng: parseFloat(sourceLng) },
      { lat: parseFloat(destLat), lng: parseFloat(destLng) }
    );
  };

  const handleSOS = () => {
    setSOSActive(true);
    onSOSTrigger(currentLocation);
  };

  const safetyMetrics = [
    { label: "Lit Streets", value: 85, color: "bg-cyber-green", icon: Shield },
    { label: "Active Patrols", value: 92, color: "bg-cyber-cyan", icon: Zap },
    { label: "Risk Index", value: 12, color: "bg-cyber-red", icon: AlertTriangle, max: 100 },
  ];

  return (
    <motion.div
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed left-0 top-0 h-full w-96 bg-cyber-dark/80 backdrop-blur-xl border-r border-cyber-purple/30 p-6 overflow-y-auto z-50"
    >
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyber-purple to-cyber-pink bg-clip-text text-transparent mb-2">
          SafeRoute AI
        </h1>
        <p className="text-gray-400 text-sm">Intelligent Navigation System</p>
      </motion.div>

      {/* Route Type Toggle */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mb-6"
      >
        <div className="flex items-center justify-between bg-cyber-black/50 rounded-xl p-4 border border-cyber-purple/20">
          <span className="text-gray-300 font-medium">Route Mode</span>
          <button
            onClick={() => setRouteType(routeType === "safest" ? "fastest" : "safest")}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyber-purple/20 hover:bg-cyber-purple/30 transition-all duration-300"
          >
            {routeType === "safest" ? (
              <>
                <Shield className="w-5 h-5 text-cyber-green" />
                <span className="text-cyber-green font-semibold">Safest</span>
              </>
            ) : (
              <>
                <Zap className="w-5 h-5 text-cyber-cyan" />
                <span className="text-cyber-cyan font-semibold">Fastest</span>
              </>
            )}
          </button>
        </div>
      </motion.div>

      {/* Source Input */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mb-4"
      >
        <label className="block text-gray-400 text-sm mb-2 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-cyber-green" />
          Source Location
        </label>
        <div className="grid grid-cols-2 gap-3">
          <input
            type="number"
            step="0.0001"
            value={sourceLat}
            onChange={(e) => setSourceLat(e.target.value)}
            placeholder="Latitude"
            className="bg-cyber-black/50 border border-cyber-purple/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyber-purple/50 focus:shadow-neon-purple transition-all"
          />
          <input
            type="number"
            step="0.0001"
            value={sourceLng}
            onChange={(e) => setSourceLng(e.target.value)}
            placeholder="Longitude"
            className="bg-cyber-black/50 border border-cyber-purple/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyber-purple/50 focus:shadow-neon-purple transition-all"
          />
        </div>
      </motion.div>

      {/* Destination Input */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mb-6"
      >
        <label className="block text-gray-400 text-sm mb-2 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-cyber-pink" />
          Destination
        </label>
        <div className="grid grid-cols-2 gap-3">
          <input
            type="number"
            step="0.0001"
            value={destLat}
            onChange={(e) => setDestLat(e.target.value)}
            placeholder="Latitude"
            className="bg-cyber-black/50 border border-cyber-purple/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyber-purple/50 focus:shadow-neon-purple transition-all"
          />
          <input
            type="number"
            step="0.0001"
            value={destLng}
            onChange={(e) => setDestLng(e.target.value)}
            placeholder="Longitude"
            className="bg-cyber-black/50 border border-cyber-purple/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyber-purple/50 focus:shadow-neon-purple transition-all"
          />
        </div>
      </motion.div>

      {/* Calculate Button */}
      <motion.button
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.6 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleCalculate}
        className="w-full bg-gradient-to-r from-cyber-purple to-cyber-pink text-white font-semibold py-4 rounded-xl shadow-neon-purple hover:shadow-neon-cyan transition-all duration-300 flex items-center justify-center gap-2 mb-8"
      >
        <Navigation className="w-5 h-5" />
        Calculate Route
      </motion.button>

      {/* Safety Metrics */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="space-y-4"
      >
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Shield className="w-5 h-5 text-cyber-purple" />
          Live Safety Metrics
        </h2>
        
        {safetyMetrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.8 + index * 0.1 }}
            className="bg-cyber-black/50 rounded-xl p-4 border border-cyber-purple/20"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <metric.icon className={`w-4 h-4 ${metric.color.replace('bg-', 'text-')}`} />
                <span className="text-gray-300 text-sm">{metric.label}</span>
              </div>
              <span className="text-white font-bold">
                {metric.max ? `${metric.value}/${metric.max}` : `${metric.value}%`}
              </span>
            </div>
            <div className="h-2 bg-cyber-black rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(metric.value / (metric.max || 100)) * 100}%` }}
                transition={{ duration: 1, delay: 1 + index * 0.1 }}
                className={`h-full ${metric.color} rounded-full shadow-lg`}
              />
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Status Indicator */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="mt-8 flex items-center gap-2 text-gray-400 text-sm"
      >
        <div className="w-2 h-2 bg-cyber-green rounded-full animate-pulse" />
        <span>System Online • Connaught Place, Delhi</span>
      </motion.div>

      {/* SOS Button */}
      <motion.button
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1.3 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleSOS}
        className="mt-8 w-full bg-gradient-to-r from-red-600 to-red-700 text-white font-bold py-5 rounded-xl shadow-neon-red hover:shadow-neon-red transition-all duration-300 flex items-center justify-center gap-3 animate-pulse-slow"
      >
        <Phone className="w-6 h-6" />
        <span className="text-xl">SOS EMERGENCY</span>
      </motion.button>

      {/* Emergency Overlay */}
      <AnimatePresence>
        {sosActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-red-900/80 backdrop-blur-sm z-[100] flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="bg-cyber-black/90 border-2 border-red-500 rounded-2xl p-8 max-w-md w-full mx-4 shadow-neon-red"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-3xl font-bold text-red-500 flex items-center gap-3">
                  <Phone className="w-8 h-8 animate-pulse" />
                  EMERGENCY SOS
                </h2>
                <button
                  onClick={() => setSOSActive(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-red-900/30 rounded-lg p-4 border border-red-500/30">
                  <p className="text-red-400 text-sm mb-2">Your Location:</p>
                  <p className="text-white font-mono">
                    {currentLocation.lat.toFixed(6)}, {currentLocation.lng.toFixed(6)}
                  </p>
                </div>

                <div className="bg-red-900/30 rounded-lg p-4 border border-red-500/30">
                  <p className="text-red-400 text-sm mb-2">Status:</p>
                  <p className="text-white flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                    Emergency Alert Sent
                  </p>
                </div>

                <div className="bg-red-900/30 rounded-lg p-4 border border-red-500/30">
                  <p className="text-red-400 text-sm mb-2">Emergency Contacts Notified:</p>
                  <ul className="text-white space-y-1 text-sm">
                    <li>• Police: 100</li>
                    <li>• Women's Helpline: 1091</li>
                    <li>• Emergency Services: 112</li>
                  </ul>
                </div>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSOSActive(false)}
                  className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold py-3 rounded-lg hover:from-red-700 hover:to-red-800 transition-all"
                >
                  Dismiss Alert
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
