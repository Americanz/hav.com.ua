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
  document.querySelectorAll(".logo").forEach((node) => {
    node.textContent = site.brand || "HAV";
  });
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

function serviceCard(item) {
  const card = item.href ? link(item.href, "service reveal") : el("article", "service reveal");
  card.append(
    el("div", item.href ? "service-icon mark" : "service-icon", item.icon || ""),
    el("h3", null, item.title),
    el("p", null, item.text),
  );
  if (item.href) card.append(el("span", "more", "Детальніше →"));
  return card;
}

function applyShared(site) {
  document.querySelectorAll(".logo").forEach((node) => {
    node.textContent = site.brand || "HAV";
  });
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
