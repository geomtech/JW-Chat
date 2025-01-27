/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './templates/*.html',
    './static/js/*.js',
    './static/js/**/*.js',
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
        'jworg': 'rgb(159, 185, 227)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
