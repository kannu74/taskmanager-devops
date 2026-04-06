/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mint: "#10b981",
        coral: "#f97316",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.12)",
      },
    },
  },
  plugins: [],
};
