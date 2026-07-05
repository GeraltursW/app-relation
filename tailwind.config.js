/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{vue,js}"
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border)",
        input: "var(--border)",
        ring: "var(--primary)",
        background: "var(--surface)",
        foreground: "var(--text)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "#ffffff"
        },
        secondary: {
          DEFAULT: "var(--primary-soft)",
          foreground: "var(--primary)"
        },
        muted: {
          DEFAULT: "var(--surface-soft)",
          foreground: "var(--muted)"
        },
        popover: {
          DEFAULT: "#ffffff",
          foreground: "var(--text)"
        },
        card: {
          DEFAULT: "#ffffff",
          foreground: "var(--text)"
        },
        destructive: {
          DEFAULT: "#dc2626",
          foreground: "#ffffff"
        }
      },
      borderRadius: {
        lg: "12px",
        md: "10px",
        sm: "8px"
      }
    }
  },
  plugins: []
};
