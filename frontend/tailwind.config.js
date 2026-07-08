/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#16241D",
          soft: "#3F4F47",
        },
        paper: {
          DEFAULT: "#F1EBDA",
          dark: "#E7DFC9",
          card: "#FAF6EC",
        },
        brass: {
          DEFAULT: "#B8862B",
          dark: "#93691F",
          light: "#D9AC5B",
        },
        pine: {
          DEFAULT: "#3E6259",
          dark: "#2A463F",
          light: "#5A8479",
        },
        border: "#D8CFB4",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
