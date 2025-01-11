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
        'viechretienne': '#BF2F13'
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography')({
      className: 'editor-container',
    }),
  ],
}
