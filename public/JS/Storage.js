window.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('toggle-theme');
  const html = document.documentElement;
  if (!toggle) return;

  // Verifica o tema salvo
  const savedTheme = localStorage.getItem('theme');
  const initialTheme = savedTheme || 'light';
  html.setAttribute('data-theme', initialTheme);
  toggle.checked = initialTheme === 'dark';

  toggle.addEventListener('change', () => {
    const theme = toggle.checked ? 'dark' : 'light';
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  });
});
