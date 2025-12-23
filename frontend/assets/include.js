function initHeaderInteractions(root) {
  const dropdown = root.querySelector(".has-dropdown");
  if (!dropdown) return;

  const trigger = dropdown.querySelector(".nav-trigger");
  if (!trigger) return;

  const closeDropdown = () => {
    trigger.setAttribute("aria-expanded", "false");
    dropdown.classList.remove("is-open");
  };

  const openDropdown = () => {
    trigger.setAttribute("aria-expanded", "true");
    dropdown.classList.add("is-open");
  };

  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    if (dropdown.classList.contains("is-open")) {
      closeDropdown();
    } else {
      openDropdown();
    }
  });

  dropdown.addEventListener("mouseenter", openDropdown);
  dropdown.addEventListener("mouseleave", closeDropdown);

  dropdown.addEventListener("focusout", (event) => {
    if (!dropdown.contains(event.relatedTarget)) {
      closeDropdown();
    }
  });

  root.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeDropdown();
      trigger.focus();
    }
  });

  document.addEventListener("click", (event) => {
    if (!dropdown.contains(event.target)) {
      closeDropdown();
    }
  });
}

async function loadPartial(id, file) {
  const el = document.getElementById(id);
  if (!el) return;

  const res = await fetch(file, { cache: "no-store" });
  if (!res.ok) return;
  el.innerHTML = await res.text();

  if (id === "header") {
    initHeaderInteractions(el);
  }

  if (id === "footer") {
    const yearEl = el.querySelector("[data-year-current]");
    if (yearEl) {
      yearEl.textContent = new Date().getFullYear();
    }
  }
}

loadPartial("header", "../partials/header.html");
loadPartial("footer", "../partials/footer.html");