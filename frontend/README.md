Frontend for CanIEdit (HTML + Tailwind + SEO pages)

- Static pages load shared header/footer via `assets/include.js`.
- Auth UI lives at `/login.html` and expects the backend at `https://api.caniedit.in/api` by default.
- Override the API origin by setting `window.APP_CONFIG = { API_BASE_URL: "https://api.example.com/api" }` before loading page scripts.
