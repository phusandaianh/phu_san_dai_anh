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
})();

