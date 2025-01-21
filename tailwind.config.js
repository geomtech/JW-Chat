/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './templates/*.html',
    './static/js/jw-chat.js',
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#3874CB',
        'secondary': '#4994EC',
        'tertiary': '#C8D9F1',
        'joyauxdelaparolededieu': '#3C7F8B',
        'appliquetoiauministere': '#D68F00',
        'viechretienne': '#BF2F13',
        'jworg': '#4a6da7'
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
