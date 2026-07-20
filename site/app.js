const footerMeta = document.querySelector("#footer-meta");

if (footerMeta) {
  const language = document.documentElement.lang === "en" ? "en-GB" : "de-DE";
  const prefix =
    document.documentElement.lang === "en"
      ? " Rendered locally on "
      : " Stand lokal gerendert am ";
  const today = new Intl.DateTimeFormat(language, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());

  footerMeta.textContent += `${prefix}${today}.`;
}

const galleryImages = document.querySelectorAll(".tour-visual img, .insight-card img");

if (galleryImages.length > 0) {
  const lightbox = document.createElement("div");
  lightbox.className = "lightbox";
  lightbox.hidden = true;
  lightbox.innerHTML = `
    <div class="lightbox-inner">
      <button class="lightbox-close" type="button" aria-label="Bild schliessen">×</button>
      <img class="lightbox-image" alt="">
      <p class="lightbox-caption"></p>
    </div>
  `;

  document.body.append(lightbox);

  const lightboxImage = lightbox.querySelector(".lightbox-image");
  const lightboxCaption = lightbox.querySelector(".lightbox-caption");
  const lightboxClose = lightbox.querySelector(".lightbox-close");

  const closeLightbox = () => {
    lightbox.hidden = true;
    document.body.style.overflow = "";
  };

  galleryImages.forEach((image) => {
    image.addEventListener("click", () => {
      lightboxImage.src = image.currentSrc || image.src;
      lightboxImage.alt = image.alt;
      lightboxCaption.textContent = image.alt;
      lightbox.hidden = false;
      document.body.style.overflow = "hidden";
    });
  });

  lightboxClose.addEventListener("click", closeLightbox);

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !lightbox.hidden) {
      closeLightbox();
    }
  });
}

const donationGateDisabled =
  document.body?.dataset?.disableDonationGate === "true";
const gatedDownloadLinks = donationGateDisabled
  ? []
  : document.querySelectorAll('.downloads-page a.button[href*="/download.php"]');

if (gatedDownloadLinks.length > 0) {
  const isEnglish = document.documentElement.lang === "en";
  const donationModal = document.createElement("div");
  donationModal.className = "donation-modal";
  donationModal.hidden = true;
  donationModal.innerHTML = `
    <div class="donation-modal-panel" role="dialog" aria-modal="true" aria-labelledby="donation-modal-title">
      <button class="donation-modal-close" type="button" aria-label="${
        isEnglish ? "Close dialog" : "Dialog schliessen"
      }">×</button>
      <p class="donation-modal-eyebrow">${isEnglish ? "Support" : "Unterstuetzen"}</p>
      <h3 id="donation-modal-title">${
        isEnglish
          ? "Please support free software and volunteer work."
          : "Bitte unterstuetze freie Software und ehrenamtliche Arbeit."
      }</h3>
      <p class="donation-modal-copy">${
        isEnglish
          ? "NetMon is provided free of charge, but development, maintenance, testing, and infrastructure take time. A voluntary donation helps keep the project going in the long term."
          : "NetMon wird kostenlos bereitgestellt, aber Entwicklung, Pflege, Tests und Infrastruktur kosten Zeit. Eine freiwillige Spende hilft, das Projekt langfristig weiterzufuehren."
      }</p>
      <div class="donation-modal-actions">
        <button class="button button-secondary donation-placeholder" type="button" disabled>
          PayPal (${isEnglish ? "inactive placeholder" : "Platzhalter, nicht aktiv"})
        </button>
        <button class="button button-primary donation-continue" type="button">
          ${isEnglish ? "Continue to download" : "Weiter zum Download"}
        </button>
      </div>
      <p class="donation-modal-note">${
        isEnglish
          ? "The download is still available immediately without a donation."
          : "Der Download ist auch ohne Spende sofort moeglich."
      }</p>
    </div>
  `;

  document.body.append(donationModal);

  const closeButton = donationModal.querySelector(".donation-modal-close");
  const continueButton = donationModal.querySelector(".donation-continue");
  let pendingHref = "";

  const closeDonationModal = () => {
    donationModal.hidden = true;
    document.body.style.overflow = "";
    pendingHref = "";
  };

  gatedDownloadLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      pendingHref = link.href;
      donationModal.hidden = false;
      document.body.style.overflow = "hidden";
      continueButton.focus();
    });
  });

  continueButton.addEventListener("click", () => {
    if (!pendingHref) {
      closeDonationModal();
      return;
    }
    const targetHref = pendingHref;
    closeDonationModal();
    window.location.href = targetHref;
  });

  closeButton.addEventListener("click", closeDonationModal);

  donationModal.addEventListener("click", (event) => {
    if (event.target === donationModal) {
      closeDonationModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !donationModal.hidden) {
      closeDonationModal();
    }
  });
}
