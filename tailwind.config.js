/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./templates/**/*.{html,js}",
    "./accounts/templates/**/*.{html,js}",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        emerald: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
        },
      },
      boxShadow: {
        glass: "0 10px 30px -12px rgba(16, 185, 129, 0.35)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
