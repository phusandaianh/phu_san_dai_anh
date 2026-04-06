/**
 * Thu nhỏ hiển thị toàn trang xuống ~90% (CSS zoom trên phần tử gốc).
 * Lưu ý: Không thể thiết lập mức zoom menu của trình duyệt (Ctrl +/-) bằng JS;
 * đây chỉ thu nhỏ bố cục trang. Chrome, Edge, Safari hỗ trợ tốt; Firefox từ 126+ hỗ trợ zoom.
 */
(function () {
    function applyPageZoom90() {
        if (document.getElementById('clinic-page-zoom-90-style')) return;
        var style = document.createElement('style');
        style.id = 'clinic-page-zoom-90-style';
        style.textContent = 'html { zoom: 90%; }';
        (document.head || document.documentElement).appendChild(style);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyPageZoom90);
    } else {
        applyPageZoom90();
    }
})();

// Footer Loader - Loads footer content from API and applies it to all pages
(async function() {
    try {
        const response = await fetch('/api/footer-content');
        if (!response.ok) {
            throw new Error('Failed to load footer content');
        }
        
        const footerData = await response.json();
        
        // Find all footer elements on the page
        const footerElements = document.querySelectorAll('footer.footer, footer');
        
        footerElements.forEach(footer => {
            // Apply styles
            footer.style.backgroundColor = footerData.bgColor || '#333333';
            footer.style.color = footerData.textColor || '#ffffff';
            footer.style.padding = (footerData.padding || 32) + 'px';
            footer.style.textAlign = footerData.textAlign || 'center';
            footer.style.marginTop = '3rem';
            
            // Update content if footer has a container
            const container = footer.querySelector('.container');
            if (container) {
                container.innerHTML = `<p style="margin: 0;">${footerData.text || '&copy; 2026 Phòng khám chuyên khoa Phụ Sản Đại Anh. All rights reserved.'}</p>`;
            } else {
                // If no container, update the footer directly
                footer.innerHTML = `<div class="container"><p style="margin: 0;">${footerData.text || '&copy; 2026 Phòng khám chuyên khoa Phụ Sản Đại Anh. All rights reserved.'}</p></div>`;
            }
        });
    } catch (error) {
        console.error('Error loading footer content:', error);
        // Fallback to default footer if API fails
        const footerElements = document.querySelectorAll('footer.footer, footer');
        footerElements.forEach(footer => {
            if (!footer.style.backgroundColor) {
                footer.style.backgroundColor = '#333333';
                footer.style.color = '#ffffff';
                footer.style.textAlign = 'center';
                footer.style.padding = '2rem';
                footer.style.marginTop = '3rem';
            }
        });
    }

    // ====== Clinic info loader (single source: /api/home-content contactInfo + heroTitle) ======
    function normalizeDigits(s) {
        return (s || '').toString().replace(/\D+/g, '');
    }
    function pickContactValue(items, matcher) {
        if (!Array.isArray(items)) return '';
        const found = items.find(x => matcher((x && x.type) || ''));
        return found && found.value ? String(found.value) : '';
    }
    function setTextIfExists(selector, text) {
        if (!text) return;
        const el = document.querySelector(selector);
        if (el) el.textContent = text;
    }
    function setAllTextIfExists(selector, text) {
        if (!text) return;
        document.querySelectorAll(selector).forEach(el => { el.textContent = text; });
    }
    function setHrefIfExists(selector, href) {
        if (!href) return;
        const el = document.querySelector(selector);
        if (el) el.setAttribute('href', href);
    }
    function setAllHrefIfExists(selector, href) {
        if (!href) return;
        document.querySelectorAll(selector).forEach(el => { el.setAttribute('href', href); });
    }

    try {
        const res = await fetch('/api/home-content');
        if (!res.ok) return;
        const data = await res.json();
        const contact = Array.isArray(data.contactInfo) ? data.contactInfo : [];

        const clinicName =
            pickContactValue(contact, t => /tên\s*phòng\s*khám/i.test(t)) ||
            (data && data.heroTitle ? String(data.heroTitle) : '');
        const clinicAddress = pickContactValue(contact, t => /địa\s*chỉ/i.test(t));
        const clinicPhone = pickContactValue(contact, t => /(điện\s*thoại|số\s*điện\s*thoại|hotline)/i.test(t));
        const googleMapsLink = pickContactValue(contact, t => /(google\s*maps|link\s*maps|maps)/i.test(t));

        // Update common placeholders (ids)
        setAllTextIfExists('#clinic-name', clinicName);
        setAllTextIfExists('#clinic-address', clinicAddress);
        setAllTextIfExists('#clinic-phone', clinicPhone);

        // Update tel/zalo links if present (ids)
        const phoneDigits = normalizeDigits(clinicPhone);
        if (phoneDigits) {
            setHrefIfExists('#clinic-phone-tel', 'tel:' + phoneDigits);
            setHrefIfExists('#clinic-phone-zalo', 'https://zalo.me/' + phoneDigits);
            setHrefIfExists('#clinic-phone-zalocall', 'https://zalo.me/' + phoneDigits);
        }

        // Update homepage "Địa chỉ phòng khám" button if present
        if (googleMapsLink) {
            setHrefIfExists('#home-clinic-maps-link', googleMapsLink);
        }

        // Update optional data-bind attributes (future use)
        setAllTextIfExists('[data-clinic-name]', clinicName);
        setAllTextIfExists('[data-clinic-address]', clinicAddress);
        setAllTextIfExists('[data-clinic-phone]', clinicPhone);
        if (phoneDigits) {
            setAllHrefIfExists('[data-clinic-phone-tel]', 'tel:' + phoneDigits);
            setAllHrefIfExists('[data-clinic-phone-zalo]', 'https://zalo.me/' + phoneDigits);
        }

        // Update existing booking-style subtitle element if present
        if (data && data.clinicSummary) {
            setTextIfExists('#clinic-summary', String(data.clinicSummary));
        }

        // Best-effort auto-replace legacy hardcoded strings across pages
        try {
            const legacyNames = [
                'Phòng khám chuyên khoa Phụ Sản Đại Anh',
                'Phòng khám Phụ Sản Đại Anh',
                'Phòng khám Đại Anh'
            ];
            const legacyPhones = ['0858.838.616', '0858838616'];
            const legacyAddress = 'TDP Quán Trắng - Tân An - Bắc Ninh';

            // Update document title (avoid leaving old name)
            if (clinicName && typeof document.title === 'string') {
                legacyNames.forEach(n => { document.title = document.title.split(n).join(clinicName); });
            }

            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
                acceptNode(node) {
                    if (!node || !node.parentNode) return NodeFilter.FILTER_REJECT;
                    const tag = (node.parentNode.nodeName || '').toLowerCase();
                    if (tag === 'script' || tag === 'style' || tag === 'noscript') return NodeFilter.FILTER_REJECT;
                    return NodeFilter.FILTER_ACCEPT;
                }
            });

            const nodes = [];
            let n;
            while ((n = walker.nextNode())) nodes.push(n);

            nodes.forEach(tn => {
                let v = tn.nodeValue || '';
                if (clinicName) legacyNames.forEach(old => { v = v.split(old).join(clinicName); });
                if (clinicAddress && legacyAddress) v = v.split(legacyAddress).join(clinicAddress);
                if (clinicPhone) legacyPhones.forEach(old => { v = v.split(old).join(clinicPhone); });
                if (v !== tn.nodeValue) tn.nodeValue = v;
            });
        } catch (e) {
            // ignore
        }
    } catch (e) {
        // ignore clinic info load failures
    }
})();

