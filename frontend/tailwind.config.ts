import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          black: "#0a0a0f",
          dark: "#12121a",
          purple: "#8b5cf6",
          pink: "#ec4899",
          cyan: "#06b6d4",
          green: "#10b981",
          red: "#ef4444",
          orange: "#f97316",
        },
      },
      boxShadow: {
        "neon-purple": "0 0 20px rgba(139, 92, 246, 0.5)",
        "neon-cyan": "0 0 20px rgba(6, 182, 212, 0.5)",
        "neon-green": "0 0 20px rgba(16, 185, 129, 0.5)",
        "neon-red": "0 0 20px rgba(239, 68, 68, 0.5)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(139, 92, 246, 0.5)" },
          "100%": { boxShadow: "0 0 20px rgba(139, 92, 246, 0.8), 0 0 30px rgba(139, 92, 246, 0.4)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
