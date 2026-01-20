Frontend for CanIEdit (HTML + Tailwind + SEO pages)

- Static pages load shared header/footer via `assets/include.js`.
- Auth UI reads the backend origin from `API_BASE_URL` (no hard-coded URLs).
- For Vite builds, set `API_BASE_URL` in your `.env` file and access it via `import.meta.env.API_BASE_URL`.
- For plain static builds, set `window.__ENV__ = { API_BASE_URL: "http://127.0.0.1:8000" }` in `assets/env.js` (loaded before `assets/config.js`).
