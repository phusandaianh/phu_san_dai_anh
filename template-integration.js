/**
 * Template Integration JavaScript
 * Hỗ trợ tích hợp template vào hệ thống hiện tại
 */

class LabTemplateManager {
    constructor() {
        this.templates = {
            'lab-result': {
                name: 'Phiếu Kết Quả Cận Lâm Sàng',
                css: 'lab-result-template.css',
                template: 'improved-lab-result-template.html'
            },
            'lab-request': {
                name: 'Phiếu Chỉ Định Cận Lâm Sàng', 
                css: 'lab-request-template.css',
                template: 'improved-lab-request-template.html'
            }
        };
        this.currentTemplate = null;
        this.data = {};
    }

    /**
     * Khởi tạo template
     */
    init(templateType) {
        if (!this.templates[templateType]) {
            throw new Error(`Template type ${templateType} not found`);
        }
        
        this.currentTemplate = templateType;
        this.loadTemplate();
        this.bindEvents();
    }

    /**
     * Load template vào DOM
     */
    loadTemplate() {
        const template = this.templates[this.currentTemplate];
        
        // Load CSS
        this.loadCSS(template.css);
        
        // Load HTML template
        this.loadHTML(template.template);
    }

    /**
     * Load CSS file
     */
    loadCSS(cssFile) {
        if (document.querySelector(`link[href="${cssFile}"]`)) {
            return; // Already loaded
        }
        
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = cssFile;
        document.head.appendChild(link);
    }

    /**
     * Load HTML template
     */
    async loadHTML(templateFile) {
        try {
            const response = await fetch(templateFile);
            const html = await response.text();
            
            // Extract body content
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const bodyContent = doc.body.innerHTML;
            
            // Insert into container
            const container = document.getElementById('template-container') || document.body;
            container.innerHTML = bodyContent;
            
        } catch (error) {
            console.error('Error loading template:', error);
        }
    }

    /**
     * Bind events
     */
    bindEvents() {
        // Auto-save on input
        document.addEventListener('input', (e) => {
            if (e.target.hasAttribute('data-field')) {
                this.saveField(e.target);
            }
        });

        // Print functionality
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('print-btn')) {
                this.printTemplate();
            }
        });
    }

    /**
     * Save field data
     */
    saveField(element) {
        const field = element.getAttribute('data-field');
        let value;
        
        if (element.type === 'checkbox') {
            value = element.checked;
        } else if (element.contentEditable === 'true') {
            value = element.textContent;
        } else {
            value = element.value;
        }
        
        this.data[field] = value;
        this.saveToStorage();
    }

    /**
     * Load data from storage
     */
    loadData() {
        const saved = localStorage.getItem(`lab_template_${this.currentTemplate}`);
        if (saved) {
            this.data = JSON.parse(saved);
            this.populateFields();
        }
    }

    /**
     * Populate fields with data
     */
    populateFields() {
        Object.keys(this.data).forEach(field => {
            const element = document.querySelector(`[data-field="${field}"]`);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = this.data[field];
                } else if (element.contentEditable === 'true') {
                    element.textContent = this.data[field];
                } else {
                    element.value = this.data[field];
                }
            }
        });
    }

    /**
     * Save to localStorage
     */
    saveToStorage() {
        localStorage.setItem(`lab_template_${this.currentTemplate}`, JSON.stringify(this.data));
    }

    /**
     * Clear all data
     */
    clearData() {
        this.data = {};
        this.saveToStorage();
        
        // Clear form fields
        document.querySelectorAll('[data-field]').forEach(el => {
            if (el.type === 'checkbox') {
                el.checked = false;
            } else if (el.contentEditable === 'true') {
                el.textContent = '';
            } else {
                el.value = '';
            }
        });
    }

    /**
     * Fill with sample data
     */
    fillSampleData() {
        const sampleData = this.getSampleData();
        Object.keys(sampleData).forEach(field => {
            this.data[field] = sampleData[field];
        });
        this.populateFields();
        this.saveToStorage();
    }

    /**
     * Get sample data based on template type
     */
    getSampleData() {
        if (this.currentTemplate === 'lab-result') {
            return {
                patient_name: 'Nguyễn Thị Minh Anh',
                patient_age: '28',
                patient_address: '123 Đường ABC, Quận 1, TP.HCM',
                patient_phone: '0901234567',
                patient_dob: '15/03/1995',
                diagnosis: 'Khám phụ khoa định kỳ - Nghi ngờ rối loạn kinh nguyệt',
                ultrasound_result: 'Tử cung kích thước bình thường, niêm mạc tử cung dày 8mm',
                ultrasound_note: 'Không có khối u, không có dịch ổ bụng',
                blood_test_result: 'Hb: 12.5 g/dL, Hct: 37.5%, WBC: 6.2 x 10³/μL',
                blood_test_note: 'Tất cả chỉ số trong giới hạn bình thường',
                urine_test_result: 'Protein: (-), Glucose: (-), Ketone: (-)',
                urine_test_note: 'Không có bất thường',
                doctor_name: 'BS. Nguyễn Văn A',
                test_date: '15/01/2024'
            };
        } else if (this.currentTemplate === 'lab-request') {
            return {
                patient_name: 'Nguyễn Thị Minh Anh',
                patient_age: '28',
                patient_address: '123 Đường ABC, Quận 1, TP.HCM',
                patient_phone: '0901234567',
                patient_dob: '15/03/1995',
                diagnosis: 'Khám phụ khoa định kỳ\nNghi ngờ rối loạn kinh nguyệt',
                ultrasound_pelvis: true,
                blood_test: true,
                urine_test: true,
                doctor_name: 'BS. Nguyễn Văn A',
                request_date: '15/01/2024'
            };
        }
        return {};
    }

    /**
     * Print template
     */
    printTemplate() {
        // Hide demo controls
        document.querySelectorAll('.no-print').forEach(el => {
            el.style.display = 'none';
        });
        
        // Print
        window.print();
        
        // Show demo controls again
        setTimeout(() => {
            document.querySelectorAll('.no-print').forEach(el => {
                el.style.display = '';
            });
        }, 1000);
    }

    /**
     * Export data as JSON
     */
    exportData() {
        const dataStr = JSON.stringify(this.data, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `lab_template_${this.currentTemplate}_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
    }

    /**
     * Import data from JSON
     */
    importData(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                this.data = JSON.parse(e.target.result);
                this.populateFields();
                this.saveToStorage();
            } catch (error) {
                alert('Lỗi đọc file JSON: ' + error.message);
            }
        };
        reader.readAsText(file);
    }

    /**
     * Get current data
     */
    getData() {
        return this.data;
    }

    /**
     * Set data
     */
    setData(data) {
        this.data = data;
        this.populateFields();
        this.saveToStorage();
    }
}

// Global instance
window.labTemplateManager = new LabTemplateManager();

// Auto-initialize if template type is specified in URL
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const templateType = urlParams.get('template');
    
    if (templateType && window.labTemplateManager.templates[templateType]) {
        window.labTemplateManager.init(templateType);
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LabTemplateManager;
}
