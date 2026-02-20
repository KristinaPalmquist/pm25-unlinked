module.exports = {
  content: ["./index.html", "./js/**/*.js"],
  theme: {
    extend: {
      colors: {
        sensor: {
          good: "#00e400",
          moderate: "#ffff00",
          sensitive: "#ff7e00",
          unhealthy: "#ff0000",
          very_unhealthy: "#8f3f97",
          hazardous: "#7e0023",
        },
        dark: "#1a1a1a",
        emerald: {
          dark: "#10b981",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
