/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{html,ts}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#2563EB', // Blue 600
                    hover: '#1D4ED8',   // Blue 700
                },
                // We can rely on default gray/slate, but let's ensure we have the requested palette if needed.
                // Using default Tailwind colors is usually fine for "Minimalisme radical".
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
