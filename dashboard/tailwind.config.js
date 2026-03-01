/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0f172a",
          50: "#1e293b",
          100: "#334155",
          200: "#475569",
        },
        accent: {
          DEFAULT: "#6366f1",
          light: "#818cf8",
          dark: "#4f46e5",
        },
        state: {
          pending: "#f59e0b",
          scheduled: "#3b82f6",
          running: "#8b5cf6",
          completed: "#10b981",
          failed: "#ef4444",
          cancelled: "#6b7280",
        },
        worker: {
          active: "#10b981",
          dead: "#ef4444",
          draining: "#f59e0b",
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(99, 102, 241, 0.3)" },
          "100%": { boxShadow: "0 0 20px rgba(99, 102, 241, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};
