const menuBtn = document.querySelector(".site-header__burger");
const siteNav = document.getElementById("site-nav");
const siteHeader = document.querySelector(".site-header");

const toggleMenu = (forceOpen) => {
  if (!menuBtn || !siteNav) return;

  const isOpen =
    typeof forceOpen === "boolean"
      ? forceOpen
      : !siteNav.classList.contains("is-open");

  siteNav.classList.toggle("is-open", isOpen);
  menuBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
};

menuBtn?.addEventListener("click", () => toggleMenu());

siteNav?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => toggleMenu(false));
});

document.addEventListener("click", (event) => {
  if (!siteNav?.classList.contains("is-open")) return;

  const target = event.target;
  if (
    target instanceof Node &&
    !siteNav.contains(target) &&
    !menuBtn?.contains(target)
  ) {
    toggleMenu(false);
  }
});

window.addEventListener("scroll", () => {
  siteHeader?.classList.toggle("is-scrolled", window.scrollY > 24);
});

const PHONE_DIGITS_LENGTH = 11;

const getPhoneDigits = (value) => {
  let digits = value.replace(/\D/g, "");

  if (digits.startsWith("8")) {
    digits = `7${digits.slice(1)}`;
  } else if (digits.length && !digits.startsWith("7")) {
    digits = `7${digits}`;
  }

  return digits.slice(0, PHONE_DIGITS_LENGTH);
};

const formatPhone = (value) => {
  const digits = getPhoneDigits(value).slice(1);

  if (!digits.length) return "+7";

  if (digits.length <= 3) {
    return `+7 (${digits}`;
  }

  if (digits.length <= 6) {
    return `+7 (${digits.slice(0, 3)}) ${digits.slice(3)}`;
  }

  if (digits.length <= 8) {
    return `+7 (${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }

  return `+7 (${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 8)}-${digits.slice(8, 10)}`;
};

const isPhoneComplete = (value) => getPhoneDigits(value).length === PHONE_DIGITS_LENGTH;

const phoneInput = document.getElementById("lead-phone");

phoneInput?.addEventListener("focus", () => {
  if (!phoneInput.value.trim()) {
    phoneInput.value = "+7";
  }
});

phoneInput?.addEventListener("blur", () => {
  if (phoneInput.value === "+7") {
    phoneInput.value = "";
  }
});

phoneInput?.addEventListener("keydown", (event) => {
  const allowedKeys = [
    "Backspace",
    "Delete",
    "ArrowLeft",
    "ArrowRight",
    "Tab",
    "Home",
    "End",
  ];

  if (allowedKeys.includes(event.key) || event.ctrlKey || event.metaKey) {
    return;
  }

  if (!/^\d$/.test(event.key)) {
    event.preventDefault();
  }
});

phoneInput?.addEventListener("input", () => {
  phoneInput.value = formatPhone(phoneInput.value);
  phoneInput.classList.remove("contact-form__input--error");
});

phoneInput?.addEventListener("paste", (event) => {
  event.preventDefault();
  const pasted = event.clipboardData?.getData("text") ?? "";
  phoneInput.value = formatPhone(pasted);
});

const SOCIAL_LABELS = {
  telegram: "Telegram",
  vk: "ВКонтакте",
};

const SOCIAL_PLACEHOLDERS = {
  telegram: "@username",
  vk: "id123456 или ник",
};

const form = document.getElementById("lead-form");
const accountInput = document.getElementById("lead-account");
const formStatus = document.getElementById("lead-form-status");
const socialRadios = form?.querySelectorAll('input[name="social_network"]');

const getSelectedSocial = () => {
  const selected = form?.querySelector('input[name="social_network"]:checked');
  return selected instanceof HTMLInputElement ? selected.value : "telegram";
};

const updateAccountPlaceholder = () => {
  if (!accountInput) return;
  const network = getSelectedSocial();
  accountInput.placeholder = SOCIAL_PLACEHOLDERS[network] ?? "";
};

socialRadios?.forEach((radio) => {
  radio.addEventListener("change", updateAccountPlaceholder);
});

updateAccountPlaceholder();

const buildLeadSummary = ({ name, phone, socialNetwork, account }) =>
  [
    `Имя: ${name}`,
    `Телефон: ${phone}`,
    `Выбранная соцсеть: ${socialNetwork}`,
    `Аккаунт: ${account}`,
  ].join("\n");

const setFormStatus = (message, type = "success") => {
  if (!formStatus) return;

  formStatus.hidden = !message;
  formStatus.textContent = message;
  formStatus.classList.remove("contact-form__status--success", "contact-form__status--error");
  formStatus.classList.add(
    type === "error" ? "contact-form__status--error" : "contact-form__status--success"
  );
};

const sendLeadToEmail = async (payload, summary, endpointEmail) => {
  const response = await fetch(`https://formsubmit.co/ajax/${endpointEmail}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      _subject: "Новая заявка SETTERS",
      _template: "box",
      name: payload.name,
      phone: payload.phone,
      social_network: payload.socialNetwork,
      account: payload.account,
      message: summary,
      summary,
    }),
  });

  if (!response.ok) {
    throw new Error("Form submit failed");
  }
};

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFormStatus("");

  const nameInput = document.getElementById("lead-name");
  const submitBtn = form.querySelector(".contact-form__submit");

  if (!phoneInput || !isPhoneComplete(phoneInput.value)) {
    phoneInput?.classList.add("contact-form__input--error");
    phoneInput?.focus();
    setFormStatus("Введите номер телефона полностью.", "error");
    return;
  }

  phoneInput.classList.remove("contact-form__input--error");

  const name = nameInput instanceof HTMLInputElement ? nameInput.value.trim() : "";
  const phone = phoneInput.value.trim();
  const networkKey = getSelectedSocial();
  const socialNetwork = SOCIAL_LABELS[networkKey] ?? networkKey;
  const account = accountInput instanceof HTMLInputElement ? accountInput.value.trim() : "";

  if (!account) {
    accountInput?.focus();
    setFormStatus("Укажите аккаунт в выбранной соцсети.", "error");
    return;
  }

  const payload = { name, phone, socialNetwork, account };
  const summary = buildLeadSummary(payload);
  const endpointEmail = form.dataset.endpointEmail ?? "hello@setters.xxx";

  if (submitBtn instanceof HTMLButtonElement) {
    submitBtn.disabled = true;
  }

  try {
    await sendLeadToEmail(payload, summary, endpointEmail);
    form.reset();
    updateAccountPlaceholder();
    setFormStatus("Заявка отправлена. Отвечу в течение рабочего дня.");
  } catch {
    setFormStatus("Не удалось отправить заявку. Напишите напрямую в Telegram.", "error");
  } finally {
    if (submitBtn instanceof HTMLButtonElement) {
      submitBtn.disabled = false;
    }
  }
});
