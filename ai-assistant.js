/**
 * AI Assistant - Trợ lý AI hỗ trợ giọng nói và văn bản tiếng Việt
 * Luôn hiển thị trên mọi trang
 */

class AIAssistant {
    constructor() {
        this.isOpen = false;
        this.isListening = false;
        this.recognition = null;
        this.wakeWordRecognition = null; // Recognition riêng cho wake word
        this.isWakeWordListening = false;
        this.wakeWordEnabled = this.getWakeWordSetting();
        this.messages = [];
        this.setupRecognition();
        this.setupWakeWordRecognition();
        this.createWidget();
        this.loadHistory();
    }
    
    // Lấy cài đặt wake word từ localStorage
    getWakeWordSetting() {
        const saved = localStorage.getItem('aiAssistantWakeWord');
        return saved !== null ? saved === 'true' : true; // Mặc định bật
    }
    
    // Lưu cài đặt wake word
    saveWakeWordSetting(enabled) {
        this.wakeWordEnabled = enabled;
        localStorage.setItem('aiAssistantWakeWord', enabled.toString());
    }

    // Tạo widget UI
    createWidget() {
        const container = document.createElement('div');
        container.className = 'ai-assistant-container';
        container.innerHTML = `
            <div class="ai-assistant-window" id="aiAssistantWindow">
                <div class="ai-assistant-header">
                    <div>
                        <h3>
                            <img src="images/ai-assistant-avatar.jpg" alt="Trợ lý AI" class="ai-assistant-avatar-header" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
                            <i class="fas fa-robot" style="display:none;"></i>
                            Trợ lý AI
                        </h3>
                        <div class="ai-assistant-status">
                            <span class="status-dot" id="aiAssistantStatusDot"></span>
                            <span id="aiAssistantStatusText">Sẵn sàng</span>
                        </div>
                        <button class="ai-assistant-wake-toggle" id="aiWakeWordToggle" onclick="aiAssistant.toggleWakeWord()" title="Bật/tắt đánh thức bằng giọng nói">
                            <i class="fas fa-microphone-slash" id="aiWakeWordIcon"></i>
                        </button>
                    </div>
                    <button class="ai-assistant-close" onclick="aiAssistant.toggleWindow()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="ai-assistant-messages" id="aiAssistantMessages">
                    <div class="ai-assistant-message assistant">
                        <img src="images/ai-assistant-avatar.jpg" alt="Trợ lý AI" class="ai-message-avatar" onerror="this.style.display='none';">
                        <div class="ai-message-content">
                            <div>Xin chào! Tôi là trợ lý AI của Phòng khám Đại Anh. Tôi có thể giúp bạn:</div>
                            <ul style="margin: 8px 0 0 20px; padding: 0;">
                                <li>Tìm kiếm bệnh nhân</li>
                                <li>Xem thông tin phòng khám</li>
                                <li>Điều hướng đến các trang</li>
                                <li>Trả lời câu hỏi</li>
                            </ul>
                            <div class="timestamp">${this.getTimeStamp()}</div>
                        </div>
                    </div>
                </div>
                
                <div class="ai-assistant-quick-actions">
                    <button class="ai-quick-action-btn" onclick="aiAssistant.sendQuickCommand('tìm kiếm bệnh nhân')">
                        <i class="fas fa-search"></i> Tìm bệnh nhân
                    </button>
                    <button class="ai-quick-action-btn" onclick="aiAssistant.sendQuickCommand('xem danh sách khám')">
                        <i class="fas fa-list"></i> Danh sách khám
                    </button>
                    <button class="ai-quick-action-btn" onclick="aiAssistant.sendQuickCommand('xem lịch làm việc')">
                        <i class="fas fa-calendar"></i> Lịch làm việc
                    </button>
                    <button class="ai-quick-action-btn" onclick="aiAssistant.sendQuickCommand('trang chủ')">
                        <i class="fas fa-home"></i> Trang chủ
                    </button>
                </div>
                
                <div class="ai-assistant-input-area">
                    <div class="ai-assistant-input-wrapper">
                        <textarea 
                            id="aiAssistantInput" 
                            class="ai-assistant-input" 
                            placeholder="Nhập câu hỏi hoặc nhấn vào biểu tượng mic để nói..."
                            rows="1"
                            onkeydown="if(event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); aiAssistant.sendMessage(); }"
                            oninput="this.style.height = 'auto'; this.style.height = Math.min(this.scrollHeight, 100) + 'px';"
                        ></textarea>
                        <button 
                            class="ai-assistant-voice-btn" 
                            id="aiAssistantVoiceBtn"
                            onclick="aiAssistant.toggleVoiceRecognition()"
                            title="Nhấn để nói (tiếng Việt)"
                        >
                            <i class="fas fa-microphone"></i>
                        </button>
                    </div>
                    <button 
                        class="ai-assistant-send-btn" 
                        onclick="aiAssistant.sendMessage()"
                        id="aiAssistantSendBtn"
                    >
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
            
            <button class="ai-assistant-btn" id="aiAssistantBtn" onclick="aiAssistant.toggleWindow()">
                <img src="images/ai-assistant-avatar.jpg" alt="Trợ lý AI" class="ai-assistant-avatar-btn" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
                <i class="fas fa-robot" style="display:none;"></i>
            </button>
        `;
        
        document.body.appendChild(container);
        this.window = document.getElementById('aiAssistantWindow');
        this.btn = document.getElementById('aiAssistantBtn');
        this.input = document.getElementById('aiAssistantInput');
        this.messagesContainer = document.getElementById('aiAssistantMessages');
        this.voiceBtn = document.getElementById('aiAssistantVoiceBtn');
        
        // Cập nhật UI wake word ban đầu
        setTimeout(() => {
            this.updateWakeWordUI();
        }, 100);
        
        // Đóng khi click outside
        document.addEventListener('click', (e) => {
            if (this.isOpen && !container.contains(e.target)) {
                this.toggleWindow();
            }
        });
    }

    // Thiết lập nhận diện giọng nói
    setupRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            // Cấu hình tối ưu cho tiếng Việt
            this.recognition.lang = 'vi-VN'; // Tiếng Việt
            this.recognition.continuous = true; // Nghe liên tục cho đến khi dừng
            this.recognition.interimResults = true; // Hiển thị kết quả tạm thời
            this.recognition.maxAlternatives = 3; // Lấy 3 phương án tốt nhất
            
            // Grammar để cải thiện độ chính xác (nếu hỗ trợ)
            if (this.recognition.grammars) {
                // Có thể thêm grammar tùy chỉnh ở đây nếu cần
            }
            
            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateVoiceButton(true);
                this.addMessage('assistant', 'Đang nghe bạn nói... 👂\n\nNói rõ ràng bằng tiếng Việt. Nhấn nút mic lần nữa để dừng.');
            };
            
            this.recognition.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';
                
                // Xử lý tất cả các kết quả (interim và final)
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    const confidence = event.results[i][0].confidence || 0.8;
                    
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                // Hiển thị transcript tạm thời
                if (interimTranscript) {
                    this.input.value = finalTranscript + interimTranscript;
                    this.input.style.color = '#666'; // Màu xám cho text tạm thời
                } else if (finalTranscript) {
                    this.input.value = finalTranscript.trim();
                    this.input.style.color = '#333'; // Màu đen cho text cuối cùng
                }
                
                // Nếu có kết quả cuối cùng, tự động gửi sau 1 giây
                if (finalTranscript.trim()) {
                    clearTimeout(this.autoSendTimer);
                    this.autoSendTimer = setTimeout(() => {
                        this.isListening = false;
                        this.updateVoiceButton(false);
                        this.recognition.stop();
                        this.sendMessage();
                    }, 1000);
                }
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                
                // Không dừng nếu là lỗi tạm thời
                if (event.error === 'no-speech') {
                    // Tiếp tục nghe nếu không có lời nói trong 3 giây
                    this.addMessage('assistant', 'Chưa nghe thấy lời nói. Vui lòng nói lại...');
                    return;
                }
                
                this.isListening = false;
                this.updateVoiceButton(false);
                
                let errorMsg = 'Không thể nhận diện giọng nói.';
                if (event.error === 'not-allowed') {
                    errorMsg = 'Vui lòng cho phép truy cập microphone trong cài đặt trình duyệt.';
                } else if (event.error === 'audio-capture') {
                    errorMsg = 'Không tìm thấy microphone. Vui lòng kiểm tra thiết bị.';
                } else if (event.error === 'network') {
                    errorMsg = 'Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet.';
                } else if (event.error === 'aborted') {
                    // Người dùng dừng, không hiển thị lỗi
                    return;
                }
                
                this.addMessage('error', errorMsg);
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                this.updateVoiceButton(false);
                
                // Nếu đang trong chế độ continuous và chưa có kết quả, tự động restart
                // (chỉ khi người dùng chưa dừng thủ công)
                if (this.recognition.continuous && this.input.value.trim() === '') {
                    // Không tự động restart để tránh loop vô hạn
                }
            };
        } else {
            console.warn('Speech recognition not supported');
            if (this.voiceBtn) {
                this.voiceBtn.style.display = 'none';
            }
        }
    }

    // Thiết lập wake word recognition (luôn lắng nghe ở chế độ nền)
    setupWakeWordRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.wakeWordRecognition = new SpeechRecognition();
            
            // Cấu hình cho wake word detection
            this.wakeWordRecognition.lang = 'vi-VN';
            this.wakeWordRecognition.continuous = true; // Luôn nghe
            this.wakeWordRecognition.interimResults = false; // Chỉ lấy kết quả cuối
            this.wakeWordRecognition.maxAlternatives = 1;
            
            // Danh sách từ khóa đánh thức
            this.wakeWords = [
                'trợ lý',
                'trợ lý ai',
                'ai ơi',
                'hey ai',
                'chào ai',
                'gọi trợ lý',
                'mở trợ lý',
                'bật trợ lý',
                'assistant',
                'hey assistant'
            ];
            
            this.wakeWordRecognition.onresult = (event) => {
                if (!this.wakeWordEnabled || this.isOpen) {
                    return; // Bỏ qua nếu tắt hoặc đang mở
                }
                
                const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
                
                // Kiểm tra wake word
                const detectedWakeWord = this.wakeWords.find(wakeWord => 
                    transcript.includes(wakeWord.toLowerCase())
                );
                
                if (detectedWakeWord) {
                    console.log('Wake word detected:', detectedWakeWord);
                    this.wakeUp();
                }
            };
            
            this.wakeWordRecognition.onerror = (event) => {
                // Không hiển thị lỗi cho wake word recognition để không làm phiền người dùng
                if (event.error === 'no-speech' || event.error === 'aborted') {
                    return;
                }
                
                // Chỉ log lỗi nghiêm trọng
                if (event.error !== 'network') {
                    console.warn('Wake word recognition error:', event.error);
                }
            };
            
            this.wakeWordRecognition.onend = () => {
                // Tự động restart wake word recognition nếu đang bật
                if (this.wakeWordEnabled && !this.isOpen) {
                    try {
                        this.wakeWordRecognition.start();
                    } catch (e) {
                        // Ignore errors khi restart
                        setTimeout(() => {
                            if (this.wakeWordEnabled) {
                                this.setupWakeWordRecognition();
                            }
                        }, 1000);
                    }
                }
            };
            
            // Khởi động wake word recognition nếu được bật
            if (this.wakeWordEnabled) {
                this.startWakeWordListening();
            }
        }
    }
    
    // Khởi động wake word listening
    startWakeWordListening() {
        if (!this.wakeWordRecognition || this.isWakeWordListening || !this.wakeWordEnabled) {
            return;
        }
        
        try {
            this.wakeWordRecognition.start();
            this.isWakeWordListening = true;
            this.updateWakeWordUI();
            console.log('Wake word listening started');
        } catch (e) {
            console.warn('Cannot start wake word recognition:', e);
            // Thử lại sau 2 giây
            setTimeout(() => {
                if (this.wakeWordEnabled) {
                    this.startWakeWordListening();
                }
            }, 2000);
        }
    }
    
    // Dừng wake word listening
    stopWakeWordListening() {
        if (this.wakeWordRecognition && this.isWakeWordListening) {
            try {
                this.wakeWordRecognition.stop();
            } catch (e) {
                // Ignore
            }
            this.isWakeWordListening = false;
            this.updateWakeWordUI();
        }
    }
    
    // Đánh thức AI (mở cửa sổ và bắt đầu nghe)
    wakeUp() {
        console.log('AI awakened!');
        
        // Mở cửa sổ
        if (!this.isOpen) {
            this.toggleWindow();
        }
        
        // Hiển thị thông báo
        this.addMessage('assistant', '👋 Đã đánh thức! Tôi đang lắng nghe bạn...');
        
        // Bắt đầu nghe ngay
        setTimeout(() => {
            if (this.recognition && !this.isListening) {
                this.startListening();
            }
        }, 500);
        
        // Cập nhật trạng thái
        this.updateStatus('Đang lắng nghe...', true);
    }
    
    // Toggle wake word
    toggleWakeWord() {
        this.wakeWordEnabled = !this.wakeWordEnabled;
        this.saveWakeWordSetting(this.wakeWordEnabled);
        
        if (this.wakeWordEnabled) {
            this.startWakeWordListening();
        } else {
            this.stopWakeWordListening();
        }
        
        this.updateWakeWordUI();
        
        // Thông báo
        const statusText = this.wakeWordEnabled ? 'đã bật' : 'đã tắt';
        this.addMessage('assistant', `Đánh thức bằng giọng nói ${statusText}. ${this.wakeWordEnabled ? 'Bạn có thể nói "Trợ lý" hoặc "AI ơi" để đánh thức tôi.' : ''}`);
    }
    
    // Cập nhật UI wake word
    updateWakeWordUI() {
        const toggle = document.getElementById('aiWakeWordToggle');
        const icon = document.getElementById('aiWakeWordIcon');
        
        if (toggle && icon) {
            if (this.wakeWordEnabled) {
                toggle.classList.add('active');
                icon.className = 'fas fa-microphone';
                toggle.title = 'Đánh thức bằng giọng nói: Bật (Nhấn để tắt)';
                
                // Cập nhật nút floating
                if (this.btn && !this.isOpen) {
                    this.btn.classList.add('wake-listening');
                }
            } else {
                toggle.classList.remove('active');
                icon.className = 'fas fa-microphone-slash';
                toggle.title = 'Đánh thức bằng giọng nói: Tắt (Nhấn để bật)';
                
                // Cập nhật nút floating
                if (this.btn) {
                    this.btn.classList.remove('wake-listening');
                }
            }
        }
    }
    
    // Cập nhật trạng thái hiển thị
    updateStatus(text, listening = false) {
        const statusText = document.getElementById('aiAssistantStatusText');
        const statusDot = document.getElementById('aiAssistantStatusDot');
        
        if (statusText) {
            statusText.textContent = text;
        }
        
        if (statusDot) {
            if (listening) {
                statusDot.style.animation = 'blink 1s infinite';
            } else {
                statusDot.style.animation = 'blink 2s infinite';
            }
        }
    }

    // Toggle window
    toggleWindow() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.window.classList.add('active');
            this.input.focus();
            this.updateStatus('Sẵn sàng', false);
            
            // Tạm dừng wake word khi mở cửa sổ
            if (this.wakeWordEnabled) {
                this.stopWakeWordListening();
            }
        } else {
            this.window.classList.remove('active');
            if (this.isListening) {
                this.stopListening();
            }
            
            // Tiếp tục wake word listening khi đóng cửa sổ
            if (this.wakeWordEnabled) {
                setTimeout(() => {
                    this.startWakeWordListening();
                }, 500);
            }
            
            this.updateStatus('Sẵn sàng', false);
        }
        
        this.updateWakeWordUI();
    }

    // Toggle voice recognition
    toggleVoiceRecognition() {
        if (!this.recognition) {
            this.addMessage('error', 'Trình duyệt của bạn không hỗ trợ nhận diện giọng nói.');
            return;
        }
        
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    // Bắt đầu nghe
    startListening() {
        try {
            // Đặt lại continuous mode
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            
            // Xóa nội dung input cũ
            if (this.input) {
                this.input.value = '';
            }
            
            this.recognition.start();
            this.btn.classList.add('listening');
        } catch (e) {
            console.error('Error starting recognition:', e);
            
            // Xử lý lỗi khi recognition đang chạy
            if (e.message && e.message.includes('already')) {
                this.recognition.stop();
                setTimeout(() => {
                    this.startListening();
                }, 100);
            } else {
                this.addMessage('error', 'Không thể bắt đầu nhận diện giọng nói. Vui lòng thử lại.');
            }
        }
    }

    // Dừng nghe
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.recognition.continuous = false; // Tắt continuous mode khi dừng
            this.btn.classList.remove('listening');
            
            // Xóa timer auto-send nếu có
            if (this.autoSendTimer) {
                clearTimeout(this.autoSendTimer);
            }
            
            // Nếu có text trong input, gửi luôn
            if (this.input && this.input.value.trim()) {
                this.sendMessage();
            }
        }
    }

    // Cập nhật nút voice
    updateVoiceButton(listening) {
        if (listening) {
            this.voiceBtn.classList.add('listening');
            this.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        } else {
            this.voiceBtn.classList.remove('listening');
            this.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        }
    }

    // Gửi lệnh nhanh
    sendQuickCommand(command) {
        this.input.value = command;
        this.sendMessage();
    }

    // Chuẩn hóa văn bản tiếng Việt
    normalizeVietnameseText(text) {
        if (!text) return '';
        
        // Loại bỏ khoảng trắng thừa
        text = text.replace(/\s+/g, ' ').trim();
        
        // Chuẩn hóa các từ viết tắt phổ biến
        const replacements = {
            'pk': 'phòng khám',
            'bn': 'bệnh nhân',
            'bs': 'bác sĩ',
            'dt': 'điện thoại',
            'dc': 'địa chỉ'
        };
        
        // Thay thế từ viết tắt (chỉ thay khi đứng một mình)
        for (const [abbr, full] of Object.entries(replacements)) {
            const regex = new RegExp(`\\b${abbr}\\b`, 'gi');
            text = text.replace(regex, full);
        }
        
        // Loại bỏ các ký tự đặc biệt không cần thiết (giữ lại dấu tiếng Việt)
        text = text.replace(/[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ.,!?;:]/g, ' ');
        
        return text.trim();
    }
    
    // Gửi tin nhắn
    async sendMessage() {
        const originalText = this.input.value.trim();
        if (!originalText) return;
        
        // Chuẩn hóa văn bản tiếng Việt
        const normalizedText = this.normalizeVietnameseText(originalText);
        
        // Thêm tin nhắn người dùng (hiển thị text gốc)
        this.addMessage('user', originalText);
        this.input.value = '';
        this.input.style.height = 'auto';
        this.input.style.color = '#333'; // Reset màu
        
        // Disable input
        this.input.disabled = true;
        const sendBtn = document.getElementById('aiAssistantSendBtn');
        if (sendBtn) sendBtn.disabled = true;
        
        // Hiển thị typing indicator
        this.showTyping();
        
        try {
            // Gửi đến API với text đã chuẩn hóa
            const response = await fetch('/api/ai-assistant/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: normalizedText, // Gửi text đã chuẩn hóa
                    original_message: originalText, // Giữ lại bản gốc để reference
                    context: this.getPageContext()
                })
            });
            
            const data = await response.json();
            this.hideTyping();
            
            if (data.success) {
                // Lưu interaction_id để feedback
                const interactionId = data.interaction_id;
                const detectedIntent = data.detected_intent;
                const confidence = data.confidence || 0.8;
                
                // Thêm tin nhắn với nút feedback
                const responseText = data.response;
                
                this.addMessage('assistant', responseText, interactionId, detectedIntent, confidence);
                
                // Nếu có action, thực hiện
                if (data.action) {
                    this.executeAction(data.action);
                }
            } else {
                this.addMessage('error', data.error || 'Có lỗi xảy ra. Vui lòng thử lại.');
            }
        } catch (error) {
            this.hideTyping();
            console.error('Error sending message:', error);
            this.addMessage('error', 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng.');
        } finally {
            this.input.disabled = false;
            if (sendBtn) sendBtn.disabled = false;
            this.input.focus();
        }
    }

    // Thêm tin nhắn với feedback buttons
    addMessage(type, text, interactionId = null, detectedIntent = null, confidence = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-assistant-message ${type}`;
        
        let feedbackHtml = '';
        // Chỉ thêm feedback buttons cho message từ assistant (trừ error và user messages)
        if (type === 'assistant' && interactionId && detectedIntent) {
            const confidencePercent = confidence ? Math.round(confidence * 100) : '?';
            feedbackHtml = `
                <div class="ai-message-feedback" style="margin-top: 8px; display: flex; gap: 8px; align-items: center; font-size: 12px;">
                    <span style="opacity: 0.7;">Độ tin cậy: ${confidencePercent}%</span>
                    <button onclick="aiAssistant.sendFeedback(${interactionId}, 'positive')" 
                            class="ai-feedback-btn positive" 
                            title="Phản hồi tốt">
                        <i class="fas fa-thumbs-up"></i>
                    </button>
                    <button onclick="aiAssistant.sendFeedback(${interactionId}, 'negative')" 
                            class="ai-feedback-btn negative" 
                            title="Phản hồi không đúng">
                        <i class="fas fa-thumbs-down"></i>
                    </button>
                </div>
            `;
        }
        
        const avatarHtml = type === 'assistant' ? `
            <img src="images/ai-assistant-avatar.jpg" alt="Trợ lý AI" class="ai-message-avatar" onerror="this.style.display='none';">
        ` : '';
        
        messageDiv.innerHTML = `
            ${avatarHtml}
            <div class="ai-message-content">
                <div>${this.formatMessage(text)}</div>
                ${feedbackHtml}
                <div class="timestamp">${this.getTimeStamp()}</div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Lưu vào lịch sử
        this.messages.push({ type, text, timestamp: new Date(), interactionId, detectedIntent });
        this.saveHistory();
    }
    
    // Gửi feedback
    async sendFeedback(interactionId, feedback) {
        try {
            const response = await fetch('/api/ai-assistant/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    interaction_id: interactionId,
                    feedback: feedback
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessage('assistant', '✅ Cảm ơn bạn đã phản hồi! Tôi sẽ học từ phản hồi này để cải thiện.', null, null, null);
            } else {
                this.addMessage('error', 'Không thể gửi phản hồi. Vui lòng thử lại.');
            }
        } catch (error) {
            console.error('Error sending feedback:', error);
            this.addMessage('error', 'Không thể gửi phản hồi. Vui lòng kiểm tra kết nối.');
        }
    }

    // Format tin nhắn (markdown đơn giản)
    formatMessage(text) {
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        // Convert URLs
        text = text.replace(/https?:\/\/[^\s]+/g, '<a href="$&" target="_blank">$&</a>');
        
        // Convert **bold**
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        return text;
    }

    // Hiển thị typing indicator
    showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-assistant-typing';
        typingDiv.id = 'aiTypingIndicator';
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    // Ẩn typing indicator
    hideTyping() {
        const typing = document.getElementById('aiTypingIndicator');
        if (typing) {
            typing.remove();
        }
    }

    // Scroll to bottom
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    // Lấy timestamp
    getTimeStamp() {
        const now = new Date();
        return now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    }

    // Lấy context của trang hiện tại
    getPageContext() {
        return {
            url: window.location.pathname,
            title: document.title,
            page: window.location.pathname.split('/').pop() || 'index.html'
        };
    }

    // Thực hiện action
    executeAction(action) {
        switch (action.type) {
            case 'navigate':
                if (action.url) {
                    window.location.href = action.url;
                }
                break;
            case 'search':
                if (action.selector) {
                    const element = document.querySelector(action.selector);
                    if (element) {
                        element.value = action.value || '';
                        element.focus();
                        if (element.oninput) element.oninput();
                        if (element.onkeyup) element.onkeyup();
                    }
                }
                break;
            case 'click':
                if (action.selector) {
                    const element = document.querySelector(action.selector);
                    if (element) {
                        element.click();
                    }
                }
                break;
            case 'refresh':
                if (typeof refreshData === 'function') {
                    refreshData();
                } else {
                    window.location.reload();
                }
                break;
        }
    }

    // Lưu lịch sử
    saveHistory() {
        try {
            const history = this.messages.slice(-20); // Chỉ lưu 20 tin nhắn gần nhất
            localStorage.setItem('aiAssistantHistory', JSON.stringify(history));
        } catch (e) {
            console.error('Error saving history:', e);
        }
    }

    // Load lịch sử
    loadHistory() {
        try {
            const saved = localStorage.getItem('aiAssistantHistory');
            if (saved) {
                const history = JSON.parse(saved);
                // Không load lại toàn bộ để tránh spam, chỉ load khi cần
            }
        } catch (e) {
            console.error('Error loading history:', e);
        }
    }
}

// Tự động load CSS nếu chưa có
function ensureAIAssistantCSS() {
    if (!document.querySelector('link[href*="ai-assistant.css"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'ai-assistant.css';
        document.head.appendChild(link);
    }
}

// Khởi tạo AI Assistant khi trang load
let aiAssistant;
document.addEventListener('DOMContentLoaded', function() {
    ensureAIAssistantCSS();
    aiAssistant = new AIAssistant();
});

// Export cho global access
window.aiAssistant = aiAssistant;

