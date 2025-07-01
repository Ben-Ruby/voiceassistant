let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let isAwake = false;
let currentAudio = null;

const micButton = document.getElementById('micButton');
const robotAvatar = document.getElementById('robotAvatar');
const statusText = document.getElementById('statusText');
const chatMessages = document.getElementById('chatMessages');
const clearBtn = document.getElementById('clearBtn');
const voiceBtns = document.querySelectorAll('.voice-btn');
const voiceTypes = [
  { key: 'zhixiaobai', label: '知小白' },
  { key: 'zhifeng_emo', label: '知锋（多情感）' },
  { key: 'xiaogang', label: '小刚' },
  { key: 'aimei', label: '艾美' }
];

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    setupEventListeners();
    loadChatHistory();
});

// 初始化WebSocket连接
function initializeSocket() {
    socket = io();

    socket.on('connect', function() {
        addSystemMessage('已连接到服务器');
    });

    socket.on('audio_response', function(data) {
        console.log('收到AI回复', data);
        if (data.audio_base64) {
            playAudio(data.audio_base64);
        }
        if (data.ai_response) addMessage(data.ai_response, 'assistant');
        if (data.user_question) addMessage(data.user_question, 'user');
        if (data.text) addSystemMessage(data.text);
    });

    socket.on('status', function(data) {
        handleStatusUpdate(data);
    });

    socket.on('error', function(data) {
        addErrorMessage(data.error);
    });
}

// 设置事件监听器
function setupEventListeners() {
    micButton.addEventListener('click', function() {
        console.log('点击了话筒按钮');
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    clearBtn.addEventListener('click', function() {
        clearChatHistory();
    });

    voiceBtns.forEach((btn, idx) => {
        btn.textContent = voiceTypes[idx].label;
        btn.dataset.voice = voiceTypes[idx].key;
        btn.addEventListener('click', function() {
            const voiceType = this.dataset.voice;
            setVoiceType(voiceType);
            voiceBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// 开始录音
async function startRecording() {
    try {
        console.log('开始录音');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        audioChunks = [];

        mediaRecorder.ondataavailable = function(event) {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = function() {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            sendAudioToServer(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        micButton.classList.add('recording');
        micButton.textContent = '⏹️';
        statusText.textContent = '正在录音...';
    } catch (error) {
        console.error('录音失败:', error);
        addErrorMessage('无法访问麦克风，请检查权限设置');
    }
}

// 停止录音
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        micButton.classList.remove('recording');
        micButton.textContent = '🎤';
        statusText.textContent = isAwake ? '正在处理...' : '点击话筒或说"小鹅"唤醒我';
    }
}

// 发送音频到服务器
function sendAudioToServer(audioBlob) {
    console.log('准备上传音频', audioBlob);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    fetch('/api/audio', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('后端返回：', data);
        if (data.audio_base64) {
            playAudio(data.audio_base64);
        }
        if (data.user_question) addMessage(data.user_question, 'user');
        if (data.ai_response) addMessage(data.ai_response, 'assistant');
        if (data.text) addSystemMessage(data.text);
    })
    .catch(error => {
        console.error('发送音频失败:', error);
        addErrorMessage('网络错误，请重试');
    });
}

// 播放base64音频
function playAudio(audioBase64) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
    currentAudio = audio;
    audio.play().catch(error => {
        console.error('播放音频失败:', error);
    });
    audio.onended = function() {
        currentAudio = null;
    };
}

// 聊天消息显示
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 系统消息显示
function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 错误消息显示
function addErrorMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.style.background = '#f8d7da';
    messageDiv.style.borderColor = '#f5c6cb';
    messageDiv.style.color = '#721c24';
    messageDiv.textContent = `错误: ${content}`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 清空聊天历史
function clearChatHistory() {
    fetch('/api/clear_history', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            chatMessages.innerHTML = '<div class="system-message">对话历史已清空</div>';
            addSystemMessage('欢迎使用小鹅语音助手！点击左侧话筒或说"小鹅"开始对话。');
        } else {
            addErrorMessage(data.error);
        }
    })
    .catch(error => {
        addErrorMessage('清空历史失败');
    });
}

// 加载聊天历史
function loadChatHistory() {
    fetch('/api/history')
    .then(response => response.json())
    .then(data => {
        if (data.success && data.data.length > 0) {
            data.data.forEach(conv => {
                addMessage(conv.question, 'user');
                addMessage(conv.response, 'assistant');
            });
        }
    })
    .catch(error => {
        // 忽略加载历史失败
    });
}

function handleStatusUpdate(data) {
    // 兼容后端推送的状态消息
    if (data && data.text) {
        addSystemMessage(data.text);
    }
}

function setVoiceType(voiceType) {
    fetch('/api/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_type: voiceType })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addSystemMessage(data.message);
        } else {
            addErrorMessage(data.error || '切换声音失败');
        }
    })
    .catch(() => {
        addErrorMessage('切换声音失败');
    });
}