/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",  // This tells Tailwind to scan these files
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}