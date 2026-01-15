function initHeaderInteractions(root) {
  const navToggle = root.querySelector("[data-nav-toggle]");
  const navMenu = root.querySelector("[data-nav-menu]");
  const menuIcon = navToggle ? navToggle.querySelector('[data-nav-icon="menu"]') : null;
  const closeIcon = navToggle ? navToggle.querySelector('[data-nav-icon="close"]') : null;
  let mobileMenuOpen = false;

  const cleanupFns = [];
  const registerCleanup = (fn) => cleanupFns.push(fn);

  const closeDropdownFallback = () => {};
  let closeDropdown = closeDropdownFallback;

  const closeMobileMenu = () => {
    if (!navToggle || !navMenu) return;
    navMenu.classList.add("hidden");
    navMenu.classList.remove("flex");
    navToggle.setAttribute("aria-expanded", "false");
    menuIcon?.classList.remove("hidden");
    closeIcon?.classList.add("hidden");
    mobileMenuOpen = false;
    closeDropdown();
  };

  const openMobileMenu = () => {
    if (!navToggle || !navMenu) return;
    navMenu.classList.remove("hidden");
    navMenu.classList.add("flex");
    navToggle.setAttribute("aria-expanded", "true");
    menuIcon?.classList.add("hidden");
    closeIcon?.classList.remove("hidden");
    mobileMenuOpen = true;
  };

  if (navToggle) {
    const handleToggleClick = (event) => {
      event.preventDefault();
      if (mobileMenuOpen) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    };
    navToggle.addEventListener("click", handleToggleClick);
    registerCleanup(() => navToggle.removeEventListener("click", handleToggleClick));
  }

  const linkHandlers = [];
  navMenu?.querySelectorAll("a").forEach((link) => {
    const handler = () => {
      if (window.matchMedia("(min-width: 1024px)").matches) return;
      closeMobileMenu();
    };
    link.addEventListener("click", handler);
    linkHandlers.push({ link, handler });
  });
  if (linkHandlers.length) {
    registerCleanup(() => {
      linkHandlers.forEach(({ link, handler }) => link.removeEventListener("click", handler));
    });
  }

  const lgQuery = window.matchMedia("(min-width: 1024px)");
  const handleBreakpointChange = (event) => {
    if (event.matches) {
      mobileMenuOpen = false;
      navToggle?.setAttribute("aria-expanded", "false");
      menuIcon?.classList.remove("hidden");
      closeIcon?.classList.add("hidden");
      navMenu?.classList.add("hidden");
      navMenu?.classList.remove("flex");
    } else if (!mobileMenuOpen) {
      navMenu?.classList.add("hidden");
      navMenu?.classList.remove("flex");
    }
  };

  if (typeof lgQuery.addEventListener === "function") {
    lgQuery.addEventListener("change", handleBreakpointChange);
    registerCleanup(() => lgQuery.removeEventListener("change", handleBreakpointChange));
  } else if (typeof lgQuery.addListener === "function") {
    lgQuery.addListener(handleBreakpointChange);
    registerCleanup(() => lgQuery.removeListener(handleBreakpointChange));
  }

  const dropdown = root.querySelector(".has-dropdown");
  let dropdownTrigger = null;
  if (dropdown) {
    const trigger = dropdown.querySelector(".nav-trigger");
    const panel = dropdown.querySelector(".dropdown-panel");
    const chevron = trigger ? trigger.querySelector("svg") : null;
    dropdownTrigger = trigger;

    if (trigger && panel) {
      closeDropdown = () => {
        trigger.setAttribute("aria-expanded", "false");
        dropdown.classList.remove("is-open");
        panel.classList.add("hidden");
        if (chevron) {
          chevron.classList.remove("rotate-180");
        }
      };

      const openDropdown = () => {
        trigger.setAttribute("aria-expanded", "true");
        dropdown.classList.add("is-open");
        panel.classList.remove("hidden");
        if (chevron) {
          chevron.classList.add("rotate-180");
        }
      };

      const handleTriggerClick = (event) => {
        event.preventDefault();
        if (dropdown.classList.contains("is-open")) {
          closeDropdown();
        } else {
          openDropdown();
        }
      };
      trigger.addEventListener("click", handleTriggerClick);
      registerCleanup(() => trigger.removeEventListener("click", handleTriggerClick));

      if (window.matchMedia("(hover: hover)").matches) {
        dropdown.addEventListener("mouseenter", openDropdown);
        dropdown.addEventListener("mouseleave", closeDropdown);
        registerCleanup(() => {
          dropdown.removeEventListener("mouseenter", openDropdown);
          dropdown.removeEventListener("mouseleave", closeDropdown);
        });
      }

      const handleFocusOut = (event) => {
        if (!dropdown.contains(event.relatedTarget)) {
          closeDropdown();
        }
      };
      dropdown.addEventListener("focusout", handleFocusOut);
      registerCleanup(() => dropdown.removeEventListener("focusout", handleFocusOut));
    }
  }

  const handleKeydown = (event) => {
    if (event.key !== "Escape") return;

    if (dropdown && typeof closeDropdown === "function") {
      const activeElement = document.activeElement;
      const wasInsideDropdown = activeElement ? dropdown.contains(activeElement) : false;
      closeDropdown();
      if (wasInsideDropdown && dropdownTrigger) {
        dropdownTrigger.focus();
      }
    }

    if (mobileMenuOpen) {
      closeMobileMenu();
      navToggle?.focus();
    }
  };
  root.addEventListener("keydown", handleKeydown);
  registerCleanup(() => root.removeEventListener("keydown", handleKeydown));

  const handleDocumentClick = (event) => {
    if (dropdown && typeof closeDropdown === "function" && !dropdown.contains(event.target)) {
      closeDropdown();
    }
    if (
      navMenu &&
      mobileMenuOpen &&
      !navMenu.contains(event.target) &&
      (!navToggle || !navToggle.contains(event.target))
    ) {
      closeMobileMenu();
    }
  };
  document.addEventListener("click", handleDocumentClick);
  registerCleanup(() => document.removeEventListener("click", handleDocumentClick));

  return () => {
    while (cleanupFns.length) {
      const fn = cleanupFns.pop();
      try {
        fn();
      } catch (error) {
        /* ignore cleanup errors */
      }
    }
  };
}

function runPartialCleanup(el) {
  const cleanup = el.__partialCleanup;
  if (typeof cleanup === "function") {
    cleanup();
    el.__partialCleanup = null;
  }
}

function hydratePartial(id, root) {
  if (id === "header") {
    root.__partialCleanup = initHeaderInteractions(root);
  }

  if (id === "footer") {
    const yearEl = root.querySelector("[data-year-current]");
    if (yearEl) {
      yearEl.textContent = new Date().getFullYear();
    }
  }
}

function renderPartial(id, el, markup) {
  runPartialCleanup(el);
  el.innerHTML = markup;
  hydratePartial(id, el);
  document.dispatchEvent(new CustomEvent("partial:loaded", { detail: { id } }));
}

function getStorage() {
  try {
    return window.sessionStorage;
  } catch (error) {
    return null;
  }
}

async function loadPartial(id, file) {
  const el = document.getElementById(id);
  if (!el) return;

  const storage = getStorage();
  const cacheKey = `partial:${file}`;
  let cachedMarkup = null;

  if (storage) {
    try {
      cachedMarkup = storage.getItem(cacheKey);
    } catch (error) {
      cachedMarkup = null;
    }
  }

  if (cachedMarkup) {
    renderPartial(id, el, cachedMarkup);
  }

  try {
    const response = await fetch(file, { cache: cachedMarkup ? "no-cache" : "default" });
    if (!response.ok) return;

    const markup = await response.text();
    if (!cachedMarkup || markup !== cachedMarkup) {
      renderPartial(id, el, markup);
      if (storage) {
        try {
          storage.setItem(cacheKey, markup);
        } catch (error) {
          /* storage quota exceeded */
        }
      }
    }
  } catch (error) {
    if (!cachedMarkup) {
      console.error("Failed to load partial:", id, error);
    }
  }
}

function resolvePartialBase() {
  const script = document.currentScript || document.querySelector('script[src*="include.js"]');
  if (!script) {
    return "../partials/";
  }

  const explicitRoot = script.getAttribute("data-partials-root");
  if (explicitRoot) {
    return explicitRoot.endsWith("/") ? explicitRoot : `${explicitRoot}/`;
  }

  try {
    const scriptUrl = new URL(script.getAttribute("src"), window.location.href);
    const withPartials = scriptUrl.href.replace(/assets\/(?:js\/)?include\.js(?:[?#].*)?$/, "partials/");
    if (withPartials !== scriptUrl.href) {
      return withPartials.endsWith("/") ? withPartials : `${withPartials}/`;
    }

    const fallback = scriptUrl.href.replace(/[^/]*$/, "partials/");
    return fallback.endsWith("/") ? fallback : `${fallback}/`;
  } catch (error) {
    return "../partials/";
  }
}

const PARTIAL_VERSION = "v3"; // bump to bust sessionStorage cache when markup changes
const partialBase = resolvePartialBase();

loadPartial("header", `${partialBase}header.html?ver=${PARTIAL_VERSION}`);
loadPartial("footer", `${partialBase}footer.html?ver=${PARTIAL_VERSION}`);

// --- Auth-aware header helpers ---
const SUPABASE_SCRIPT_SRC = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2";
const APP_CONFIG_SRC = "/assets/config.js";
const SUPABASE_URL = () => (window.APP_CONFIG && window.APP_CONFIG.SUPABASE_URL) || "";
const SUPABASE_ANON_KEY = () => (window.APP_CONFIG && window.APP_CONFIG.SUPABASE_ANON_KEY) || "";
let supabaseClient = null;
let supabaseScriptPromise = null;
let appConfigPromise = null;

function loadAppConfig() {
  if (window.APP_CONFIG) return Promise.resolve();
  if (appConfigPromise) return appConfigPromise;
  appConfigPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = APP_CONFIG_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Unable to load app config"));
    document.head.appendChild(script);
  });
  return appConfigPromise;
}

function loadSupabaseScript() {
  if (window.supabase && typeof window.supabase.createClient === "function") {
    return Promise.resolve();
  }
  if (supabaseScriptPromise) return supabaseScriptPromise;
  supabaseScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SUPABASE_SCRIPT_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Unable to load Supabase client"));
    document.head.appendChild(script);
  });
  return supabaseScriptPromise;
}

async function getSupabaseClient() {
  let url = SUPABASE_URL();
  let anonKey = SUPABASE_ANON_KEY();
  if (!url || !anonKey) {
    try {
      await loadAppConfig();
      url = SUPABASE_URL();
      anonKey = SUPABASE_ANON_KEY();
    } catch (error) {
      return null;
    }
  }
  if (!url || !anonKey) {
    return null;
  }
  if (!supabaseClient) {
    await loadSupabaseScript();
    if (!window.supabase || typeof window.supabase.createClient !== "function") {
      return null;
    }
    supabaseClient = window.supabase.createClient(url, anonKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    });
  }
  return supabaseClient;
}

async function getSupabaseAccessToken() {
  const client = await getSupabaseClient();
  if (!client) return null;
  const { data } = await client.auth.getSession();
  return data?.session?.access_token || null;
}

function normalizeSupabaseUser(user) {
  if (!user) return null;
  const metadata = user.user_metadata || {};
  return {
    email: user.email || "",
    full_name: metadata.full_name || metadata.name || "",
  };
}

async function fetchCurrentSupabaseUser() {
  const client = await getSupabaseClient();
  if (!client) return null;
  const { data } = await client.auth.getUser();
  return normalizeSupabaseUser(data?.user);
}

function resolveApiBase() {
  return (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || "https://api.caniedit.in/api";
}

function applyHomeAuthState(user, options = {}) {
  const guestBlocks = document.querySelectorAll('[data-auth-home="guest"]');
  const userBlocks = document.querySelectorAll('[data-auth-home="user"]');
  const emailEls = document.querySelectorAll('[data-auth-home-email], [data-auth-email]');
  const initialEls = document.querySelectorAll('[data-auth-home-initial], [data-auth-initial]');
  const isPending = options.pending === true;

  const showUser = Boolean(user || isPending);

  guestBlocks.forEach((el) => el.classList.toggle("hidden", showUser));
  userBlocks.forEach((el) => el.classList.toggle("hidden", !showUser));

  if (showUser) {
    emailEls.forEach((el) => (el.textContent = user ? user.email || "Account" : "Signing in..."));
    const initial = user
      ? (user.full_name || user.email || "?").trim()[0]?.toUpperCase() || "?"
      : isPending
        ? "..."
        : "?";
    initialEls.forEach((el) => (el.textContent = initial));
  }
}

function toggleVisibility(els, shouldShow) {
  const isDesktop = window.matchMedia("(min-width: 1024px)").matches;
  els.forEach((el) => {
    const scope = el.dataset.authScope || "all";
    const matchesScope = scope === "all" || (scope === "desktop" ? isDesktop : !isDesktop);
    if (!matchesScope) return;

    if (!el.dataset.authDisplay) {
      const computed = window.getComputedStyle(el).display;
      el.dataset.authDisplay = computed && computed !== "none" ? computed : "block";
    }
    if (shouldShow) {
      el.classList.remove("hidden");
      el.style.display = el.dataset.authDisplay;
    } else {
      el.classList.add("hidden");
      el.style.display = "none";
    }
  });
}

function applyHeaderAuthState(user, options = {}) {
  const loginCtas = document.querySelectorAll("[data-auth-login]");
  const userBlocks = document.querySelectorAll("[data-auth-user]");
  const emailEls = document.querySelectorAll("[data-auth-email]");
  const initialEls = document.querySelectorAll("[data-auth-initial]");
  const isPending = options.pending === true;

  const showUser = Boolean(user || isPending);
  toggleVisibility(loginCtas, !showUser);
  toggleVisibility(userBlocks, showUser);

  emailEls.forEach((el) => (el.textContent = user ? user.email || "Account" : isPending ? "Signing in..." : "Account"));
  const initial = user
    ? (user.full_name || user.email || "?").trim()[0]?.toUpperCase() || "?"
    : isPending
      ? "..."
      : "?";
  initialEls.forEach((el) => (el.textContent = initial));
}

async function hydrateHeaderAuth() {
  applyHeaderAuthState(null, { pending: true });
  applyHomeAuthState(null, { pending: true });

  const user = await fetchCurrentSupabaseUser();
  if (user) {
    applyHeaderAuthState(user);
    applyHomeAuthState(user);
    return user;
  }

  applyHeaderAuthState(null);
  applyHomeAuthState(null);
  return null;
}

// --- Auth modal ---
const AUTH_MODAL_ID = "auth-modal";
const DEFAULT_AUTH_PROMPT = "Send a code to continue.";
const DEFAULT_LIMIT_PROMPT = "Create a free account to get 2x more merges and save history.";

let authModalBound = false;
let authModalApi = null;
const NAME_MODAL_ID = "profile-name-modal";
let nameModalBound = false;
let nameModalApi = null;
let namePromptShown = false;

function buildAuthModal() {
  if (document.getElementById(AUTH_MODAL_ID)) return;
  const modal = document.createElement("div");
  modal.id = AUTH_MODAL_ID;
  modal.className = "fixed inset-0 z-50 hidden";
  modal.innerHTML = `
    <div data-auth-overlay class="absolute inset-0 bg-slate-900/70 backdrop-blur-sm"></div>
    <div class="absolute inset-0 flex items-center justify-center px-4">
      <div class="relative w-full max-w-xl rounded-3xl border border-slate-800 bg-slate-950 text-slate-100 shadow-[0_30px_120px_-60px_rgba(0,0,0,0.8)]">
        <button data-auth-close class="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-800 text-slate-400 transition hover:text-white" aria-label="Close">
          <span aria-hidden="true">×</span>
        </button>
        <div class="grid gap-6 px-6 py-6 sm:px-8 sm:py-8">
          <div class="space-y-2">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">Frictionless access</p>
            <h2 class="text-2xl font-semibold">Sign in with email or Google</h2>
            <p class="text-sm text-slate-400">No password required. We’ll send a one-time code. Signing in doubles your daily limits and saves history.</p>
          </div>
          <div class="space-y-4">
            <label class="block space-y-2">
              <span class="text-sm font-semibold text-slate-200">Email</span>
              <input id="auth-email" class="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400" type="email" name="email" autocomplete="email" required />
            </label>
            <div class="grid gap-3 sm:grid-cols-[1fr,auto] sm:items-end">
              <label class="block space-y-2">
                <span class="text-sm font-semibold text-slate-200">6-digit code</span>
                <input id="auth-code" class="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400 disabled:opacity-60" type="text" name="code" inputmode="numeric" minlength="4" maxlength="8" autocomplete="one-time-code" placeholder="Enter code" disabled />
              </label>
              <div class="flex gap-2 sm:flex-col sm:items-stretch">
                <button id="auth-send" class="inline-flex items-center justify-center rounded-xl border border-emerald-400/40 bg-emerald-500/10 px-4 py-2.5 text-sm font-semibold text-emerald-200 transition hover:border-emerald-300/60 hover:bg-emerald-500/20" type="button">Send code</button>
                <button id="auth-verify" class="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60" type="button" disabled>Verify & Continue</button>
              </div>
            </div>
            <button id="auth-google" class="inline-flex w-full items-center justify-center gap-3 rounded-xl border border-slate-800 bg-white/5 px-4 py-3 text-sm font-semibold text-white transition hover:border-slate-700">
              <span aria-hidden="true">🔒</span> Continue with Google
            </button>
            <p id="auth-status" class="min-h-[1.25rem] text-sm text-slate-300" role="status"></p>
            <p class="text-xs text-slate-500">We never store plaintext passwords. Codes expire in minutes.</p>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function setAuthStatus(type, message) {
  const el = document.getElementById("auth-status");
  if (!el) return;
  const palette = type === "error" ? "text-rose-300" : type === "success" ? "text-emerald-300" : "text-slate-300";
  el.textContent = message;
  el.className = `min-h-[1.25rem] text-sm ${palette}`;
}

async function postJSON(path, body, token, method = "POST") {
  const headers = { "Content-Type": "application/json" };
  const supabaseToken = token || (await getSupabaseAccessToken());
  if (supabaseToken) headers.Authorization = `Bearer ${supabaseToken}`;
  const response = await fetch(`${resolveApiBase()}${path}`, {
    method,
    headers,
    credentials: "include",
    body: JSON.stringify(body),
  });
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : {};
  if (!response.ok) {
    const detail = data?.detail || "Request failed";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function wireAuthModal() {
  buildAuthModal();
  const modal = document.getElementById(AUTH_MODAL_ID);
  const overlay = modal?.querySelector("[data-auth-overlay]");
  const closeBtn = modal?.querySelector("[data-auth-close]");
  const sendBtn = document.getElementById("auth-send");
  const verifyBtn = document.getElementById("auth-verify");
  const googleBtn = document.getElementById("auth-google");
  const codeInput = document.getElementById("auth-code");
  const emailInput = document.getElementById("auth-email");

  const open = (message = DEFAULT_AUTH_PROMPT) => {
    modal?.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    setAuthStatus("neutral", message);
    emailInput?.focus();
  };

  const close = () => {
    modal?.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  };

  function attachTriggers() {
    document.querySelectorAll("[data-auth-modal-trigger]").forEach((el) => {
      if (el.dataset.authModalBound === "true") return;
      el.dataset.authModalBound = "true";
      el.addEventListener("click", (event) => {
        event.preventDefault();
        open();
      });
    });
  }

  attachTriggers();

  if (authModalBound) {
    return authModalApi;
  }

  authModalBound = true;

  overlay?.addEventListener("click", close);
  closeBtn?.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });

  sendBtn?.addEventListener("click", async () => {
    if (!emailInput) return;
    const email = emailInput.value.trim();
    if (!email) {
      setAuthStatus("error", "Enter your email to get a code.");
      return;
    }
    setAuthStatus("neutral", "Sending code...");
    sendBtn.disabled = true;
    try {
      const client = await getSupabaseClient();
      if (!client) {
        throw new Error("Supabase is not configured yet.");
      }
      const { error } = await client.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: `${window.location.origin}/dashboard.html` },
      });
      if (error) throw error;
      setAuthStatus("success", "Code sent. Check your email.");
      codeInput.disabled = false;
      verifyBtn.disabled = false;
      codeInput.focus();
    } catch (error) {
      setAuthStatus("error", error.message || "Unable to send code");
    } finally {
      sendBtn.disabled = false;
    }
  });

  verifyBtn?.addEventListener("click", async () => {
    if (!emailInput || !codeInput) return;
    const email = emailInput.value.trim();
    const code = codeInput.value.trim();
    if (!email || !code) {
      setAuthStatus("error", "Enter your email and code.");
      return;
    }
    setAuthStatus("neutral", "Verifying...");
    verifyBtn.disabled = true;
    try {
      const client = await getSupabaseClient();
      if (!client) {
        throw new Error("Supabase is not configured yet.");
      }
      const { error } = await client.auth.verifyOtp({
        email,
        token: code,
        type: "email",
      });
      if (error) throw error;
      setAuthStatus("success", "Signed in. You can keep editing.");
      const profilePromise = hydrateHeaderAuth();
      profilePromise.then(ensureProfileNamePrompt);
      close();
      document.dispatchEvent(new CustomEvent("auth:signed-in"));
    } catch (error) {
      setAuthStatus("error", error.message || "Invalid code");
    } finally {
      verifyBtn.disabled = false;
    }
  });

  googleBtn?.addEventListener("click", () => {
    setAuthStatus("neutral", "Redirecting to Google...");
    (async () => {
      const client = await getSupabaseClient();
      if (!client) {
        setAuthStatus("error", "Supabase is not configured yet.");
        return;
      }
      const { error } = await client.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}/dashboard.html` },
      });
      if (error) {
        setAuthStatus("error", error.message || "Unable to start Google sign-in.");
      }
    })();
  });

  const promptForLimit = (message) => open(message || DEFAULT_LIMIT_PROMPT);

  authModalApi = { open, close, promptForLimit, setStatus: setAuthStatus };
  window.authModal = authModalApi;
  window.promptAuthForLimit = promptForLimit;

  return authModalApi;
}

function setNameStatus(type, message) {
  const el = document.getElementById("profile-name-status");
  if (!el) return;
  const palette = type === "error" ? "text-rose-500" : type === "success" ? "text-emerald-600" : "text-slate-500";
  el.textContent = message;
  el.className = `min-h-[1.25rem] text-sm ${palette}`;
}

function buildNameModal() {
  if (document.getElementById(NAME_MODAL_ID)) return;
  const modal = document.createElement("div");
  modal.id = NAME_MODAL_ID;
  modal.className = "fixed inset-0 z-50 hidden";
  modal.innerHTML = `
    <div data-name-overlay class="absolute inset-0 bg-slate-900/70 backdrop-blur-sm"></div>
    <div class="absolute inset-0 flex items-center justify-center px-4">
      <div class="relative w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_30px_120px_-60px_rgba(15,23,42,0.5)]">
        <button data-name-close class="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:text-slate-700" aria-label="Close">
          <span aria-hidden="true">×</span>
        </button>
        <div class="space-y-4 pt-2">
          <h2 class="text-xl font-semibold text-slate-900">Tell us your name</h2>
          <p class="text-sm text-slate-600">We use it to personalize your dashboard.</p>
          <p class="text-xs text-slate-500">Signed in as <span data-name-email class="font-semibold text-slate-700"></span></p>
          <label class="block space-y-1.5">
            <span class="text-sm font-medium text-slate-700">Full name</span>
            <input id="profile-name-input" class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400" type="text" name="full_name" placeholder="Jane Doe" />
          </label>
          <p id="profile-name-status" class="min-h-[1.25rem] text-sm text-slate-500" role="status"></p>
          <div class="flex items-center justify-end gap-3">
            <button data-name-skip class="text-sm font-semibold text-slate-500 transition hover:text-slate-700" type="button">Later</button>
            <button id="profile-name-save" class="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700" type="button">Save</button>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function wireNameModal() {
  buildNameModal();
  const modal = document.getElementById(NAME_MODAL_ID);
  const overlay = modal?.querySelector("[data-name-overlay]");
  const closeBtn = modal?.querySelector("[data-name-close]");
  const skipBtn = modal?.querySelector("[data-name-skip]");
  const emailEl = modal?.querySelector("[data-name-email]");
  const input = document.getElementById("profile-name-input");
  const saveBtn = document.getElementById("profile-name-save");

  const open = (user) => {
    namePromptShown = true;
    modal?.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
    if (emailEl) {
      emailEl.textContent = user?.email || "your account";
    }
    if (input) {
      input.value = user?.full_name || "";
      input.focus();
    }
    setNameStatus("neutral", "");
  };

  const close = () => {
    modal?.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  };

  if (!nameModalBound) {
    nameModalBound = true;

    overlay?.addEventListener("click", close);
    closeBtn?.addEventListener("click", close);
    skipBtn?.addEventListener("click", () => {
      close();
    });

    saveBtn?.addEventListener("click", async () => {
      if (!input) return;
      const fullName = input.value.trim();
      if (!fullName) {
        setNameStatus("error", "Enter your name before saving.");
        input.focus();
        return;
      }
      setNameStatus("neutral", "Saving...");
      saveBtn.disabled = true;
      try {
        const client = await getSupabaseClient();
        if (!client) {
          throw new Error("Supabase is not configured yet.");
        }
        const { error } = await client.auth.updateUser({
          data: { full_name: fullName },
        });
        if (error) throw error;
        setNameStatus("success", "Saved!");
        setTimeout(() => {
          close();
          hydrateHeaderAuth();
        }, 400);
      } catch (error) {
        setNameStatus("error", error.message || "Unable to save name.");
      } finally {
        saveBtn.disabled = false;
      }
    });
  }

  nameModalApi = { open, close };
  return nameModalApi;
}

async function ensureProfileNamePrompt(user) {
  if (namePromptShown) return;
  const profile = user || (await fetchCurrentSupabaseUser());
  if (!profile) {
    return;
  }
  if (!window.location.pathname.endsWith("/dashboard.html")) {
    return;
  }
  if (profile.full_name && profile.full_name.trim()) {
    namePromptShown = true;
    return;
  }
  const modal = wireNameModal();
  if (!modal) return;
  modal.open(profile);
}

let logoutHandlerBound = false;
function bindLogoutHandler() {
  if (logoutHandlerBound) return;
  logoutHandlerBound = true;
  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-auth-logout]");
    if (!target) return;
    event.preventDefault();
    (async () => {
      const client = await getSupabaseClient();
      if (client) {
        await client.auth.signOut();
      }
      applyHeaderAuthState(null);
      applyHomeAuthState(null);
      namePromptShown = false;
      window.location.href = "/";
    })();
  });
}

document.addEventListener("partial:loaded", (event) => {
  if (event?.detail?.id !== "header") return;
  bindLogoutHandler();
  hydrateHeaderAuth().then(ensureProfileNamePrompt);
  wireAuthModal();
});

document.addEventListener("auth:signed-in", () => {
  ensureProfileNamePrompt();
  if (!window.location.pathname.endsWith("/dashboard.html")) {
    setTimeout(() => {
      window.location.href = "/dashboard.html";
    }, 0);
  }
});

// In case the header is already present (or partials fail to load from cache), attempt hydration once on load.
window.addEventListener("DOMContentLoaded", () => {
  const hasHeader = document.querySelector("header.site-header");
  if (hasHeader) {
    bindLogoutHandler();
    hydrateHeaderAuth().then(ensureProfileNamePrompt);
  }
  applyHomeAuthState(null);
  wireAuthModal();
  (async () => {
    const client = await getSupabaseClient();
    if (!client || window.__supabaseListenerBound) return;
    window.__supabaseListenerBound = true;
    client.auth.onAuthStateChange(() => {
      hydrateHeaderAuth().then(ensureProfileNamePrompt);
    });
  })();
});

window.CanIEditAuth = {
  getAccessToken: getSupabaseAccessToken,
  getUser: fetchCurrentSupabaseUser,
  getClient: getSupabaseClient,
};