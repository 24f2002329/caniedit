window.APP_CONFIG = window.APP_CONFIG || {};
window.APP_CONFIG.SUPABASE_URL =
  window.APP_CONFIG.SUPABASE_URL
  || "https://loemhxgitafdlkavgvkt.supabase.co";
window.APP_CONFIG.SUPABASE_ANON_KEY =
  window.APP_CONFIG.SUPABASE_ANON_KEY
  || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvZW1oeGdpdGFmZGxrYXZndmt0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0OTczODIsImV4cCI6MjA4NDA3MzM4Mn0.92GXA3nRTWoJY5ndt09V5Y1AKILZSb0UKJXIgGYLGxI";
window.APP_CONFIG.API_BASE_URL =
  window.APP_CONFIG.API_BASE_URL
  || (window.__ENV__ && window.__ENV__.API_BASE_URL)
  || "";

window.APP_CONFIG.GA_MEASUREMENT_ID =
  window.APP_CONFIG.GA_MEASUREMENT_ID
  || (window.__ENV__ && window.__ENV__.GA_MEASUREMENT_ID)
  || "";
