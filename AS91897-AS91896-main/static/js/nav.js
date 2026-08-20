document.addEventListener("DOMContentLoaded", () => {
    const header = document.querySelector("header");
    const SCROLL_THRESHOLD = 40; // px scrolled before it goes transparent
 
    function updateHeaderState() {
        if (window.scrollY > SCROLL_THRESHOLD) {
            header.classList.add("scrolled");
        } else {
            header.classList.remove("scrolled");
        }
    }
 
    window.addEventListener("scroll", updateHeaderState);
    updateHeaderState(); // run once in case the page loads mid-scroll
});