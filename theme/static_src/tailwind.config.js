/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        // Caminhos relativos à pasta theme/static_src
        '../templates/**/*.html',
        '../../templates/**/*.html', // Caso tenha templates na raiz do projeto
        '../../**/templates/**/*.html', // Busca em todos os apps
    ],
    theme: {
        extend: {
            colors: {
                // Cores extraídas do Manual de Marca [cite: 39, 40, 41, 42]
                'somnus-blue-deep': '#253786',
                'somnus-blue-inst': '#0067b1',
                'somnus-green-light': '#76b82a',
                'somnus-green-dark': '#009640',
            },
            fontFamily: {
                // Tipografia principal definida no manual [cite: 53, 66]
                'poppins': ['Poppins', 'sans-serif'],
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}