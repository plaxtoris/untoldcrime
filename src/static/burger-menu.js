document.addEventListener('DOMContentLoaded', () => {
    const burgerMenu = document.getElementById('burger-menu');
    const navMenu = document.getElementById('nav-menu');
    
    if (!burgerMenu || !navMenu) return;
    
    burgerMenu.addEventListener('click', () => {
        burgerMenu.classList.toggle('active');
        navMenu.classList.toggle('active');
        
        // Update aria-label for accessibility
        const isOpen = burgerMenu.classList.contains('active');
        burgerMenu.setAttribute('aria-label', isOpen ? 'Menü schließen' : 'Menü öffnen');
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!burgerMenu.contains(e.target) && !navMenu.contains(e.target)) {
            burgerMenu.classList.remove('active');
            navMenu.classList.remove('active');
            burgerMenu.setAttribute('aria-label', 'Menü öffnen');
        }
    });
    
    // Close menu when clicking on a link
    const navLinks = navMenu.querySelectorAll('a');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            burgerMenu.classList.remove('active');
            navMenu.classList.remove('active');
            burgerMenu.setAttribute('aria-label', 'Menü öffnen');
        });
    });
});