/**
 * Đặt tỷ lệ hiển thị trang ~90% trên mọi trang có gắn script này.
 *
 * Hạn chế: không thể đổi zoom hệ thống của trình duyệt (Ctrl +/-); chỉ dùng CSS zoom
 * trên <html>. Chrome / Edge / Safari ổn định; Firefox 126+ hỗ trợ thuộc tính zoom.
 *
 * Cách dùng: <script src="page-zoom-90.js"></script> (ưu tiên cuối <body> hoặc trong <head>).
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
