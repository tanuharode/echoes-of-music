/**
 * Echoes of Music by Tanu Harode - Interactive Frontend Scripts
 * Handles mobile navigation, scroll behaviors, animations, testimonial sliders,
 * media gallery filtering, lightbox modal viewer, and dynamic booking forms.
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // ==============================================================================
    // 1. MOBILE NAVIGATION DRAWER
    // ==============================================================================
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (mobileNavToggle && navMenu) {
        mobileNavToggle.addEventListener('click', () => {
            mobileNavToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking a link
        const navLinks = navMenu.querySelectorAll('ul a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileNavToggle.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }

    // ==============================================================================
    // 2. STICKY HEADER & SCROLL BEHAVIOR
    // ==============================================================================
    const mainHeader = document.getElementById('mainHeader');
    
    const handleHeaderScroll = () => {
        if (window.scrollY > 50) {
            mainHeader.classList.add('scrolled');
        } else {
            mainHeader.classList.remove('scrolled');
        }
    };
    
    if (mainHeader) {
        window.addEventListener('scroll', handleHeaderScroll);
        handleHeaderScroll(); // Run on load
    }

    // ==============================================================================
    // 3. FADE-IN SCROLL ANIMATIONS (INTERSECTION OBSERVER)
    // ==============================================================================
    const animElements = document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right');
    
    if ('IntersectionObserver' in window && animElements.length > 0) {
        const animObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    // Stop observing once animated
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.12, // Trigger when 12% visible
            rootMargin: '0px 0px -50px 0px' // Trigger slightly before it enters screen
        });
        
        animElements.forEach(el => animObserver.observe(el));
    } else {
        // Fallback for older browsers
        animElements.forEach(el => el.classList.add('active'));
    }

    // ==============================================================================
    // 4. TESTIMONIALS CAROUSEL SLIDER
    // ==============================================================================
    const testimonialSlider = document.getElementById('testimonialSlider');
    
    if (testimonialSlider) {
        const slides = testimonialSlider.querySelectorAll('.testimonial-slide');
        const dots = document.querySelectorAll('#sliderDots .dot');
        const prevBtn = document.getElementById('prevTestimonial');
        const nextBtn = document.getElementById('nextTestimonial');
        let currentSlide = 0;
        let slideInterval;
        
        const goToSlide = (n) => {
            slides[currentSlide].classList.remove('active');
            dots[currentSlide].classList.remove('active');
            
            // Apply translation offset
            testimonialSlider.style.transform = `translateX(-${n * 100}%)`;
            
            currentSlide = (n + slides.length) % slides.length;
            slides[currentSlide].classList.add('active');
            dots[currentSlide].classList.add('active');
        };
        
        const nextSlide = () => {
            goToSlide((currentSlide + 1) % slides.length);
        };
        
        const prevSlide = () => {
            goToSlide((currentSlide - 1 + slides.length) % slides.length);
        };
        
        // Event Listeners
        if (nextBtn) nextBtn.addEventListener('click', () => { nextSlide(); resetTimer(); });
        if (prevBtn) prevBtn.addEventListener('click', () => { prevSlide(); resetTimer(); });
        
        dots.forEach(dot => {
            dot.addEventListener('click', (e) => {
                const targetIdx = parseInt(e.target.getAttribute('data-slide'));
                goToSlide(targetIdx);
                resetTimer();
            });
        });
        
        // Auto Cycle Timers
        const startTimer = () => {
            slideInterval = setInterval(nextSlide, 6000); // 6 seconds per slide
        };
        
        const resetTimer = () => {
            clearInterval(slideInterval);
            startTimer();
        };
        
        startTimer();
    }

    // ==============================================================================
    // 5. MEDIA GALLERY CATEGORY FILTERS
    // ==============================================================================
    const filterButtons = document.querySelectorAll('.filter-btn');
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    if (filterButtons.length > 0 && galleryItems.length > 0) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from other buttons
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filterValue = btn.getAttribute('data-filter');
                
                galleryItems.forEach(item => {
                    const itemCat = item.getAttribute('data-category');
                    if (filterValue === 'all' || itemCat === filterValue) {
                        item.style.display = 'block';
                        // Trigger simple visual animation trigger
                        setTimeout(() => item.style.opacity = '1', 50);
                    } else {
                        item.style.opacity = '0';
                        item.style.display = 'none';
                    }
                });
            });
        });
    }

    // ==============================================================================
    // 6. LIGHTBOX VIEWER GALLERY MODAL
    // ==============================================================================
    const lightboxModal = document.getElementById('lightboxModal');
    const lightboxImg = document.getElementById('lightboxImg');
    const lightboxTitle = document.getElementById('lightboxTitle');
    const lightboxCat = document.getElementById('lightboxCat');
    const lightboxDesc = document.getElementById('lightboxDesc');
    const lightboxClose = document.getElementById('lightboxClose');
    const lightboxPrev = document.getElementById('lightboxPrev');
    const lightboxNext = document.getElementById('lightboxNext');
    
    if (lightboxModal && galleryItems.length > 0) {
        // Collect visible images details for active navigation
        let activeItems = Array.from(galleryItems);
        let currentIndex = 0;
        
        const updateActiveItems = () => {
            // Filter only currently visible items based on current category selection
            const activeFilter = document.querySelector('.filter-btn.active')?.getAttribute('data-filter') || 'all';
            activeItems = Array.from(galleryItems).filter(item => {
                return activeFilter === 'all' || item.getAttribute('data-category') === activeFilter;
            });
        };
        
        const openLightbox = (index) => {
            updateActiveItems();
            
            // Find matched item inside visible array
            currentIndex = index;
            const targetItem = activeItems[currentIndex];
            if (!targetItem) return;
            
            const imgElement = targetItem.querySelector('img');
            const overlayTitle = targetItem.querySelector('.overlay-content h4');
            const overlayCat = targetItem.querySelector('.img-category');
            const overlayDesc = targetItem.querySelector('.img-date');
            
            lightboxImg.src = imgElement.src;
            lightboxImg.alt = imgElement.alt;
            lightboxTitle.textContent = overlayTitle.textContent;
            lightboxCat.textContent = overlayCat.textContent;
            lightboxDesc.textContent = overlayDesc.textContent;
            
            lightboxModal.classList.add('active');
            document.body.style.overflow = 'hidden'; // Stop page scrolling
        };
        
        const closeLightbox = () => {
            lightboxModal.classList.remove('active');
            document.body.style.overflow = 'auto'; // Restore scrolling
        };
        
        const navigateLightbox = (direction) => {
            if (activeItems.length <= 1) return;
            let nextIndex = currentIndex + direction;
            
            if (nextIndex >= activeItems.length) nextIndex = 0;
            if (nextIndex < 0) nextIndex = activeItems.length - 1;
            
            openLightbox(nextIndex);
        };
        
        // Add click events to gallery items
        galleryItems.forEach(item => {
            item.addEventListener('click', () => {
                updateActiveItems();
                const matchedIdx = activeItems.indexOf(item);
                if (matchedIdx !== -1) {
                    openLightbox(matchedIdx);
                }
            });
        });
        
        // Modal Events
        if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
        if (lightboxPrev) lightboxPrev.addEventListener('click', () => navigateLightbox(-1));
        if (lightboxNext) lightboxNext.addEventListener('click', () => navigateLightbox(1));
        
        // Close on clicking modal background
        lightboxModal.addEventListener('click', (e) => {
            if (e.target === lightboxModal) {
                closeLightbox();
            }
        });
        
        // Keyboard arrow controls support
        document.addEventListener('keydown', (e) => {
            if (!lightboxModal.classList.contains('active')) return;
            
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowRight') navigateLightbox(1);
            if (e.key === 'ArrowLeft') navigateLightbox(-1);
        });
    }

    // ==============================================================================
    // 7. DYNAMIC BOOKING FORM DROPDOWNS & DEFAULTS
    // ==============================================================================
    const bookingType = document.getElementById('bookingType');
    const eventName = document.getElementById('eventName');
    
    // Dropdown options dictionary
    const optionsData = {
        Class: [
            { val: "Hindustani Classical Vocal Course", label: "Hindustani Classical Vocal Course" },
            { val: "Ghazal & Voice Culture Batch", label: "Ghazal & Voice Culture (Specialized)" },
            { val: "Individual Personal Coaching", label: "1-on-1 Personalized Coaching" },
            { val: "Kids Foundation Music Class", label: "Kids Vocal Foundation Batch" }
        ],
        Show: [
            { val: "Sham-e-Ghazal", label: "Sham-e-Ghazal Evening" },
            { val: "Soft Bollywood Night", label: "Soft Bollywood Night (Retro)" },
            { val: "Light Music Evening", label: "Light Music Evening (Folk/Devotional)" }
        ]
    };
    
    const populateOptions = (category, selectedVal = null) => {
        if (!eventName) return;
        
        // Clear previous options
        eventName.innerHTML = '';
        
        if (!category || !optionsData[category]) {
            const defOpt = document.createElement('option');
            defOpt.value = "";
            defOpt.textContent = "-- Select Category First --";
            defOpt.disabled = true;
            defOpt.selected = true;
            eventName.appendChild(defOpt);
            return;
        }
        
        // Add default placeholder
        const placeholderOpt = document.createElement('option');
        placeholderOpt.value = "";
        placeholderOpt.textContent = `-- Select ${category === 'Class' ? 'Class' : 'Show'} --`;
        placeholderOpt.disabled = true;
        placeholderOpt.selected = !selectedVal;
        eventName.appendChild(placeholderOpt);
        
        // Populate options
        optionsData[category].forEach(opt => {
            const el = document.createElement('option');
            el.value = opt.val;
            el.textContent = opt.label;
            if (selectedVal && (opt.val.toLowerCase().replace(/-/g, '_') === selectedVal.toLowerCase().replace(/-/g, '_') || opt.val === selectedVal)) {
                el.selected = true;
            }
            eventName.appendChild(el);
        });
    };
    
    if (bookingType && eventName) {
        bookingType.addEventListener('change', (e) => {
            populateOptions(e.target.value);
        });
    }

    // ==============================================================================
    // 8. PARSING URL PARAMETERS (AUTO FILL BOOKINGS FROM SHOW CARDS)
    // ==============================================================================
    const parseUrlParams = () => {
        if (!bookingType || !eventName) return;
        
        const urlParams = new URLSearchParams(window.location.search);
        const typeParam = urlParams.get('type');   // 'Class' or 'Show'
        const selectParam = urlParams.get('select'); // option value
        
        if (typeParam) {
            bookingType.value = typeParam;
            populateOptions(typeParam, selectParam);
            
            // Focus on booking name to make form interactive
            const bookName = document.getElementById('bookName');
            if (bookName) {
                setTimeout(() => bookName.focus(), 800);
            }
        }
    };
    
    parseUrlParams();

    // ==============================================================================
    // 9. SELF-CLOSING FLASH TOAST NOTIFICATIONS
    // ==============================================================================
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        flashMessages.forEach(msg => {
            // Dismiss automatically after 5.5 seconds
            setTimeout(() => {
                msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                msg.style.opacity = '0';
                msg.style.transform = 'translateX(50px)';
                setTimeout(() => msg.remove(), 500);
            }, 5500);
        });
    }
});
