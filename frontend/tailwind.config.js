/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./**/*.html",
    "./assets/**/*.{js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        brand: "#2563eb",
        brandDark: "#1d4ed8",
        brandAccent: "#14b8a6",
      },
      boxShadow: {
        card: "0 20px 45px rgba(15, 23, 42, 0.08)",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
