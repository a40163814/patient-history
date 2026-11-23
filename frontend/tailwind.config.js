/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ayush: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        triage: {
          red: '#dc2626',
          amber: '#d97706',
          green: '#16a34a',
        }
      },
      minHeight: {
        'touch': '48px'
      },
      minWidth: {
        'touch': '48px'
      }
    },
  },
  plugins: [],
}
