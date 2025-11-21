/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{html,ts}",
    ],
    theme: {
        extend: {
            colors: {
                gray: {
                    900: '#111827',
                    800: '#1F2937',
                    700: '#374151',
                    600: '#4B5563',
                    500: '#6B7280',
                    400: '#9CA3AF',
                    300: '#D1D5DB',
                    200: '#E5E7EB',
                    100: '#F3F4F6',
                    50: '#F9FAFB',
                },
                primary: {
                    DEFAULT: '#6366f1', // Indigo 500
                    hover: '#4f46e5',   // Indigo 600
                },
                accent: {
                    DEFAULT: '#8b5cf6', // Violet 500
                    hover: '#7c3aed',   // Violet 600
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
