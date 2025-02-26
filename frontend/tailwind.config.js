module.exports = {
  content: ["./*.html", "./src/**/*.js"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["retro"]
  }
} 