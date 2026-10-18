// Google calls this function automatically once its script has loaded
    function googleTranslateElementInit() {
        new google.translate.TranslateElement({
            pageLanguage: 'en',   // the language your site is written in
            autoDisplay: false    // stops Google showing its own banner/popup
        }, 'google_translate_element');
    }
 
    // Google remembers the chosen language in a cookie called "googtrans" (format: /en/mi)
    function getSavedLanguage() {
        const match = document.cookie.match(/googtrans=\/en\/([^;]+)/);
        return match ? match[1] : 'en';
    }
 
    function setLanguage(lang) {
        if (lang === 'en') {
            // Deleting the cookie (by giving it an expiry date in the past) switches back to English
            document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
            document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + location.hostname + ';';
        } else {
            document.cookie = 'googtrans=/en/' + lang + '; path=/;';
        }
        location.reload();   // reload so Google applies the new language to the whole page
    }
 
    const select = document.getElementById('language-select');
    select.value = getSavedLanguage();   // show the current language in the dropdown after a reload
    select.addEventListener('change', function () {
        setLanguage(this.value);
    });