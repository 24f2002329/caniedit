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
const AUTH_TOKEN_KEY = "caniedit:access_token"; // legacy; kept for backward compatibility

function readAuthToken() {
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY);
  } catch (error) {
    return null;
  }
}

function clearAuthToken() {
  try {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  } catch (error) {
    /* ignore */
  }
}

function resolveApiBase() {
  return (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || "https://api.caniedit.in/api";
}

async function fetchCurrentUserFromCookie() {
  try {
    const response = await fetch(`${resolveApiBase()}/auth/me`, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

async function fetchCurrentUser(token) {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  try {
    const response = await fetch(`${resolveApiBase()}/auth/me`, {
      method: "GET",
      headers,
      credentials: token ? "include" : "include",
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
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

  const userFromCookie = await fetchCurrentUserFromCookie();
  if (userFromCookie) {
    applyHeaderAuthState(userFromCookie);
    applyHomeAuthState(userFromCookie);
    return;
  }

  // Legacy fallback: if a token exists, attempt once, then clear it.
  const token = readAuthToken();
  if (token) {
    const user = await fetchCurrentUser(token);
    if (user) {
      applyHeaderAuthState(user);
      applyHomeAuthState(user);
      return;
    }
    clearAuthToken();
  }

  applyHeaderAuthState(null);
  applyHomeAuthState(null);
}

// --- Auth modal ---
const AUTH_MODAL_ID = "auth-modal";
const DEFAULT_AUTH_PROMPT = "Send a code to continue.";
const DEFAULT_LIMIT_PROMPT = "Create a free account to get 2x more merges and save history.";

let authModalBound = false;
let authModalApi = null;

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
              <span class="text-sm font-semibold text-slate-200">Name (optional)</span>
              <input id="auth-name" class="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400" type="text" name="full_name" placeholder="Jane Doe" />
            </label>
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

async function postJSON(path, body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${resolveApiBase()}${path}`, {
    method: "POST",
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
  const nameInput = document.getElementById("auth-name");

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
    const full_name = nameInput?.value.trim() || undefined;
    if (!email) {
      setAuthStatus("error", "Enter your email to get a code.");
      return;
    }
    setAuthStatus("neutral", "Sending code...");
    sendBtn.disabled = true;
    try {
      const data = await postJSON("/auth/request-otp", { email, full_name });
      setAuthStatus("success", data.code ? `Code sent (dev): ${data.code}` : "Code sent. Check your email.");
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
    const full_name = nameInput?.value.trim() || undefined;
    if (!email || !code) {
      setAuthStatus("error", "Enter your email and code.");
      return;
    }
    setAuthStatus("neutral", "Verifying...");
    verifyBtn.disabled = true;
    try {
      const data = await postJSON("/auth/verify-otp", { email, code, full_name });
      setAuthStatus("success", "Signed in. You can keep editing.");
      hydrateHeaderAuth();
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
    window.location.href = `${resolveApiBase()}/auth/google`;
  });

  const promptForLimit = (message) => open(message || DEFAULT_LIMIT_PROMPT);

  authModalApi = { open, close, promptForLimit, setStatus: setAuthStatus };
  window.authModal = authModalApi;
  window.promptAuthForLimit = promptForLimit;

  return authModalApi;
}

let logoutHandlerBound = false;
function bindLogoutHandler() {
  if (logoutHandlerBound) return;
  logoutHandlerBound = true;
  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-auth-logout]");
    if (!target) return;
    event.preventDefault();
    clearAuthToken();
    fetch(`${resolveApiBase()}/auth/logout`, {
      method: "POST",
      credentials: "include",
    }).finally(() => {
      applyHeaderAuthState(null);
      applyHomeAuthState(null);
      window.location.href = "/";
    });
  });
}

document.addEventListener("partial:loaded", (event) => {
  if (event?.detail?.id !== "header") return;
  bindLogoutHandler();
  hydrateHeaderAuth();
  wireAuthModal();
});

// In case the header is already present (or partials fail to load from cache), attempt hydration once on load.
window.addEventListener("DOMContentLoaded", () => {
  const hasHeader = document.querySelector("header.site-header");
  if (hasHeader) {
    bindLogoutHandler();
    hydrateHeaderAuth();
  }
  applyHomeAuthState(readAuthToken() ? { email: "" } : null);
  wireAuthModal();
});