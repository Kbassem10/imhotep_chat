// Main JavaScript functionality for Imhotep Chat

// Toggle password visibility
function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const button = field.nextElementSibling;
    
    if (field.type === 'password') {
        field.type = 'text';
    } else {
        field.type = 'password';
    }
}

// Show/hide loading overlay
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// Auto-hide messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('[class*="bg-green-100"], [class*="bg-red-100"], [class*="bg-blue-100"]');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
});

// Validate password on registration
function validatePassword() {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (password && confirmPassword) {
        if (password.value !== confirmPassword.value) {
            alert('Passwords do not match!');
            return false;
        }
        
        if (password.value.length < 8) {
            alert('Password must be at least 8 characters long!');
            return false;
        }
    }
    
    return true;
}

// Simplified global function for sidebar toggle that will work with onclick
function handleSidebarToggle() {
    const sidebar = document.getElementById('sideNav');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (!sidebar || !overlay) return;
    
    if (sidebar.classList.contains('-translate-x-full')) {
        // Open sidebar
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
    } else {
        // Close sidebar
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
    }
}

// Make sure the function is globally available
window.handleSidebarToggle = handleSidebarToggle;

// Form submission handling
document.addEventListener('submit', function(e) {
    // Show loading overlay when form is submitted
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
});

// Mobile sidebar functionality 
document.addEventListener('DOMContentLoaded', function() {
    // Attach event listeners to all sidebar toggle buttons
    const toggleButtons = document.querySelectorAll('[data-action="toggle-sidebar"]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            handleSidebarToggle();
        });
    });
    
    // Make sure mobile navigation button is visible and working
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    if (mobileMenuButton) {
        // Ensure button is visible on mobile only
        if (window.innerWidth < 1024) {
            mobileMenuButton.style.display = 'block';
        } else {
            mobileMenuButton.style.display = 'none';
        }
        
        // Re-attach the click event (in case it was lost)
        const button = mobileMenuButton.querySelector('button');
        if (button) {
            button.onclick = function() {
                handleSidebarToggle();
            };
        }
    }
    
    // Ensure sidebar and overlay are properly initialized
    const sidebar = document.getElementById('sideNav');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar && !sidebar.classList.contains('-translate-x-full')) {
        sidebar.classList.add('-translate-x-full');
    }
    
    if (overlay && !overlay.classList.contains('hidden')) {
        overlay.classList.add('hidden');
    }
    
    // Add window resize listener to hide button on desktop
    window.addEventListener('resize', function() {
        if (mobileMenuButton) {
            if (window.innerWidth >= 1024) {
                mobileMenuButton.style.display = 'none';
            } else {
                mobileMenuButton.style.display = 'block';
            }
        }
    });
});

// Update mobile sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    // Make sure mobile navigation button is visible on mobile only
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    if (mobileMenuButton) {
        // Set initial visibility based on screen size
        mobileMenuButton.style.display = window.innerWidth < 1024 ? 'block' : 'none';
        
        // Add resize listener
        window.addEventListener('resize', function() {
            mobileMenuButton.style.display = window.innerWidth < 1024 ? 'block' : 'none';
        });
    }
    
    // Ensure sidebar starts in correct state (closed)
    const sidebar = document.getElementById('sideNav');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar) {
        sidebar.classList.add('-translate-x-full');
    }
    
    if (overlay) {
        overlay.classList.add('hidden');
    }
});

// Setup footer interaction
function setupFooterInteraction() {
    // Add any footer-specific functionality here
    const footerLinks = document.querySelectorAll('footer a');
    footerLinks.forEach(link => {
        if (link.getAttribute('rel') === 'noopener noreferrer') {
            link.addEventListener('click', function(e) {
                // Optional: track outbound links
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'click', {
                        'event_category': 'outbound',
                        'event_label': link.href
                    });
                }
            });
        }
    });

    // Add PWA install prompt
    const appVersion = document.querySelector('footer p.text-xs.text-gray-500');
    if (appVersion && window.matchMedia('(display-mode: browser)').matches) {
        // Check if app is installable
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            const installPrompt = e;
            
            // Create install button if doesn't exist
            if (!document.getElementById('pwa-install-btn')) {
                const installBtn = document.createElement('button');
                installBtn.id = 'pwa-install-btn';
                installBtn.className = 'ml-2 text-xs text-blue-600 hover:text-blue-800 font-medium';
                installBtn.textContent = 'Install App';
                installBtn.addEventListener('click', () => {
                    installPrompt.prompt();
                    installPrompt.userChoice.then(choiceResult => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('User accepted the install prompt');
                        }
                    });
                });
                appVersion.appendChild(installBtn);
            }
        });
    }
}

// Chat functionality
class ChatManager {
    constructor() {
        this.currentRoom = null;
        this.socket = null;
        this.messageHistory = new Map();
        this.typingTimer = null;
        this.isTyping = false;
    }

    // Initialize chat interface
    init() {
        this.setupEventListeners();
        this.loadRecentChats();
    }

    // Setup event listeners
    setupEventListeners() {
        // Message input events
        const messageInput = document.getElementById('messageText');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
                this.handleTyping();
            });

            messageInput.addEventListener('keyup', () => {
                this.handleTypingStop();
            });
        }

        // Emoji picker
        this.initEmojiPicker();
        
        // File upload
        this.initFileUpload();
    }

    // Handle typing indicator
    handleTyping() {
        if (!this.isTyping && this.socket) {
            this.isTyping = true;
            this.socket.send(JSON.stringify({
                type: 'typing',
                room_id: this.currentRoom
            }));
        }
        
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(() => {
            this.handleTypingStop();
        }, 1000);
    }

    handleTypingStop() {
        if (this.isTyping && this.socket) {
            this.isTyping = false;
            this.socket.send(JSON.stringify({
                type: 'stop_typing',
                room_id: this.currentRoom
            }));
        }
    }

    // Message formatting
    formatMessage(text) {
        // Convert URLs to links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        text = text.replace(urlRegex, '<a href="$1" target="_blank" class="text-blue-600 hover:underline">$1</a>');
        
        // Convert emoji codes to emoji
        const emojiMap = {
            ':)': '😊', ':(': '😢', ':D': '😃', ':P': '😛',
            '<3': '❤️', ':thumbsup:': '👍', ':fire:': '🔥'
        };
        
        Object.keys(emojiMap).forEach(code => {
            text = text.replace(new RegExp(escapeRegex(code), 'g'), emojiMap[code]);
        });
        
        return text;
    }

    // Initialize emoji picker
    initEmojiPicker() {
        const emojiButton = document.getElementById('emojiButton');
        if (emojiButton) {
            emojiButton.addEventListener('click', () => {
                this.toggleEmojiPicker();
            });
        }
    }

    toggleEmojiPicker() {
        let picker = document.getElementById('emojiPicker');
        if (!picker) {
            picker = this.createEmojiPicker();
        }
        picker.classList.toggle('hidden');
    }

    createEmojiPicker() {
        const emojis = ['😊', '😢', '😃', '😛', '❤️', '👍', '🔥', '🎉', '💯', '🚀'];
        const picker = document.createElement('div');
        picker.id = 'emojiPicker';
        picker.className = 'absolute bottom-12 right-0 bg-white border border-gray-200 rounded-lg shadow-lg p-2 grid grid-cols-5 gap-1 hidden z-10';
        
        emojis.forEach(emoji => {
            const button = document.createElement('button');
            button.className = 'p-2 hover:bg-gray-100 rounded text-lg';
            button.textContent = emoji;
            button.onclick = () => this.insertEmoji(emoji);
            picker.appendChild(button);
        });
        
        document.getElementById('messageInput').appendChild(picker);
        return picker;
    }

    insertEmoji(emoji) {
        const input = document.getElementById('messageText');
        const start = input.selectionStart;
        const end = input.selectionEnd;
        const text = input.value;
        
        input.value = text.substring(0, start) + emoji + text.substring(end);
        input.focus();
        input.setSelectionRange(start + emoji.length, start + emoji.length);
        
        this.toggleEmojiPicker();
    }

    // Initialize file upload
    initFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const fileButton = document.getElementById('fileButton');
        
        if (fileButton && fileInput) {
            fileButton.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', (e) => {
                this.handleFileUpload(e.target.files[0]);
            });
        }
    }

    handleFileUpload(file) {
        if (!file) return;
        
        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            this.showNotification('File size must be less than 10MB', 'error');
            return;
        }
        
        // Show upload progress
        this.showUploadProgress(file.name);
        
        // Simulate upload (replace with actual upload logic)
        setTimeout(() => {
            this.hideUploadProgress();
            this.addFileMessage(file);
        }, 2000);
    }

    showUploadProgress(fileName) {
        const progressHtml = `
            <div id="uploadProgress" class="flex justify-end mb-4">
                <div class="max-w-xs bg-blue-100 rounded-lg p-3">
                    <div class="flex items-center space-x-2">
                        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span class="text-sm text-blue-800">Uploading ${fileName}...</span>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('messagesArea').innerHTML += progressHtml;
        this.scrollToBottom();
    }

    hideUploadProgress() {
        const progress = document.getElementById('uploadProgress');
        if (progress) {
            progress.remove();
        }
    }

    addFileMessage(file) {
        const fileIcon = this.getFileIcon(file.type);
        const message = {
            id: Date.now(),
            type: 'file',
            fileName: file.name,
            fileSize: this.formatFileSize(file.size),
            fileIcon: fileIcon,
            sent: true,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        
        this.addMessageToUI(message);
    }

    getFileIcon(fileType) {
        if (fileType.startsWith('image/')) return '🖼️';
        if (fileType.startsWith('video/')) return '🎥';
        if (fileType.startsWith('audio/')) return '🎵';
        if (fileType.includes('pdf')) return '📄';
        if (fileType.includes('word')) return '📝';
        return '📎';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Scroll to bottom of messages
    scrollToBottom() {
        const messagesArea = document.getElementById('messagesArea');
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    }

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 max-w-sm p-4 rounded-lg shadow-lg z-50 ${
            type === 'error' ? 'bg-red-500 text-white' : 
            type === 'success' ? 'bg-green-500 text-white' : 
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Add message to UI
    addMessageToUI(message) {
        const messagesArea = document.getElementById('messagesArea');
        if (!messagesArea) return;
        
        let messageHtml;
        
        if (message.type === 'file') {
            messageHtml = this.createFileMessageHTML(message);
        } else {
            messageHtml = this.createTextMessageHTML(message);
        }
        
        messagesArea.innerHTML += messageHtml;
        this.scrollToBottom();
    }

    createTextMessageHTML(message) {
        const alignment = message.sent ? 'justify-end' : 'justify-start';
        const bgColor = message.sent ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800';
        const borderRadius = message.sent ? 'rounded-l-lg rounded-tr-lg' : 'rounded-r-lg rounded-tl-lg';
        
        return `
            <div class="flex ${alignment} mb-4">
                <div class="max-w-xs lg:max-w-md px-4 py-2 ${bgColor} ${borderRadius}">
                    <p class="text-sm">${this.formatMessage(message.text)}</p>
                    <p class="text-xs opacity-75 mt-1">${message.time}</p>
                </div>
            </div>
        `;
    }

    createFileMessageHTML(message) {
        const alignment = message.sent ? 'justify-end' : 'justify-start';
        const bgColor = message.sent ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800';
        const borderRadius = message.sent ? 'rounded-l-lg rounded-tr-lg' : 'rounded-r-lg rounded-tl-lg';
        
        return `
            <div class="flex ${alignment} mb-4">
                <div class="max-w-xs lg:max-w-md px-4 py-3 ${bgColor} ${borderRadius}">
                    <div class="flex items-center space-x-3">
                        <span class="text-2xl">${message.fileIcon}</span>
                        <div>
                            <p class="text-sm font-medium">${message.fileName}</p>
                            <p class="text-xs opacity-75">${message.fileSize}</p>
                        </div>
                    </div>
                    <p class="text-xs opacity-75 mt-2">${message.time}</p>
                </div>
            </div>
        `;
    }
}

// Utility function
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Initialize chat manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chat if we're on the chat page
    if (document.getElementById('messagesArea')) {
        window.chatManager = new ChatManager();
        window.chatManager.init();
    }
});
