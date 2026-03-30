// Aplica tema imediatamente (antes do DOMContentLoaded) para evitar flash sem estilo
(function() {
  var saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

window.addEventListener('DOMContentLoaded', function() {
  var toggle = document.getElementById('toggle-theme');
  if (!toggle) return;

  var theme = localStorage.getItem('theme') || 'light';
  toggle.checked = theme === 'dark';

  toggle.addEventListener('change', function() {
    var t = toggle.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem('theme', t);
  });
});
