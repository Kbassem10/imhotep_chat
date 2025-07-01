// Chat functionality variables
let currentChatId = null;
let messageSocket = null;
let currentFriendsTab = 'friends';
let isMobileView = false;
let userFriends = [];

// Initialize the main menu functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeMainMenu();
    checkMobileView();
    
    // Add resize listener
    window.addEventListener('resize', checkMobileView);
});

// Initialize all event listeners and functionality
function initializeMainMenu() {
    // Modal toggles
    document.getElementById('friendsModalBtn')?.addEventListener('click', toggleFriendsModal);
    document.getElementById('newChatModalBtn')?.addEventListener('click', toggleNewChatModal);
    document.getElementById('emptyStateNewChatBtn')?.addEventListener('click', toggleNewChatModal);
    
    // Modal close buttons
    document.getElementById('closeFriendsModal')?.addEventListener('click', toggleFriendsModal);
    document.getElementById('closeNewChatModal')?.addEventListener('click', toggleNewChatModal);
    
    // Search functionality
    document.getElementById('chatSearchInput')?.addEventListener('keyup', (e) => filterChats(e.target.value));
    document.getElementById('userSearchInput')?.addEventListener('keyup', (e) => searchUsers(e.target.value));
    
    // Friends tab switching
    document.getElementById('friendsTab')?.addEventListener('click', () => switchFriendsTab('friends'));
    document.getElementById('requestsTab')?.addEventListener('click', () => switchFriendsTab('requests'));
    
    // Message form
    document.getElementById('messageForm')?.addEventListener('submit', sendMessage);
    document.getElementById('messageText')?.addEventListener('keydown', handleTextareaKeydown);
    document.getElementById('messageText')?.addEventListener('input', (e) => autoResizeTextarea(e.target));
    
    // Chat items
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', function() {
            const chatId = this.dataset.chatId;
            const chatName = this.dataset.chatName;
            openChat(chatId, chatName);
        });
    });
    
    // Mobile back button
    document.getElementById('backToChatsBtn')?.addEventListener('click', closeChatOnMobile);
}

// Check if user is on mobile
function checkMobileView() {
    isMobileView = window.innerWidth < 1024;
}

// Enhanced mobile functionality
function closeChatOnMobile() {
    if (isMobileView) {
        currentChatId = null;
        if (messageSocket) {
            messageSocket.close();
            messageSocket = null;
        }
        
        const chatSection = document.getElementById('chatSection');
        const chatListSection = document.getElementById('chatListSection');
        const mobileChatHeader = document.getElementById('mobileChatHeader');
        
        // Add slide out animation
        chatSection.classList.add('chat-slide-out');
        
        setTimeout(() => {
            chatSection.classList.add('hidden');
            chatSection.classList.remove('mobile-fullscreen', 'chat-slide-out', 'fixed', 'inset-0', 'z-40', 'flex', 'flex-col');
            chatListSection.classList.remove('hidden', 'mobile-hidden');
            mobileChatHeader.classList.add('hidden');
        }, 300);
    }
}

// Auto-resize textarea
function autoResizeTextarea(textarea) {
    textarea.style.height = '48px';
    textarea.style.height = Math.min(textarea.scrollHeight, 128) + 'px';
}

// Handle textarea keydown
function handleTextareaKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage(event);
    }
}

// Toggle new chat modal
function toggleNewChatModal() {
    const modal = document.getElementById('newChatModal');
    modal.classList.toggle('hidden');
    if (!modal.classList.contains('hidden')) {
        document.getElementById('userSearchInput').focus();
        // Load friends list for checking
        loadFriendsForNewChat();
    }
}

// Toggle friends modal
function toggleFriendsModal() {
    const modal = document.getElementById('friendsModal');
    modal.classList.toggle('hidden');
    if (!modal.classList.contains('hidden')) {
        loadFriends();
        loadFriendRequests();
    }
}

// Switch friends tab
function switchFriendsTab(tab) {
    currentFriendsTab = tab;
    const friendsTab = document.getElementById('friendsTab');
    const requestsTab = document.getElementById('requestsTab');
    const friendsList = document.getElementById('friendsList');
    const requestsList = document.getElementById('requestsList');

    if (tab === 'friends') {
        friendsTab.className = 'flex-1 px-4 py-2 text-sm font-medium bg-blue-500 text-white rounded-l-md';
        requestsTab.className = 'flex-1 px-4 py-2 text-sm font-medium bg-gray-200 text-gray-700 rounded-r-md';
        friendsList.classList.remove('hidden');
        requestsList.classList.add('hidden');
        loadFriends();
    } else {
        friendsTab.className = 'flex-1 px-4 py-2 text-sm font-medium bg-gray-200 text-gray-700 rounded-l-md';
        requestsTab.className = 'flex-1 px-4 py-2 text-sm font-medium bg-blue-500 text-white rounded-r-md';
        friendsList.classList.add('hidden');
        requestsList.classList.remove('hidden');
        loadFriendRequests();
    }
}

// Load friends for new chat (to check if users are already friends)
function loadFriendsForNewChat() {
    fetch('/get-friends/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        userFriends = data.friends || [];
    })
    .catch(error => {
        console.error('Error loading friends:', error);
        userFriends = [];
    });
}

// Load friends
function loadFriends() {
    fetch('/get-friends/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        displayFriends(data.friends || []);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('friendsList').innerHTML = '<p class="text-red-500 text-center py-4">Error loading friends</p>';
    });
}

// Display friends
function displayFriends(friends) {
    const friendsList = document.getElementById('friendsList');
    friendsList.innerHTML = '';
    
    if (friends.length === 0) {
        friendsList.innerHTML = '<p class="text-gray-500 text-center py-4">No friends yet</p>';
        return;
    }
    
    friends.forEach(friend => {
        const friendElement = document.createElement('div');
        friendElement.className = 'flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg';
        friendElement.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    <span class="text-white font-medium">${friend.name.charAt(0).toUpperCase()}</span>
                </div>
                <div>
                    <p class="font-medium text-gray-900">${friend.name}</p>
                    <p class="text-sm text-gray-500">${friend.email}</p>
                </div>
            </div>
            <button onclick="startChatWithFriend(${friend.id}, '${friend.name}')" 
                    class="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600">
                Chat
            </button>
        `;
        friendsList.appendChild(friendElement);
    });
}

// Load friend requests
function loadFriendRequests() {
    fetch('/get-friend-requests/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        displayFriendRequests(data.friend_requests || []);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('requestsList').innerHTML = '<p class="text-red-500 text-center py-4">Error loading requests</p>';
    });
}

// Display friend requests
function displayFriendRequests(requests) {
    const requestsList = document.getElementById('requestsList');
    requestsList.innerHTML = '';
    
    if (requests.length === 0) {
        requestsList.innerHTML = '<p class="text-gray-500 text-center py-4">No pending requests</p>';
        return;
    }
    
    requests.forEach(request => {
        const requestElement = document.createElement('div');
        requestElement.className = 'flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg';
        requestElement.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                    <span class="text-white font-medium">${request.requester.name.charAt(0).toUpperCase()}</span>
                </div>
                <div>
                    <p class="font-medium text-gray-900">${request.requester.name}</p>
                    <p class="text-sm text-gray-500">${request.requester.email}</p>
                </div>
            </div>
            <div class="flex space-x-2">
                <button onclick="acceptFriendRequest(${request.id}, '${request.requester.name}')" 
                        class="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600">
                    Accept
                </button>
                <button onclick="declineFriendRequest(${request.id})" 
                        class="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600">
                    Decline
                </button>
            </div>
        `;
        requestsList.appendChild(requestElement);
    });
}

// Accept friend request
function acceptFriendRequest(requestId, friendName) {
    fetch('/accept-friend-request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            friendship_id: requestId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showNotification(`Friend request from ${friendName} accepted!`, 'success');
            loadFriendRequests(); // Refresh requests
            loadFriends(); // Refresh friends list
        } else {
            showNotification(data.error || 'Failed to accept friend request', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

// Decline friend request
function declineFriendRequest(requestId) {
    // Implementation for declining friend request
    showNotification('Decline friend request functionality not implemented yet', 'info');
}

// Start chat with friend
function startChatWithFriend(friendId, friendName) {
    toggleFriendsModal();
    startChat(friendId, friendName);
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
    } text-white`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Filter chat list
function filterChats(query) {
    const chatItems = document.querySelectorAll('.chat-item');
    query = query.toLowerCase();
    
    chatItems.forEach(item => {
        const chatName = item.querySelector('.chat-name').textContent.toLowerCase();
        if (chatName.includes(query)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// Search users for new chat
function searchUsers(query) {
    if (!query.trim()) {
        document.getElementById('searchResults').innerHTML = '<p class="text-gray-500 text-center py-4">Start typing to search for users</p>';
        return;
    }

    fetch('/search-user/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            name: query
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.users) {
            displaySearchResults(data.users);
        } else {
            document.getElementById('searchResults').innerHTML = '<p class="text-red-500 text-center py-4">Error searching users</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('searchResults').innerHTML = '<p class="text-red-500 text-center py-4">Error searching users</p>';
    });
}

// Display search results with friendship status
function displaySearchResults(users) {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = '';
    
    if (users.length === 0) {
        resultsContainer.innerHTML = '<p class="text-gray-500 text-center py-4">No users found</p>';
        return;
    }
    
    users.forEach(user => {
        // Skip current user
        if (window.userData && user.id === window.userData.id) {
            return;
        }
        
        const userElement = document.createElement('div');
        userElement.className = 'flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg';
        
        // Check if already friends
        const isAlreadyFriend = userFriends.some(friend => friend.id === user.id);
        
        userElement.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    <span class="text-white font-medium">${user.name.charAt(0).toUpperCase()}</span>
                </div>
                <div>
                    <p class="font-medium text-gray-900">${user.name}</p>
                    <p class="text-sm text-gray-500">${user.email}</p>
                </div>
            </div>
            ${isAlreadyFriend ? 
                `<button onclick="startChat(${user.id}, '${user.name}')" 
                         class="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600">
                    Start Chat
                 </button>` :
                `<button onclick="addFriend(${user.id}, '${user.name}')" 
                         class="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600">
                    Add Friend
                 </button>`
            }
        `;
        resultsContainer.appendChild(userElement);
    });
}

// Add friend function
function addFriend(friendId, friendName) {
    fetch('/add-friend/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            friend_id: friendId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showNotification(`Friend request sent to ${friendName}!`, 'success');
            toggleNewChatModal();
        } else {
            showNotification(data.error || 'Failed to send friend request', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Start new chat (automatically creates ChatRoom if they're friends)
function startChat(userId, userName) {
    fetch('/start-chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.chat_room_id) {
            openChat(data.chat_room_id, userName);
            toggleNewChatModal();
            // Refresh chat list to show new chat
            setTimeout(() => {
                location.reload();
            }, 500);
        } else {
            showNotification(data.error || 'Failed to start chat', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

// Open chat
function openChat(chatId, chatName) {
    currentChatId = chatId;
    
    // Update chat header
    document.getElementById('chatTitle').textContent = chatName;
    document.getElementById('chatInitial').textContent = chatName.charAt(0).toUpperCase();
    document.getElementById('mobileChatTitle').textContent = chatName;
    
    // Show chat section
    const chatSection = document.getElementById('chatSection');
    const chatListSection = document.getElementById('chatListSection');
    const mobileChatHeader = document.getElementById('mobileChatHeader');
    
    if (isMobileView) {
        // Mobile PWA-like experience
        chatListSection.classList.add('mobile-hidden');
        mobileChatHeader.classList.remove('hidden');
        chatSection.classList.remove('hidden');
        chatSection.classList.add('mobile-fullscreen', 'chat-slide-in');
        
        // Remove animation class after animation completes
        setTimeout(() => {
            chatSection.classList.remove('chat-slide-in');
        }, 300);
    } else {
        // Desktop experience
        chatSection.classList.remove('hidden');
    }
    
    // Load messages
    loadMessages(chatId);
    
    // Connect WebSocket
    connectToChat(chatId);
}

// Connect to chat WebSocket
function connectToChat(chatId) {
    if (messageSocket) {
        messageSocket.close();
    }
    
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsPath = `${wsScheme}://${window.location.host}/ws/chat/${chatId}/`;
    
    messageSocket = new WebSocket(wsPath);
    
    messageSocket.onopen = function(e) {
        console.log('Chat WebSocket connected');
    };
    
    messageSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'message') {
            addMessageToUI(data);
        }
    };
    
    messageSocket.onclose = function(e) {
        console.log('Chat WebSocket closed');
    };
    
    messageSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };
}

// Load messages
function loadMessages(chatId) {
    fetch(`/get-messages/${chatId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.messages) {
            displayMessages(data.messages);
        } else {
            console.error('Error loading messages:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Display messages
function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    const noMessagesPlaceholder = document.getElementById('noMessagesPlaceholder');
    
    // Hide placeholder
    if (noMessagesPlaceholder) {
        noMessagesPlaceholder.style.display = 'none';
    }
    
    // Clear existing messages
    container.innerHTML = '';
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-2.72-.418l-3.134 1.256a.5.5 0 01-.633-.633l1.256-3.134A8.955 8.955 0 0112 4c4.418 0 8 3.582 8 8z"></path>
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No messages yet</h3>
                <p class="mt-1 text-sm text-gray-500">Send a message to start the conversation.</p>
            </div>
        `;
        return;
    }
    
    messages.forEach(message => {
        addMessageToUI(message, false);
    });
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Add message to UI
function addMessageToUI(messageData, shouldScroll = true) {
    const container = document.getElementById('messagesContainer');
    const isOwnMessage = window.userData && messageData.sender_id === window.userData.id;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${isOwnMessage ? 'justify-end' : 'justify-start'} mb-4`;
    
    const timestamp = new Date(messageData.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
    
    messageDiv.innerHTML = `
        <div class="max-w-xs lg:max-w-md px-4 py-2 ${
            isOwnMessage 
                ? 'bg-blue-600 text-white rounded-l-lg rounded-tr-lg' 
                : 'bg-gray-200 text-gray-800 rounded-r-lg rounded-tl-lg'
        }">
            ${!isOwnMessage ? `<p class="text-xs font-medium mb-1 opacity-75">${messageData.sender_name || messageData.username || 'Unknown'}</p>` : ''}
            <p class="text-sm">${messageData.content || messageData.message}</p>
            <div class="flex items-center justify-between mt-1">
                <p class="text-xs opacity-75">${timestamp}</p>
                ${isOwnMessage ? `
                    <div class="flex items-center space-x-1">
                        ${messageData.status === 'Delivered' ? `
                            <svg class="w-3 h-3 opacity-75" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                            </svg>
                        ` : messageData.status === 'Seen' ? `
                            <svg class="w-3 h-3 opacity-75" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                            </svg>
                            <svg class="w-3 h-3 opacity-75 -ml-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                            </svg>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    container.appendChild(messageDiv);
    
    if (shouldScroll) {
        container.scrollTop = container.scrollHeight;
    }
}

// Send message
function sendMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('messageText');
    const message = messageInput.value.trim();
    
    if (!message || !messageSocket || !currentChatId) return;
    
    messageSocket.send(JSON.stringify({
        'type': 'message',
        'message': message,
        'room_id': currentChatId
    }));
    
    // Add message to UI immediately
    addMessageToUI({
        content: message,
        sender_id: window.userData?.id,
        sender_name: window.userData?.username,
        timestamp: new Date().toISOString(),
        status: 'Pending'
    });
    
    messageInput.value = '';
    autoResizeTextarea(messageInput);
}

// Make functions available globally for onclick handlers
window.acceptFriendRequest = acceptFriendRequest;
window.declineFriendRequest = declineFriendRequest;
window.startChatWithFriend = startChatWithFriend;
window.addFriend = addFriend;
window.startChat = startChat;
