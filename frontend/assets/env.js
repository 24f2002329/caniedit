// Local/runtime overrides for static hosting.
// Set window.__ENV__.API_BASE_URL to your backend origin (no /api).
// Example: window.__ENV__ = { API_BASE_URL: "http://127.0.0.1:8000" };
window.__ENV__ = window.__ENV__ || {};

if (!window.__ENV__.API_BASE_URL) {
	const host = window.location && window.location.hostname;
	if (host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0") {
		window.__ENV__.API_BASE_URL = "http://127.0.0.1:8000";
	} else {
		window.__ENV__.API_BASE_URL = "https://api.caniedit.in";
	}
}
