// API Base URL
const API_BASE = 'http://localhost:5000/api';

// State
let currentUser = null;
let currentPage = 'feed';
let uploadType = 'post'; // 'post' or 'story'

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Auth forms
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    
    // Upload forms
    document.getElementById('uploadForm').addEventListener('submit', handleUpload);
    document.getElementById('faceRegForm').addEventListener('submit', handleFaceRegistration);
    
    // Image preview
    document.getElementById('imageInput').addEventListener('change', previewImage);
    document.getElementById('faceImageInput').addEventListener('change', previewFaceImage);
    
    // Poll for notifications
    setInterval(checkNotifications, 30000); // Check every 30 seconds
}

// Auth functions
function showLoginForm() {
    document.getElementById('loginForm').style.display = 'flex';
    document.getElementById('registerForm').style.display = 'none';
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
    document.querySelectorAll('.tab-btn')[1].classList.remove('active');
}

function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'flex';
    document.querySelectorAll('.tab-btn')[0].classList.remove('active');
    document.querySelectorAll('.tab-btn')[1].classList.add('active');
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            showMainApp();
        } else {
            document.getElementById('loginError').textContent = data.error;
        }
    } catch (error) {
        document.getElementById('loginError').textContent = 'Connection error';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const fullName = document.getElementById('registerFullName').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, full_name: fullName, password }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            showMainApp();
        } else {
            document.getElementById('registerError').textContent = data.error;
        }
    } catch (error) {
        document.getElementById('registerError').textContent = 'Connection error';
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        document.getElementById('authPage').style.display = 'block';
        document.getElementById('mainPage').style.display = 'none';
        document.getElementById('navbar').style.display = 'none';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data;
            showMainApp();
        } else {
            document.getElementById('authPage').style.display = 'block';
        }
    } catch (error) {
        document.getElementById('authPage').style.display = 'block';
    }
}

function showMainApp() {
    document.getElementById('authPage').style.display = 'none';
    document.getElementById('mainPage').style.display = 'block';
    document.getElementById('navbar').style.display = 'block';
    
    loadFeed();
    loadStories();
    checkNotifications();
}

// Feed functions
async function loadFeed() {
    try {
        const response = await fetch(`${API_BASE}/posts`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            displayFeed(data.posts);
        }
    } catch (error) {
        console.error('Error loading feed:', error);
    }
}

function displayFeed(posts) {
    const feedContainer = document.getElementById('feedContainer');
    feedContainer.innerHTML = '';
    
    if (posts.length === 0) {
        feedContainer.innerHTML = '<p style="text-align: center; color: #8e8e8e;">No posts yet</p>';
        return;
    }
    
    posts.forEach(post => {
        const postCard = createPostCard(post);
        feedContainer.appendChild(postCard);
    });
}

function createPostCard(post) {
    const card = document.createElement('div');
    card.className = 'post-card';
    
    const timeAgo = getTimeAgo(new Date(post.created_at));
    
    card.innerHTML = `
        <div class="post-header">
            <div class="post-avatar"></div>
            <div class="post-user-info">
                <div class="post-username">${post.username}</div>
                <div class="post-time">${timeAgo}</div>
            </div>
        </div>
        <img class="post-image" src="${API_BASE}${post.image_url}" alt="Post image">
        ${post.caption ? `<div class="post-caption"><strong>${post.username}</strong>${post.caption}</div>` : ''}
        ${post.face_count > 0 ? `<div class="face-approval-notice">🔒 ${post.face_count} face(s) detected. Waiting for approval to display.</div>` : ''}
    `;
    
    return card;
}

// Stories functions
async function loadStories() {
    try {
        const response = await fetch(`${API_BASE}/stories`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            displayStories(data.stories);
        }
    } catch (error) {
        console.error('Error loading stories:', error);
    }
}

function displayStories(stories) {
    const storiesContainer = document.getElementById('storiesContainer');
    
    // Keep the "Add Story" button
    const addStoryBtn = storiesContainer.querySelector('.add-story-btn');
    storiesContainer.innerHTML = '';
    storiesContainer.appendChild(addStoryBtn);
    
    stories.forEach(story => {
        if (!story.is_expired) {
            const storyItem = createStoryItem(story);
            storiesContainer.appendChild(storyItem);
        }
    });
}

function createStoryItem(story) {
    const item = document.createElement('div');
    item.className = 'story-item';
    item.onclick = () => viewStory(story.id);
    
    item.innerHTML = `
        <div class="story-avatar">
            <img src="${API_BASE}${story.image_url}" alt="${story.username}">
        </div>
        <span>${story.username}</span>
    `;
    
    return item;
}

function viewStory(storyId) {
    // Open story in modal or fullscreen
    alert('Story viewer - implement fullscreen story view');
}

// Upload functions
function showUploadModal(type) {
    uploadType = type;
    document.getElementById('uploadModalTitle').textContent = type === 'post' ? 'Create Post' : 'Create Story';
    document.getElementById('captionInput').style.display = type === 'post' ? 'block' : 'none';
    document.getElementById('uploadModal').style.display = 'block';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
    document.getElementById('uploadForm').reset();
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('uploadStatus').textContent = '';
}

function previewImage(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('imagePreview');
            preview.src = e.target.result;
            preview.style.display = 'block';
            document.querySelector('#imageUploadArea label').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
}

async function handleUpload(e) {
    e.preventDefault();
    
    const imageInput = document.getElementById('imageInput');
    const captionInput = document.getElementById('captionInput');
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!imageInput.files[0]) {
        statusDiv.textContent = 'Please select an image';
        statusDiv.className = 'upload-status error';
        return;
    }
    
    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
    
    if (uploadType === 'post') {
        formData.append('caption', captionInput.value);
    }
    
    statusDiv.textContent = 'Uploading and processing faces...';
    statusDiv.className = 'upload-status info';
    
    try {
        const endpoint = uploadType === 'post' ? '/posts' : '/stories';
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            statusDiv.textContent = `${uploadType === 'post' ? 'Post' : 'Story'} created! ${data.faces_detected} face(s) detected.`;
            statusDiv.className = 'upload-status success';
            
            setTimeout(() => {
                closeUploadModal();
                if (uploadType === 'post') {
                    loadFeed();
                } else {
                    loadStories();
                }
            }, 2000);
        } else {
            statusDiv.textContent = data.error || 'Upload failed';
            statusDiv.className = 'upload-status error';
        }
    } catch (error) {
        statusDiv.textContent = 'Connection error';
        statusDiv.className = 'upload-status error';
    }
}

// Notifications
async function checkNotifications() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_BASE}/notifications`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            const unreadCount = data.notifications.filter(n => !n.is_read).length;
            
            const badge = document.getElementById('notificationBadge');
            if (unreadCount > 0) {
                badge.textContent = unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error checking notifications:', error);
    }
}

async function showNotifications() {
    currentPage = 'notifications';
    document.getElementById('feedContainer').style.display = 'none';
    document.getElementById('profilePage').style.display = 'none';
    document.getElementById('notificationsPage').style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/notifications`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            displayNotifications(data.notifications);
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function displayNotifications(notifications) {
    const notificationsList = document.getElementById('notificationsList');
    notificationsList.innerHTML = '';
    
    if (notifications.length === 0) {
        notificationsList.innerHTML = '<p style="text-align: center; padding: 20px; color: #8e8e8e;">No notifications</p>';
        return;
    }
    
    notifications.forEach(notif => {
        const notifItem = createNotificationItem(notif);
        notificationsList.appendChild(notifItem);
    });
}

function createNotificationItem(notif) {
    const item = document.createElement('div');
    item.className = `notification-item ${!notif.is_read ? 'unread' : ''}`;
    
    const timeAgo = getTimeAgo(new Date(notif.created_at));
    
    item.innerHTML = `
        <div class="notification-icon">🔔</div>
        <div class="notification-content">
            <div class="notification-message">${notif.message}</div>
            <div class="notification-time">${timeAgo}</div>
        </div>
        ${notif.type === 'face_detected' ? `
            <div class="notification-actions">
                <button class="btn-secondary" onclick="showApprovals()">Review</button>
            </div>
        ` : ''}
    `;
    
    return item;
}

async function showApprovals() {
    try {
        const response = await fetch(`${API_BASE}/approvals/pending`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            displayApprovals(data.approvals);
            document.getElementById('approvalModal').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading approvals:', error);
    }
}

function displayApprovals(approvals) {
    const approvalsList = document.getElementById('approvalsList');
    approvalsList.innerHTML = '';
    
    if (approvals.length === 0) {
        approvalsList.innerHTML = '<p style="text-align: center; color: #8e8e8e;">No pending approvals</p>';
        return;
    }
    
    approvals.forEach(approval => {
        const approvalItem = createApprovalItem(approval);
        approvalsList.appendChild(approvalItem);
    });
}

function createApprovalItem(approval) {
    const item = document.createElement('div');
    item.className = 'approval-item';
    
    const imageUrl = approval.content_type === 'post' 
        ? `/api/posts/${approval.content_id}/image`
        : `/api/stories/${approval.content_id}/image`;
    
    item.innerHTML = `
        <img class="approval-preview" src="${API_BASE}${imageUrl}" alt="Content preview">
        <div class="approval-info">
            <strong>${approval.uploader.username}</strong> posted a ${approval.content_type} with your face
            <br><small>Posted ${getTimeAgo(new Date(approval.created_at))}</small>
        </div>
        <div class="approval-actions">
            <button class="btn-approve" onclick="handleApproval(${approval.id}, true)">Approve</button>
            <button class="btn-reject" onclick="handleApproval(${approval.id}, false)">Reject</button>
        </div>
    `;
    
    return item;
}

async function handleApproval(approvalId, isApprove) {
    const action = isApprove ? 'approve' : 'reject';
    
    try {
        const response = await fetch(`${API_BASE}/approvals/${approvalId}/${action}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            // Refresh approvals list
            showApprovals();
            // Reload feed to show updated images
            loadFeed();
        }
    } catch (error) {
        console.error('Error handling approval:', error);
    }
}

function closeApprovalModal() {
    document.getElementById('approvalModal').style.display = 'none';
}

// Profile functions
async function showProfile() {
    currentPage = 'profile';
    document.getElementById('feedContainer').style.display = 'none';
    document.getElementById('notificationsPage').style.display = 'none';
    document.getElementById('profilePage').style.display = 'block';
    
    document.getElementById('profileUsername').textContent = currentUser.username;
    document.getElementById('profileFullName').textContent = currentUser.full_name || currentUser.email;
    
    try {
        const response = await fetch(`${API_BASE}/users/${currentUser.id}/posts`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            const profilePosts = document.getElementById('profilePosts');
            profilePosts.innerHTML = '';
            
            data.posts.forEach(post => {
                const postCard = createPostCard(post);
                profilePosts.appendChild(postCard);
            });
        }
    } catch (error) {
        console.error('Error loading profile posts:', error);
    }
}

function showFeed() {
    currentPage = 'feed';
    document.getElementById('feedContainer').style.display = 'block';
    document.getElementById('notificationsPage').style.display = 'none';
    document.getElementById('profilePage').style.display = 'none';
    
    loadFeed();
}

// Face registration
function showFaceRegistrationModal() {
    document.getElementById('faceRegModal').style.display = 'block';
}

function closeFaceRegModal() {
    document.getElementById('faceRegModal').style.display = 'none';
    document.getElementById('faceRegForm').reset();
    document.getElementById('faceImagePreview').style.display = 'none';
}

function previewFaceImage(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('faceImagePreview');
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
}

async function handleFaceRegistration(e) {
    e.preventDefault();
    
    const imageInput = document.getElementById('faceImageInput');
    
    if (!imageInput.files[0]) {
        alert('Please select an image');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
    
    try {
        const response = await fetch(`${API_BASE}/users/register-face`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Face registered successfully! You will now be recognized in photos.');
            closeFaceRegModal();
        } else {
            alert(data.error || 'Face registration failed');
        }
    } catch (error) {
        alert('Connection error');
    }
}

// Utility functions
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + 'y';
    
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + 'mo';
    
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + 'd';
    
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + 'h';
    
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + 'm';
    
    return Math.floor(seconds) + 's';
}
