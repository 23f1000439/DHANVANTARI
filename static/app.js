// --- CONFIG & STATE ---
const API_URL = "/api/agent/query";
let CURRENT_ROLE = "patient";
let EDGE_MODE = true; // Default to Edge ON
let CONVERSATION_ID = Date.now();

// --- TILE DEFINITIONS (Dhanvantari Context) ---
const tiles = [
    {
        id: 'triage',
        title: 'Virtual Triage',
        size: 'wide', // 2x1
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
        gradient: 'from-blue-600 to-indigo-600',
        front: { title: 'Symptom Check', subtitle: 'Tap to start assessment', extra: 'AI Ready' },
        back: { title: 'Actions', options: ['Report Fever', 'Check Cough', 'View History'] },
        role: 'patient'
    },
    {
        id: 'vitals',
        title: 'My Vitals',
        size: 'small', // 1x1
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>',
        gradient: 'from-rose-500 to-pink-600',
        front: { title: '98%', subtitle: 'SpO2' },
        back: { title: 'Heart Rate', subtitle: '72 bpm' }, // Simple text for back
        role: 'patient'
    },
    {
        id: 'meds',
        title: 'Medications',
        size: 'small',
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>',
        gradient: 'from-emerald-500 to-teal-600',
        front: { title: 'Metformin', subtitle: '500mg • 8:00 AM' },
        back: { title: 'Adherence', subtitle: '95% this week' },
        role: 'patient'
    },
    {
        id: 'appointments',
        title: 'Appointments',
        size: 'medium', // 2x1 (same as wide in this grid system)
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
        gradient: 'from-purple-600 to-violet-600',
        front: { title: 'Dr. Sharma', subtitle: 'Tomorrow, 10:00 AM', extra: 'Video Call' },
        back: { title: 'Actions', options: ['Join Call', 'Reschedule'] },
        role: 'patient'
    },
    // Doctor Tiles
    {
        id: 'patients-list',
        title: 'Patient List',
        size: 'wide',
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>',
        gradient: 'from-cyan-600 to-blue-700',
        front: { title: '12 Patients', subtitle: '3 Waiting for Review' },
        back: { title: 'Triage', subtitle: 'High Priority: 2' },
        role: 'doctor'
    },
    {
        id: 'protocols',
        title: 'Protocols',
        size: 'medium',
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>',
        gradient: 'from-slate-600 to-slate-800',
        front: { title: 'Treatment Guidelines', subtitle: 'Search Protocols' },
        back: { title: 'Recent', options: ['Diabetes Type 2', 'Hypertension'] },
        role: 'doctor'
    }
];

// --- RENDER ENGINE ---

function getSizeClasses(size) {
    if (size === 'wide' || size === 'medium') return 'col-span-2 row-span-1';
    return 'col-span-1 row-span-1';
}

function renderTiles() {
    const grid = document.getElementById('tilesGrid');
    grid.innerHTML = '';

    // Filter tiles by role
    const visibleTiles = tiles.filter(t => t.role === CURRENT_ROLE || !t.role);

    visibleTiles.forEach((tile, index) => {
        const el = document.createElement('div');
        el.className = `tile ${getSizeClasses(tile.size)} tile-animate`;
        el.style.animationDelay = `${index * 0.1}s`;

        // Front Content
        const frontHTML = `
            <div class="h-full flex flex-col justify-between p-4 relative z-10">
                <div class="flex justify-between items-start">
                    <div class="text-white/80 opacity-70 scale-90">${tile.icon}</div>
                    ${tile.gradient.includes('rose') ? '<div class="w-2 h-2 bg-white rounded-full animate-ping"></div>' : ''}
                </div>
                <div class="tile-cycle">
                    <p class="text-xl font-bold leading-none text-white drop-shadow-md">${tile.front.title}</p>
                    <p class="text-xs text-white/70 mt-1">${tile.front.subtitle}</p>
                    ${tile.front.extra ? `<span class="text-[10px] bg-white/20 px-1.5 py-0.5 rounded mt-2 inline-block">${tile.front.extra}</span>` : ''}
                </div>
            </div>
        `;

        // Back Content
        let backHTML = '';
        if (tile.back.options) {
            backHTML = `
                <div class="h-full flex flex-col p-4 relative z-10">
                    <p class="text-xs font-semibold uppercase opacity-60 mb-2">${tile.back.title}</p>
                    <div class="flex flex-col gap-2">
                        ${tile.back.options.map(opt => `<button class="text-left text-[10px] bg-white/10 hover:bg-white/20 rounded px-2 py-1 transition">${opt}</button>`).join('')}
                    </div>
                </div>
            `;
        } else {
            backHTML = `
                <div class="h-full flex flex-col justify-center items-center p-4 text-center relative z-10">
                    <p class="text-xs font-semibold uppercase opacity-60 mb-1">${tile.back.title}</p>
                    <p class="text-lg font-bold">${tile.back.subtitle}</p>
                </div>
            `;
        }

        el.innerHTML = `
            <div class="tile-inner h-full">
                <div class="tile-face tile-front bg-gradient-to-br ${tile.gradient}">
                    ${frontHTML}
                </div>
                <div class="tile-face tile-back bg-slate-900 border border-white/10">
                    ${backHTML}
                </div>
            </div>
        `;

        // Interactions
        el.addEventListener('click', (e) => {
            // If clicking a button inside back face, don't flip
            if (e.target.tagName === 'BUTTON') {
                openChat(tile.title, `I selected "${e.target.innerText}" from ${tile.title}.`);
                return;
            }
            // Flip logic or Open Chat
            if (tile.id === 'triage' || tile.id === 'protocols') {
                // Open Chat directly for interactive tiles
                openChat(tile.title);
            } else {
                el.classList.toggle('flipped');
            }
        });

        grid.appendChild(el);
    });
}

// --- CHAT & API LOGIC ---

const chatPanel = document.getElementById('miniChat');
const chatInput = document.getElementById('chatInput');
const chatMsgs = document.getElementById('chatMessages');
const overlay = document.getElementById('overlay');

function openChat(context = "General", initialQuery = "") {
    document.getElementById('chatTitle').innerText = context;
    document.getElementById('chatContext').innerText = `AI Agent Active (${CURRENT_ROLE})`;
    chatPanel.classList.add('mini-chat-open');
    overlay.style.opacity = '1';
    overlay.style.pointerEvents = 'auto';

    if (initialQuery) {
        // Auto send if triggered by action
        sendUserMessage(initialQuery);
    } else {
        chatInput.focus();
    }
}

function closeChat() {
    chatPanel.classList.remove('mini-chat-open');
    overlay.style.opacity = '0';
    overlay.style.pointerEvents = 'none';
}

document.getElementById('closeChatBtn').addEventListener('click', closeChat);
overlay.addEventListener('click', closeChat);
document.getElementById('aiAssistBtn').addEventListener('click', () => openChat());

// Sending Messages
async function sendUserMessage(text = "") {
    const query = text || chatInput.value.trim();
    if (!query) return;

    // UI
    addMessage(query, 'user');
    chatInput.value = "";

    // API Call
    addMessage("Thinking...", 'ai', true); // Temp loading msg

    const payload = {
        query: query,
        role: CURRENT_ROLE,
        conversation_id: CONVERSATION_ID,
        device: {
            has_local_model: EDGE_MODE,
            battery_level: 85
        }
    };

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        // Remove loading
        chatMsgs.lastElementChild.remove();

        // Formatting
        let responseText = data.response || "No response.";
        if (data.delegated) responseText = `[⚡ Edge AI]: ${data.instruction}`;

        addMessage(responseText, 'ai');

    } catch (e) {
        console.error(e);
        chatMsgs.lastElementChild.remove();
        addMessage("⚠️ Connection Error. Ensure backend is running.", 'ai');
    }
}

function addMessage(text, type, isTemp = false) {
    const div = document.createElement('div');
    div.className = `msg-row ${type === 'user' ? 'user-row' : ''}`;
    div.innerHTML = `<div class="msg-bubble-${type} ${isTemp ? 'animate-pulse' : ''}">${text}</div>`;
    chatMsgs.appendChild(div);
    chatMsgs.scrollTop = chatMsgs.scrollHeight;
}

document.getElementById('sendBtn').addEventListener('click', () => sendUserMessage());
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendUserMessage();
});


// --- GLOBAL UTILS ---
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    document.getElementById('currentDate').innerText = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

function setRole(role) {
    CURRENT_ROLE = role;
    renderTiles(); // Re-render tiles for new role
    // Visual feedback on role change can be added here
}

document.getElementById('edgeToggle').addEventListener('click', () => {
    EDGE_MODE = !EDGE_MODE;
    document.getElementById('edgeState').innerText = EDGE_MODE ? "ON" : "OFF";
    document.getElementById('edgeState').style.color = EDGE_MODE ? "#4ade80" : "#ef4444";
});

// Init
setInterval(updateTime, 1000);
updateTime();
renderTiles();
