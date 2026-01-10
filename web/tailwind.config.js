/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0a0a0a"
      }
    }
  },
  safelist: [
    // Needed because we use theme colors dynamically in classnames
    "border-blue-500/40",
    "border-cyan-500/40",
    "border-orange-500/40",
    "border-teal-500/40",
    "border-indigo-500/40",
    "border-amber-500/40",
    "bg-blue-500/10",
    "bg-cyan-500/10",
    "bg-orange-500/10",
    "bg-teal-500/10",
    "bg-indigo-500/10",
    "bg-amber-500/10",
    "text-blue-300",
    "text-cyan-300",
    "text-orange-300",
    "text-teal-300",
    "text-indigo-300",
    "text-amber-300"
  ]
};