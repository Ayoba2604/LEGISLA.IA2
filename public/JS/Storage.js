window.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('toggle-theme');
  const html = document.documentElement;

  // Verifica o tema salvo
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    html.setAttribute('data-theme', savedTheme);
    toggle.checked = savedTheme === 'dark';
  }

  toggle.addEventListener('change', () => {
    const theme = toggle.checked ? 'dark' : 'light';
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  });
});
