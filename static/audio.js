(() => {
  const button = document.querySelector('.music-toggle');
  const audio = document.getElementById('page-music');
  if (!button || !audio) return;

  const src = button.dataset.musicSrc;
  const key = 'wowdb-music-enabled';
  const enabled = localStorage.getItem(key) === 'true';

  audio.volume = 0.45;
  audio.src = src;

  function setState(isPlaying) {
    button.classList.toggle('is-playing', isPlaying);
    button.setAttribute('aria-pressed', String(isPlaying));
    const text = button.querySelector('.music-toggle-text');
    if (text) text.textContent = isPlaying ? 'Music on' : 'Music';
  }

  async function playMusic() {
    try {
      await audio.play();
      localStorage.setItem(key, 'true');
      setState(true);
    } catch {
      localStorage.setItem(key, 'false');
      setState(false);
    }
  }

  function pauseMusic() {
    audio.pause();
    localStorage.setItem(key, 'false');
    setState(false);
  }

  button.addEventListener('click', () => {
    if (audio.paused) {
      playMusic();
    } else {
      pauseMusic();
    }
  });

  if (enabled) {
    // Browser autoplay rules may still require the first click.
    playMusic();
  } else {
    setState(false);
  }
})();
