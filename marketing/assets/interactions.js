(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const root = document.documentElement;
  const body = document.body;

  body.classList.add("motion-ready");

  const progress = document.createElement("div");
  progress.className = "k-scroll-progress";
  body.appendChild(progress);

  const updateProgress = () => {
    const max = root.scrollHeight - window.innerHeight;
    const ratio = max > 0 ? window.scrollY / max : 0;
    progress.style.transform = `scaleX(${Math.min(1, Math.max(0, ratio))})`;
  };

  updateProgress();
  window.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);

  const revealItems = document.querySelectorAll(".k-sect, footer, .k-hero-grid > div");
  revealItems.forEach((el) => el.classList.add("k-reveal"));

  if (reduceMotion) {
    revealItems.forEach((el) => el.classList.add("k-visible"));
  } else {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("k-visible");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    revealItems.forEach((el) => revealObserver.observe(el));
  }

  const interactiveSelectors = [
    ".k-steps > div",
    ".k-three > div",
    ".k-benefits > div",
    ".k-metrics > div",
    ".k-ba > div",
    ".k-two > div"
  ];

  const cards = [...document.querySelectorAll(interactiveSelectors.join(","))]
    .filter((el) => el.getBoundingClientRect().width > 80);

  cards.forEach((card) => {
    card.classList.add("k-interactive");
    if (reduceMotion) return;

    if (card.dataset.softCard === "true") {
      card.addEventListener("pointerenter", () => card.classList.add("is-active"));
      card.addEventListener("pointerleave", () => card.classList.remove("is-active"));
      return;
    }

    card.addEventListener("pointermove", (event) => {
      const rect = card.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width;
      const y = (event.clientY - rect.top) / rect.height;
      const tiltX = (x - 0.5) * 7;
      const tiltY = (0.5 - y) * 7;

      card.style.setProperty("--tilt-x", `${tiltX.toFixed(2)}deg`);
      card.style.setProperty("--tilt-y", `${tiltY.toFixed(2)}deg`);
      card.style.setProperty("--mx", `${(x * 100).toFixed(1)}%`);
      card.style.setProperty("--my", `${(y * 100).toFixed(1)}%`);
      card.classList.add("is-active");
    });

    card.addEventListener("pointerleave", () => {
      card.style.setProperty("--tilt-x", "0deg");
      card.style.setProperty("--tilt-y", "0deg");
      card.style.setProperty("--mx", "50%");
      card.style.setProperty("--my", "50%");
      card.classList.remove("is-active");
    });
  });

  document.querySelectorAll("a[href]").forEach((link) => {
    link.classList.add("k-action");
  });

  document.querySelectorAll('img[src*="komite-logo"]').forEach((img) => {
    const frame = img.parentElement;
    if (frame) frame.classList.add("k-logo-soft");
  });

  const metricValues = document.querySelectorAll(".k-metrics > div > div:first-child");
  const animateMetric = (el) => {
    if (el.dataset.animated === "true") return;
    el.dataset.animated = "true";
    el.classList.add("k-pulse");

    const finalText = el.textContent.trim();
    const match = finalText.match(/^(-?\d+)(%)?$/);
    if (!match || reduceMotion) return;

    const target = Number(match[1]);
    const suffix = match[2] || "";
    const start = performance.now();
    const duration = 950;

    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = `${Math.round(target * eased)}${suffix}`;
      if (progress < 1) requestAnimationFrame(tick);
      else el.textContent = finalText;
    };

    requestAnimationFrame(tick);
  };

  if (metricValues.length) {
    const metricObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) animateMetric(entry.target);
        });
      },
      { threshold: 0.55 }
    );
    metricValues.forEach((metric) => metricObserver.observe(metric));
  }

  const contactForm = document.querySelector("#formulario-contacto");
  if (contactForm) {
    const status = contactForm.querySelector(".k-form-status");
    contactForm.addEventListener("submit", (event) => {
      event.preventDefault();

      if (!contactForm.reportValidity()) return;

      const data = new FormData(contactForm);
      const recipient = contactForm.dataset.contactEmail || "contacto.komite@gmail.com";
      const lines = [
        "Hola, quiero agendar una demo de Komite.",
        "",
        `Nombre: ${data.get("nombre") || ""}`,
        `Email: ${data.get("email") || ""}`,
        `Telefono: ${data.get("telefono") || ""}`,
        `Administradora: ${data.get("administradora") || ""}`,
        `Condominios: ${data.get("condominios") || ""}`,
        `Cargo: ${data.get("cargo") || ""}`,
        "",
        "Mensaje:",
        data.get("mensaje") || ""
      ];
      const subject = encodeURIComponent("Solicitud de demo Komite");
      const body = encodeURIComponent(lines.join("\n"));

      if (status) status.textContent = "Abriendo tu cliente de correo...";
      window.location.href = `mailto:${recipient}?subject=${subject}&body=${body}`;
    });
  }
})();
