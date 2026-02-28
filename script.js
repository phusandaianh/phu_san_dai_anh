// Hệ thống đăng ký khám bệnh online
class AppointmentSystem {
    constructor() {
        this.appointments = [];
        this.initializeFromLocalStorage();
        this.setupEventListeners();
    }

    // Khởi tạo dữ liệu từ localStorage nếu có
    initializeFromLocalStorage() {
        const savedAppointments = localStorage.getItem('appointments');
        if (savedAppointments) {
            this.appointments = JSON.parse(savedAppointments);
        }
    }

    // Thiết lập các event listener
    setupEventListeners() {
        const appointmentForm = document.getElementById('appointmentForm');
        if (appointmentForm) {
            appointmentForm.addEventListener('submit', (e) => this.handleFormSubmission(e));
        }

        // Thiết lập validation cho các trường input
        this.setupInputValidation();
    }

    // Thiết lập validation cho các trường input
    setupInputValidation() {
        // Validation cho số điện thoại
        const phoneInput = document.getElementById('phoneNumber');
        if (phoneInput) {
            phoneInput.addEventListener('input', function() {
                const phonePattern = /^[0-9]{10,11}$/;
                if (this.value && !phonePattern.test(this.value)) {
                    this.setCustomValidity('Vui lòng nhập số điện thoại hợp lệ (10-11 số)');
                } else {
                    this.setCustomValidity('');
                }
            });
        }

        // Validation cho ngày hẹn khám
        const appointmentDateInput = document.getElementById('appointmentDate');
        if (appointmentDateInput) {
            // Set min date to today
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            const formattedToday = `${yyyy}-${mm}-${dd}`;
            
            appointmentDateInput.setAttribute('min', formattedToday);
            
            // Disable Sundays
            appointmentDateInput.addEventListener('input', function() {
                const selectedDate = new Date(this.value);
                if (selectedDate.getDay() === 0) { // 0 is Sunday
                    this.setCustomValidity('Chủ nhật phòng khám không làm việc. Vui lòng chọn ngày khác.');
                } else {
                    this.setCustomValidity('');
                }
            });
        }

        // Validation cho email nếu được nhập
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.addEventListener('input', function() {
                if (this.value) {
                    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailPattern.test(this.value)) {
                        this.setCustomValidity('Vui lòng nhập địa chỉ email hợp lệ');
                    } else {
                        this.setCustomValidity('');
                    }
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    }

    // Xử lý khi form được submit
    handleFormSubmission(e) {
        e.preventDefault();
        
        // Lấy dữ liệu từ form
        const formData = new FormData(e.target);
        const appointmentData = {
            id: Date.now(), // Tạo ID duy nhất dựa trên timestamp
            fullName: formData.get('fullName'),
            phoneNumber: formData.get('phoneNumber'),
            email: formData.get('email') || '',
            dob: formData.get('dob'),
            address: formData.get('address') || '',
            appointmentDate: formData.get('appointmentDate'),
            appointmentTime: formData.get('appointmentTime'),
            service: formData.get('service'),
            symptoms: formData.get('symptoms') || '',
            status: 'pending', // Trạng thái mặc định: chờ xác nhận
            createdAt: new Date().toISOString()
        };
        
        // Kiểm tra xem đã có lịch hẹn vào thời gian này chưa
        if (this.isTimeSlotAvailable(appointmentData.appointmentDate, appointmentData.appointmentTime)) {
            // Thêm lịch hẹn mới
            this.appointments.push(appointmentData);
            
            // Lưu vào localStorage
            this.saveToLocalStorage();
            
            // Hiển thị thông báo thành công
            this.showSuccessModal(appointmentData);
            
            // Gửi thông báo qua Zalo (mô phỏng)
            this.sendZaloNotification(appointmentData);
            
            // Reset form
            e.target.reset();
        } else {
            alert('Thời gian này đã có lịch hẹn. Vui lòng chọn thời gian khác!');
        }
    }

    // Kiểm tra xem thời gian đã có lịch hẹn chưa
    isTimeSlotAvailable(date, time) {
        // Trong thực tế, cần kiểm tra với dữ liệu từ server
        // Đây chỉ là mô phỏng kiểm tra với dữ liệu localStorage
        const existingAppointment = this.appointments.find(
            app => app.appointmentDate === date && app.appointmentTime === time
        );
        
        // Giả sử mỗi khung giờ chỉ nhận tối đa 3 lịch hẹn
        const countSameTimeSlot = this.appointments.filter(
            app => app.appointmentDate === date && app.appointmentTime === time
        ).length;
        
        return countSameTimeSlot < 3;
    }

    // Lưu dữ liệu vào localStorage
    saveToLocalStorage() {
        localStorage.setItem('appointments', JSON.stringify(this.appointments));
    }

    // Hiển thị modal thông báo thành công
    showSuccessModal(appointmentData) {
        const successModal = document.getElementById('successModal');
        if (successModal) {
            // Cập nhật nội dung modal nếu cần
            const modalContent = successModal.querySelector('.modal-content');
            if (modalContent) {
                const appointmentInfo = document.createElement('div');
                appointmentInfo.classList.add('appointment-details');
                appointmentInfo.innerHTML = `
                    <p><strong>Họ tên:</strong> ${appointmentData.fullName}</p>
                    <p><strong>Ngày hẹn:</strong> ${this.formatDate(appointmentData.appointmentDate)}</p>
                    <p><strong>Giờ hẹn:</strong> ${appointmentData.appointmentTime}</p>
                    <p><strong>Dịch vụ:</strong> ${this.getServiceName(appointmentData.service)}</p>
                `;
                
                // Thêm thông tin lịch hẹn vào modal
                const existingDetails = modalContent.querySelector('.appointment-details');
                if (existingDetails) {
                    modalContent.replaceChild(appointmentInfo, existingDetails);
                } else {
                    // Thêm sau thẻ p cuối cùng
                    const lastP = modalContent.querySelector('p:last-of-type');
                    if (lastP) {
                        lastP.after(appointmentInfo);
                    }
                }
            }
            
            // Hiển thị modal
            successModal.style.display = 'flex';
        }
    }

    // Gửi thông báo qua Zalo (mô phỏng)
    sendZaloNotification(appointmentData) {
        console.log('Gửi thông báo Zalo đến số 0858838616 với thông tin:');
        console.log(`Lịch hẹn mới: ${appointmentData.fullName}, ${this.formatDate(appointmentData.appointmentDate)}, ${appointmentData.appointmentTime}, ${this.getServiceName(appointmentData.service)}`);
        
        // Trong thực tế, cần tích hợp API của Zalo để gửi thông báo
    }

    // Format lại ngày tháng
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    }

    // Lấy tên dịch vụ từ value
    getServiceName(serviceValue) {
        const serviceMap = {
            'kham-phu-khoa': 'Khám phụ khoa',
            'kham-thai': 'Khám thai',
            'sieu-am': 'Siêu âm',
            'sieu-am-5d': 'Siêu âm dị tật thai 5D',
            'tu-van': 'Tư vấn sức khỏe sinh sản'
        };
        
        return serviceMap[serviceValue] || serviceValue;
    }
}

// Khởi tạo hệ thống đặt lịch khi trang được tải
document.addEventListener('DOMContentLoaded', () => {
    const appointmentButton = document.querySelector('.btn.primary-btn[href="#appointment-form"]');
    const appointmentFormSection = document.querySelector('#appointment-form');

    if (appointmentButton && appointmentFormSection) {
        appointmentButton.addEventListener('click', (event) => {
            event.preventDefault();
            appointmentFormSection.scrollIntoView({ behavior: 'smooth' });
            appointmentFormSection.classList.add('highlight');

            setTimeout(() => {
                appointmentFormSection.classList.remove('highlight');
            }, 2000); // Remove highlight after 2 seconds
        });
    }
});

// Function to handle appointment booking
async function bookAppointment(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('patient-name').value,
        phone: document.getElementById('patient-phone').value,
        address: document.getElementById('patient-address').value,
        reason: document.getElementById('patient-reason').value,
        appointment_time: document.getElementById('appointment-time').value,
        // Có thể bổ sung thêm các trường ngày, bác sĩ nếu cần
    };

    try {
        const response = await fetch('/api/appointments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (response.ok) {
            alert('Đặt lịch thành công!');
            // Redirect to appointment details page
            window.location.href = `/appointment-details.html?id=${data.appointment_id}`;
        } else {
            throw new Error(data.message || 'Có lỗi xảy ra');
        }
    } catch (error) {
        alert(error.message);
    }
}

// Function to load available services
async function loadServices() {
    try {
        const response = await fetch('/api/services');
        const services = await response.json();
        
        const serviceSelect = document.getElementById('service-type');
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.name} - ${service.price.toLocaleString('vi-VN')}đ`;
            serviceSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

// Function to print prescription
async function printPrescription(appointmentId) {
    try {
        const response = await fetch(`/api/print_prescription/${appointmentId}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `prescription_${appointmentId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            throw new Error('Không thể in đơn thuốc');
        }
    } catch (error) {
        alert(error.message);
    }
}

// Function to print ultrasound result
async function printUltrasound(appointmentId) {
    try {
        const response = await fetch(`/api/print_ultrasound/${appointmentId}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ultrasound_${appointmentId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            throw new Error('Không thể in kết quả siêu âm');
        }
    } catch (error) {
        alert(error.message);
    }
}

// Function to calculate total bill
function calculateBill(services) {
    let total = 0;
    services.forEach(service => {
        total += service.price;
    });
    return total;
}

// Function to handle payment
async function processPayment(appointmentId, amount) {
    try {
        const response = await fetch('/api/payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                appointment_id: appointmentId,
                amount: amount
            })
        });

        if (response.ok) {
            alert('Thanh toán thành công!');
            // Update UI to show payment status
            document.getElementById('payment-status').textContent = 'Đã thanh toán';
        } else {
            throw new Error('Thanh toán thất bại');
        }
    } catch (error) {
        alert(error.message);
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Load services when the page loads
    loadServices();
    
    // Add event listeners
    const appointmentForm = document.getElementById('appointment-form');
    if (appointmentForm) {
        appointmentForm.addEventListener('submit', bookAppointment);
    }
    
    // Add event listeners for print buttons
    const printPrescriptionBtn = document.getElementById('print-prescription');
    if (printPrescriptionBtn) {
        printPrescriptionBtn.addEventListener('click', () => {
            const appointmentId = printPrescriptionBtn.dataset.appointmentId;
            printPrescription(appointmentId);
        });
    }
    
    const printUltrasoundBtn = document.getElementById('print-ultrasound');
    if (printUltrasoundBtn) {
        printUltrasoundBtn.addEventListener('click', () => {
            const appointmentId = printUltrasoundBtn.dataset.appointmentId;
            printUltrasound(appointmentId);
        });
    }
});
