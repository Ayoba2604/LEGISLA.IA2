document.addEventListener('DOMContentLoaded', function () {
    const themeDetails = document.getElementById('theme-details');
    const menu = document.getElementById('theme-menu');
    const toggle = document.getElementById('toggle-theme');
    const options = document.querySelectorAll('.theme-option');

    if (!themeDetails || !menu || !toggle || options.length === 0) return;

    function syncActiveOption() {
        options.forEach((opt) => {
            const isDark = opt.dataset.theme === 'dark';
            const active = isDark ? toggle.checked : !toggle.checked;
            opt.classList.toggle('active', active);
        });
    }

    function closeMenu() {
        themeDetails.open = false;
    }

    options.forEach((opt) => {
        opt.addEventListener('click', function () {
            toggle.checked = opt.dataset.theme === 'dark';
            toggle.dispatchEvent(new Event('change', { bubbles: true }));
            syncActiveOption();
            closeMenu();
        });
    });

    document.addEventListener('click', function (e) {
        if (!themeDetails.contains(e.target)) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeMenu();
        }
    });

    syncActiveOption();
});
