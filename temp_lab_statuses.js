    const state = { month: '', provider: '', q: '' };
    window.LAB_STATUSES = ["Chờ kết quả", "Đã nghe, thiếu kết quả", "Đã nghe", "Không liên lạc được", "Nhắn tin"];

    function renderStatusOptions() {
        const container = document.getElementById('status-options-list');
        if (!window.LAB_STATUSES || !Array.isArray(window.LAB_STATUSES)) {
            window.LAB_STATUSES = ["Chờ kết quả", "Đã nghe, thiếu kết quả", "Đã nghe", "Không liên lạc được", "Nhắn tin"];
        }
        
        container.innerHTML = window.LAB_STATUSES.map((status, index) => `
            <div class="status-row">
                <input type="text" value="${status}" class="status-option" data-index="${index}" style="flex:1;">
                <button class="delete-btn" onclick="deleteStatus(${index})" ${index < 5 ? 'disabled title="Không thể xóa trạng thái mặc định"' : ''}>
                    <i class="fas fa-trash"></i> Xóa
                </button>
            </div>
        `).join('');

        // Add change listeners to inputs
        container.querySelectorAll('.status-option').forEach(input => {
            const index = parseInt(input.dataset.index);
            input.onchange = async () => {
                const newValue = input.value.trim();
                if (!newValue) {
                    alert('Trạng thái không được để trống');
                    input.value = window.LAB_STATUSES[index];
                    return;
                }
                if (window.LAB_STATUSES.includes(newValue) && window.LAB_STATUSES.indexOf(newValue) !== index) {
                    alert('Trạng thái này đã tồn tại!');
                    input.value = window.LAB_STATUSES[index];
                    return;
                }
                window.LAB_STATUSES[index] = newValue;
                try {
                    await saveLabSettings();
                } catch (e) {
                    input.value = window.LAB_STATUSES[index];
                }
            };
        });
    }

    window.deleteStatus = async function(index) {
        // Không cho xóa 5 trạng thái mặc định
        if (index < 5) {
            alert('Không thể xóa trạng thái mặc định');
            return;
        }
        
        if(confirm('Bạn có chắc muốn xóa trạng thái này?')) {
            const oldValue = window.LAB_STATUSES[index];
            try {
                window.LAB_STATUSES.splice(index, 1);
                await saveLabSettings();
                renderStatusOptions();
            } catch (e) {
                // Khôi phục nếu lưu thất bại
                window.LAB_STATUSES.splice(index, 0, oldValue);
                renderStatusOptions();
            }
        }
    };

    async function loadLabSettings(){
        try{
            const res = await fetch('/api/lab-settings'); 
            if(!res.ok) return; 
            const js = await res.json();
            if(js.status_options && Array.isArray(js.status_options) && js.status_options.length > 0) {
                // Đảm bảo 5 trạng thái mặc định luôn có
                const defaultStatuses = ["Chờ kết quả", "Đã nghe, thiếu kết quả", "Đã nghe", "Không liên lạc được", "Nhắn tin"];
                window.LAB_STATUSES = [...defaultStatuses, ...js.status_options.filter(s => !defaultStatuses.includes(s))];
            }
            renderStatusOptions();
        }catch(e){
            console.error('Error loading settings:', e);
        }
    }

    async function saveLabSettings(){
        try {
            // Tách riêng trạng thái mặc định và trạng thái tùy chỉnh
            const defaultStatuses = ["Chờ kết quả", "Đã nghe, thiếu kết quả", "Đã nghe", "Không liên lạc được", "Nhắn tin"];
            const customStatuses = window.LAB_STATUSES.filter(s => !defaultStatuses.includes(s));
            
            const payload = { 
                status_options: customStatuses,
                clear_status_on_sync: document.getElementById('lab-clear-status').checked
            };

            console.log('Saving settings:', payload);

            const res = await fetch('/api/lab-settings', { 
                method: 'PUT',
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(payload) 
            });

            if(res.ok){ 
                const result = await res.json();
                console.log('Save result:', result);
                
                if(result.status_options) {
                    window.LAB_STATUSES = [...defaultStatuses, ...result.status_options];
                }
                
                renderStatusOptions();
                alert('Đã lưu cài đặt!'); 
            } else {
                throw new Error('Lưu thất bại - vui lòng thử lại');
            }
        } catch(e) {
            console.error('Error saving settings:', e);
            throw e; // Ném lỗi để hàm gọi có thể xử lý
        }
    }

    // Initialize status options management
    document.addEventListener('DOMContentLoaded', () => {
        // Add new status handler
        document.getElementById('add-status-btn').onclick = async () => {
            const input = document.getElementById('new-status-input');
            const value = input.value.trim();
            if(!value) {
                alert('Vui lòng nhập trạng thái mới');
                return;
            }
            if(window.LAB_STATUSES.includes(value)) {
                alert('Trạng thái này đã tồn tại!');
                return;
            }
            
            try {
                window.LAB_STATUSES.push(value);
                await saveLabSettings();
                input.value = '';
                renderStatusOptions();
            } catch (e) {
                // Nếu lưu thất bại, xóa trạng thái vừa thêm
                window.LAB_STATUSES.pop();
                renderStatusOptions();
                alert(e.message);
            }
        };

        // Allow Enter key to add new status
        document.getElementById('new-status-input').onkeypress = (e) => {
            if(e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('add-status-btn').click();
            }
        };
    });