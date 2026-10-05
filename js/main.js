document.documentElement.classList.add("js");

const FALLBACK_EMAIL = "hello@hav.com.ua";

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node && value != null) node.textContent = value;
}

function link(href, className, text) {
  const node = el("a", className, text);
  node.href = href;
  if (/^https?:\/\//.test(href)) {
    node.target = "_blank";
    node.rel = "noopener noreferrer";
  }
  return node;
}

function render(site) {
  setText("footerTagline", site.tagline);

  const hero = site.hero || {};
  setText("heroBadge", hero.badge);
  const title = document.getElementById("heroTitle");
  title.replaceChildren();
  title.append(
    document.createTextNode(hero.titleBefore || ""),
    el("span", null, hero.titleAccent || ""),
    document.createTextNode(hero.titleAfter || ""),
  );
  setText("heroLead", hero.lead);

  const cta = document.getElementById("heroCta");
  cta.replaceChildren(
    link("#contact", "btn btn-primary", hero.primaryCta || "Отримати консультацію"),
    link("#services", "btn btn-ghost", hero.secondaryCta || "Наші послуги"),
  );

  const stats = document.getElementById("stats");
  stats.replaceChildren();
  (site.stats || []).forEach((item) => {
    const card = el("div", "stat reveal");
    card.append(el("b", null, item.value), el("span", null, item.label));
    stats.append(card);
  });

  fillSection("services", site.services, (item) => serviceCard(item));
  fillSection("systems", site.systems, (item) => serviceCard(item));

  const techCopy = site.tech || {};
  setText("techTag", techCopy.tag);
  setText("techTitle", techCopy.title);
  setText("techSub", techCopy.subtitle);
  const techGrid = document.getElementById("techGrid");
  techGrid.replaceChildren();
  (techCopy.items || []).forEach((name) => techGrid.append(el("span", "tech", name)));

  fillSection("process", site.process, (item) => {
    const card = el("article", "step reveal");
    card.append(el("h4", null, item.title), el("p", null, item.text));
    return card;
  });

  fillSection("cases", site.cases, (item) => {
    const card = el("article", "case reveal");
    card.append(
      el("span", "case-tag", item.tag),
      el("h3", null, item.title),
      el("p", null, item.text),
      el("div", "case-result", item.result),
    );
    return card;
  });

  const contact = site.contact || {};
  setText("contactTag", contact.tag);
  setText("contactTitle", contact.title);
  setText("contactSub", contact.subtitle);
  applyShared(site);
}

const ICONS = {
  cloud: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 18h10a4 4 0 0 0 .2-8 6 6 0 0 0-11.6-1.6A3.5 3.5 0 0 0 7 18z"/></svg>',
  cicd: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h12"/><path d="M13 4l3 3-3 3"/><path d="M20 17H8"/><path d="M11 14l-3 3 3 3"/></svg>',
  kubernetes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7.5 4.3v9.4L12 21l-7.5-4.3V7.3z"/><circle cx="12" cy="12" r="2.2"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v6c0 4.2-2.8 7.2-7 9-4.2-1.8-7-4.8-7-9V6z"/></svg>',
  chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 16v-4"/><path d="M12 16V8"/><path d="M16 16v-6"/></svg>',
  rocket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19c1.5-1.2 4-4.2 4-8.2C16 6.5 14.2 3.5 12 2c-2.2 1.5-4 4.5-4 8.8 0 4 2.5 7 4 8.2z"/><path d="M9 14.5C7.2 15.2 5.5 15 4 14c.6 2.2 2.2 3.6 4.2 4"/><path d="M15 14.5c1.8.7 3.5.5 5-.5-.6 2.2-2.2 3.6-4.2 4"/></svg>',
};

function serviceIcon(name) {
  const node = document.createElement("div");
  if (ICONS[name]) {
    node.className = "service-icon";
    node.innerHTML = ICONS[name];
    return node;
  }
  node.className = "service-icon mark";
  node.textContent = name || "";
  return node;
}

function serviceCard(item) {
  const card = item.href ? link(item.href, "service reveal") : el("article", "service reveal");
  card.append(
    serviceIcon(item.icon),
    el("h3", null, item.title),
    el("p", null, item.text),
  );
  if (item.href) card.append(el("span", "more", "Детальніше →"));
  return card;
}

function applyShared(site) {
  setText("footerTagline", site.tagline);
  const submit = document.getElementById("submitBtn");
  const submitLabel = (site.contact || {}).submit;
  if (submit && submitLabel) submit.textContent = submitLabel;

  const contacts = document.getElementById("footerContacts");
  if (!contacts) return;
  contacts.replaceChildren();
  ((site.footer || {}).contacts || []).forEach((item) => {
    const li = el("li");
    li.append(link(item.href, null, item.label));
    contacts.append(li);
  });
  const year = new Date().getFullYear();
  setText("copyright", `© ${year} ${(site.footer || {}).copyright || ""}`.trim());
  setText("footerSite", (site.footer || {}).site || "");
}

function fillSection(name, block, makeCard) {
  const data = block || {};
  setText(`${name}Tag`, data.tag);
  setText(`${name}Title`, data.title);
  setText(`${name}Sub`, data.subtitle);
  const grid = document.getElementById(`${name}Grid`);
  grid.replaceChildren();
  (data.items || []).forEach((item) => grid.append(makeCard(item)));
}

function armReveal() {
  const nodes = document.querySelectorAll(".reveal");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) {
    nodes.forEach((node) => node.classList.add("visible"));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.15 });
  nodes.forEach((node) => {
    if (node.getBoundingClientRect().top < window.innerHeight * 0.92) {
      node.classList.add("visible");
    } else {
      observer.observe(node);
    }
  });
}

function initChrome() {
  const header = document.getElementById("header");
  const syncHeader = () => header.classList.toggle("scrolled", window.scrollY > 40);
  syncHeader();
  window.addEventListener("scroll", syncHeader, { passive: true });

  const burger = document.getElementById("burger");
  const navLinks = document.getElementById("navLinks");
  const closeMenu = () => {
    navLinks.classList.remove("open");
    burger.setAttribute("aria-expanded", "false");
  };
  burger.addEventListener("click", () => {
    const open = navLinks.classList.toggle("open");
    burger.setAttribute("aria-expanded", open ? "true" : "false");
  });
  navLinks.querySelectorAll("a").forEach((anchor) => anchor.addEventListener("click", closeMenu));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });
  armReveal();
}

function initForm(site) {
  const form = document.getElementById("contactForm");
  if (!form) return;
  const status = document.getElementById("formStatus");
  const button = document.getElementById("submitBtn");
  const contact = site.contact || {};

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    button.disabled = true;
    status.className = "form-status";
    status.textContent = contact.sending || "Надсилаємо…";
    const fallback = contact.error || `Не вдалося надіслати заявку. Напишіть на ${FALLBACK_EMAIL}`;
    try {
      const response = await fetch("/api/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(data),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload.ok) {
        status.className = "form-status err";
        status.textContent = payload.error || fallback;
        return;
      }
      form.reset();
      status.className = "form-status ok";
      status.textContent = contact.success || "Дякуємо. Заявку надіслано.";
    } catch {
      status.className = "form-status err";
      status.textContent = fallback;
    } finally {
      button.disabled = false;
    }
  });
}

async function boot() {
  const home = document.body.dataset.page === "home";
  try {
    const response = await fetch("/content.json", { headers: { "Accept": "application/json" } });
    if (!response.ok) throw new Error("content");
    const site = await response.json();
    if (home) render(site);
    else applyShared(site);
    initChrome();
    initForm(site);
  } catch (error) {
    if (home) {
      const lead = document.getElementById("heroLead");
      if (lead) {
        lead.textContent = `Не вдалося завантажити сторінку. Оновіть її або напишіть на ${FALLBACK_EMAIL}`;
      }
    }
    initChrome();
    initForm({});
  } finally {
    document.documentElement.classList.remove("booting");
  }
}

boot();
