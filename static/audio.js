(function () {
  const STORAGE_ENABLED = "wowDatabaseMusicEnabled";
  const STORAGE_VOLUME = "wowDatabaseMusicVolume";
  const DEFAULT_VOLUME = 0.6;
  const EXTENSIONS = ["mp3", "ogg", "wav", "m4a"];

  const body = document.body;
  const musicKey = body?.dataset?.musicKey || "homepage";
  const enabledInput = document.getElementById("music-enabled");
  const volumeInput = document.getElementById("music-volume");
  const volumeValue = document.getElementById("music-volume-value");

  let enabled = localStorage.getItem(STORAGE_ENABLED);
  if (enabled === null) {
    enabled = "true";
    localStorage.setItem(STORAGE_ENABLED, enabled);
  }

  let volume = Number(localStorage.getItem(STORAGE_VOLUME));
  if (!Number.isFinite(volume)) {
    volume = DEFAULT_VOLUME;
    localStorage.setItem(STORAGE_VOLUME, String(volume));
  }
  volume = Math.max(0, Math.min(1, volume));

  let extIndex = 0;
  const audio = new Audio();
  audio.loop = true;
  audio.preload = "auto";
  audio.volume = volume;

  function sourceForCurrentExtension() {
    return `/music/${musicKey}.${EXTENSIONS[extIndex]}`;
  }

  function setSource() {
    audio.src = sourceForCurrentExtension();
    audio.currentTime = 0;
  }

  function isEnabled() {
    return localStorage.getItem(STORAGE_ENABLED) !== "false";
  }

  function setEnabled(nextEnabled) {
    localStorage.setItem(STORAGE_ENABLED, nextEnabled ? "true" : "false");
    if (enabledInput) enabledInput.checked = nextEnabled;
    if (nextEnabled) {
      playFromStart();
    } else {
      audio.pause();
    }
  }

  function setVolume(nextVolume) {
    volume = Math.max(0, Math.min(1, nextVolume));
    audio.volume = volume;
    localStorage.setItem(STORAGE_VOLUME, String(volume));
    if (volumeInput) volumeInput.value = String(Math.round(volume * 100));
    if (volumeValue) volumeValue.textContent = `${Math.round(volume * 100)}%`;
  }

  function playFromStart() {
    if (!isEnabled()) return;
    if (!audio.src) setSource();
    audio.currentTime = 0;
    audio.play().catch(() => {
      // Browsers often block autoplay until the first user interaction.
    });
  }

  audio.addEventListener("error", () => {
    extIndex += 1;
    if (extIndex >= EXTENSIONS.length) {
      audio.pause();
      return;
    }
    setSource();
    if (isEnabled()) {
      audio.play().catch(() => {});
    }
  });

  if (enabledInput) {
    enabledInput.checked = isEnabled();
    enabledInput.addEventListener("change", () => setEnabled(enabledInput.checked));
  }

  if (volumeInput) {
    volumeInput.value = String(Math.round(volume * 100));
    if (volumeValue) volumeValue.textContent = `${Math.round(volume * 100)}%`;
    volumeInput.addEventListener("input", () => setVolume(Number(volumeInput.value) / 100));
  }

  setSource();
  setVolume(volume);

  if (isEnabled()) {
    playFromStart();
  }

  // One click anywhere can unlock audio after browser autoplay blocking.
  document.addEventListener(
    "pointerdown",
    () => {
      if (isEnabled() && audio.paused) {
        audio.play().catch(() => {});
      }
    },
    { once: true }
  );
})();
