const App = {
    state: {
        user: null,
        token: null,
        chatHistory: [],
        patientContext: null
    },

    // --- NAVIGATION ---
    init() {
        // Check local storage for session? For demo, we start clean.
        console.log("App Initialized");
    },

    navigate(viewId) {
        document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
        document.getElementById(`view-${viewId}`).classList.add('active');
        
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        // Find nav item that calls this view
        const activeNav = document.querySelector(`.nav-item[onclick*="${viewId}"]`);
        if(activeNav) activeNav.classList.add('active');
    },

    // --- AUTH ---
    async login(role) {
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role})
            });
            
            if (!response.ok) throw new Error("Login failed");
            
            const data = await response.json();
            this.state.user = data.user;
            this.state.patientContext = data.patient; // Populated only if patient
            
            // Update UI
            document.getElementById('user-name').innerText = data.user.full_name;
            document.getElementById('user-role').innerText = role;
            document.getElementById('user-avatar').innerText = data.user.full_name.charAt(0);
            
            // Show Sidebar
            document.getElementById('sidebar').classList.remove('hidden');
            
            // Filter Nav Links
            document.querySelectorAll('.nav-item').forEach(el => {
                if(el.dataset.role === role.toLowerCase()) {
                    el.style.display = 'block';
                } else {
                    el.style.display = 'none';
                }
            });
            
            // Navigate to Home based on role
            if (role === 'Patient') {
                this.navigate('patient-chat');
            } else if (role === 'Doctor') {
                this.navigate('doctor-search');
            } else if (role === 'Admin') {
                this.navigate('admin-coding');
            }
            
            // Hide Login
            document.getElementById('view-login').classList.remove('active');
            
        } catch (e) {
            alert("Error logging in: " + e.message);
        }
    },

    logout() {
        this.state.user = null;
        this.state.chatHistory = [];
        document.getElementById('sidebar').classList.add('hidden');
        document.getElementById('view-login').classList.add('active');
        document.querySelectorAll('.view').forEach(el => {
            if(el.id !== 'view-login') el.classList.remove('active');
        });
    },

    // --- PATIENT CHAT ---
    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        // Add User Message to UI
        this.addMessageToUI('user', text);
        input.value = '';

        // API Call
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: text,
                    history: this.state.chatHistory,
                    patient_context: this.state.patientContext || {}
                })
            });

            const data = await response.json();
            
            // Update History
            this.state.chatHistory.push({role: 'user', content: text});
            this.state.chatHistory.push({role: 'model', content: data.response});
            
            // Add Model Message to UI
            this.addMessageToUI('model', data.response, data.is_emergency);

        } catch (e) {
            this.addMessageToUI('model', "Error: Could not reach Dr. AI.");
        }
    },

    addMessageToUI(role, text, isEmergency=false) {
        const container = document.getElementById('chat-history');
        const str = `
            <div class="message ${role} ${isEmergency ? 'emergency' : ''}">
                <div class="text">${text}</div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', str);
        container.scrollTop = container.scrollHeight;
    },

    // --- DOCTOR SEARCH ---
    async clinicalSearch() {
        const query = document.getElementById('doc-search-input').value;
        const container = document.getElementById('search-results');
        
        container.innerHTML = '<div class="glass-panel">Searching medical protocols... <i class="fa-solid fa-spinner fa-spin"></i></div>';
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    query: query,
                    patient_meds: "Metformin, Lisinopril" // Mock
                })
            });
            const data = await response.json();
            container.innerHTML = `<div class="glass-panel">${marked.parse(data.result)}</div>`; // Assume marked.js is loaded or just plain text
            
        } catch (e) {
            container.innerHTML = '<div class="glass-panel">Error searching protocols.</div>';
        }
    },

    // --- ADMIN CODING ---
    async generateCodes() {
        const note = document.getElementById('clinical-note').value;
        const container = document.getElementById('coding-results');
        
        container.innerHTML = 'Analyzing...';
        
        try {
            const response = await fetch('/api/coding', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({note})
            });
            const data = await response.json();
            
            let html = '';
            data.codes.forEach(code => {
                const color = code.confidence > 0.8 ? '#10B981' : '#F59E0B';
                html += `
                    <div style="padding: 10px; border-left: 4px solid ${color}; background: #f8fafc; margin-bottom: 8px;">
                        <strong>${code.code}</strong>: ${code.description}
                        <br><small>Confidence: ${Math.round(code.confidence * 100)}%</small>
                    </div>
                `;
            });
            container.innerHTML = html;
            
        } catch (e) {
            container.innerHTML = 'Error generating codes.';
        }
    }
};

// RX Upload Listener
const rxInput = document.getElementById('rx-upload');
if (rxInput) {
    rxInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if(!file) return;
        
        const output = document.getElementById('json-output');
        output.innerText = "Extracting data with Gemini Vision...";
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload_rx', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            output.innerText = JSON.stringify(data, null, 2);
        } catch (e) {
            output.innerText = "Error extracting data.";
        }
    });
}

// Init
App.init();
