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

const partialBase = resolvePartialBase();

loadPartial("header", `${partialBase}header.html`);
loadPartial("footer", `${partialBase}footer.html`);