/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: "#5156be",
        // Minia (Themesbrand) palette — my-madec-frontend-test-v2-UI/Admin
        madec: {
          primary: "#5156be",
          light: "#7478cb",
          mid: "#6266c9",
          tint: "#eef0fa",
          active: "#f3f4fb",
          selected: "#e5e6f6",
          surface: "#f8f9fa",
          border: "#e9e9ef",
          text: "#313533",
          secondary: "#545a6d",
          muted: "#74788d",
          placeholder: "#74788d",
          danger: "#fd625e",
          dangerTint: "#ffe0df",
          success: "#2ab57d",
          successTint: "#d4f0e5",
          warning: "#ffbf53",
          warningTint: "#fff2dd",
          info: "#4ba6ef",
          infoTint: "#dbedfc",
          promo: "#ffe0df",
          sidebar: "#fbfaff",
        },
        primary: {
          50: "#f1f2fa",
          100: "#e5e6f6",
          200: "#b9bbe5",
          300: "#979ad8",
          400: "#7478cb",
          500: "#5156be",
          600: "#414598",
          700: "#313472",
          800: "#20224c",
          900: "#101126",
          950: "#0a0b19",
        },
      },
      fontFamily: {
        sans: [
          "IBM Plex Sans",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "rgba(116, 120, 141, 0.10) 0px 5px 20px -6px",
        "card-hover":
          "rgba(116, 120, 141, 0.18) 0px 10px 26px -6px",
        sidebar: "0px 2px 2px #fbfaff",
      },
      borderRadius: {
        xl: "0.5rem",
        "2xl": "0.75rem",
      },
    },
  },
  plugins: [],
}
