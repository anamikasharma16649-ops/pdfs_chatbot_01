const API_BASE = "http://127.0.0.1:8000";
let token = localStorage.getItem("token") || "";
let currentChatId = null;

// Load PDF database
let pdfDatabase = {};
try {
    pdfDatabase = JSON.parse(localStorage.getItem('pdfDatabase')) || {};
} catch(e) {
    pdfDatabase = {};
    console.error("Error loading PDF database:", e);
}

// ========== CACHE FOR CHATS ==========
let chatsCache = null;
let chatsCacheTime = null;
const CACHE_DURATION = 5000; // 5 seconds

// ========== API HELPER ==========
async function apiFetch(url, options = {}) {
    if (!token) throw new Error("No auth token");
    options.headers = { ...(options.headers || {}), "Authorization": `Bearer ${token}` };
    const res = await fetch(url, options);
    if (res.status === 401) {
        alert("Session expired. Please login again.");
        logout();
        throw new Error("Unauthorized");
    }
    return res;
}

// ========== AUTH FUNCTIONS ==========
function toggleAuth(form) {
    document.getElementById("signup-form").style.display = form === 'signup' ? 'block' : 'none';
    document.getElementById("login-form").style.display = form === 'login' ? 'block' : 'none';
}

async function signup() {
    const email = document.getElementById("signup-email").value;
    const password = document.getElementById("signup-password").value;
    const btn = document.querySelector("#signup-form button");
    const msg = document.getElementById("auth-message");
    btn.disabled = true;
    msg.innerText = "Creating your account...";
    try {
        const res = await fetch(`${API_BASE}/signup`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (data.message) {
            msg.className = "message-text success";
            msg.innerText = "Account created successfully! Please log in.";
            toggleAuth("login");
        } else {
            msg.className = "message-text error";
            msg.innerText = data.detail || "Something went wrong!";
        }
    } catch (e) {
        msg.innerText = "Backend not reachable!";
        console.error(e);
    } finally { btn.disabled = false; }
}

async function login() {
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const btn = document.querySelector("#login-form button");
    const msg = document.getElementById("auth-message");
    btn.disabled = true;
    msg.innerText = "Processing...";
    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (data.access_token) {
            token = data.access_token;
            localStorage.setItem("token", token);
            msg.innerText = "";
            showApp();
            loadChats(true); // Force refresh on login
        } else {
            msg.className = "message-text error";
            msg.innerText = "Invalid email or password";
        }
    } catch (e) {
        msg.innerText = "Backend not reachable!";
        console.error(e);
    } finally { btn.disabled = false; }
}

function logout() {
    token = "";
    currentChatId = null;
    localStorage.removeItem("token");
    localStorage.removeItem("chat_id");
    document.getElementById("app-container").style.display = "none";
    document.getElementById("auth-container").style.display = "flex";
}

// ========== CHAT FUNCTIONS ==========
async function createNewChat() {
    const res = await apiFetch(`${API_BASE}/chats`, { method: "POST" });
    const data = await res.json();
    currentChatId = data.id;
    localStorage.setItem("chat_id", currentChatId);
    document.getElementById("chat-window").innerHTML = `
        <div class="empty-chat">
            <h3>New Chat Started</h3>
            <p>Upload a PDF and ask questions to get instant AI answers.</p>
        </div>`;
    document.getElementById("sidebar").classList.remove("active");
    
    // Clear cache and load fresh
    chatsCache = null;
    loadChats(true);
}

// 🔥 OPTIMIZED LOAD CHATS
async function loadChats(forceRefresh = false) {
    try {
        // Use cache if available and not expired
        if (!forceRefresh && chatsCache && chatsCacheTime && (Date.now() - chatsCacheTime < CACHE_DURATION)) {
            renderChats(chatsCache);
            return;
        }
        
        const res = await apiFetch(`${API_BASE}/chats`);
        const chats = await res.json();
        
        // Update cache
        chatsCache = chats;
        chatsCacheTime = Date.now();
        
        renderChats(chats);
        
    } catch (e) { 
        console.error("Failed to load chats", e); 
    }
}

// 🔥 SEPARATE RENDERING FUNCTION
function renderChats(chats) {
    const ul = document.getElementById("chat-history");
    ul.innerHTML = "";
    
    chats.forEach(chat => {
        const li = document.createElement("li");
        li.className = "history-item";
        if (chat.id === currentChatId) {
            li.classList.add("active");
        }
        
        const span = document.createElement("span");
        span.className = "history-title";
        span.textContent = chat.title || "New Chat";
        span.dataset.chatId = chat.id;
        
        // Add PDF indicator if chat has PDFs
        if (pdfDatabase[chat.id] && pdfDatabase[chat.id].length > 0) {
            span.innerHTML += ' <span style="font-size:11px;">📄</span>';
        }
        
        span.onclick = () => openChat(chat.id);
        li.appendChild(span);
        
        // Add individual delete button
        const deleteBtn = document.createElement("button");
        deleteBtn.className = "delete-chat-btn";
        deleteBtn.innerHTML = "✕";
        deleteBtn.onclick = (e) => deleteSingleChat(chat.id, e);
        li.appendChild(deleteBtn);
        
        ul.appendChild(li);
    });
    
    ul.style.display = "block";
}

// Display PDFs for current chat
function displayChatPDFs() {
    const container = document.getElementById('chat-pdfs-container');
    const pdfList = document.getElementById('chat-pdfs-list');
    
    if (!container || !pdfList) return;
    
    if (!currentChatId || !pdfDatabase[currentChatId] || pdfDatabase[currentChatId].length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    pdfList.innerHTML = '';
    
    const pdfs = pdfDatabase[currentChatId].sort((a, b) => 
        new Date(b.uploadedAt) - new Date(a.uploadedAt)
    );
    
    pdfs.forEach(pdf => {
        const li = document.createElement("li");
        li.className = "pdf-item";
        
        const date = new Date(pdf.uploadedAt).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        li.innerHTML = `
            <span class="pdf-name">📄 ${pdf.name}</span>
            <span class="pdf-date">${date}</span>
        `;
        
        li.onclick = () => {
            addChatMessage("bot", `📄 **${pdf.name}**\n_Uploaded on ${date}_`);
        };
        
        pdfList.appendChild(li);
    });
}

// 🔥 OPTIMIZED OPEN CHAT
async function openChat(chatId) {
    // Don't reload if same chat
    if (currentChatId === chatId) {
        document.getElementById("sidebar").classList.remove("active");
        return;
    }
    
    currentChatId = chatId;
    localStorage.setItem("chat_id", chatId);
    document.getElementById("sidebar").classList.remove("active");
    
    // Update active class immediately
    document.querySelectorAll(".history-item").forEach(item => {
        item.classList.remove("active");
    });
    
    const activeItem = document.querySelector(`.history-title[data-chat-id="${chatId}"]`);
    if (activeItem) {
        activeItem.parentElement.classList.add("active");
    }
    
    // Show loading indicator
    document.getElementById("chat-window").innerHTML = `
        <div class="empty-chat">
            <h3>⏳ Loading chat...</h3>
        </div>`;

    try {
        const res = await apiFetch(`${API_BASE}/chats/${chatId}`);
        const messages = await res.json();
        const chatWindow = document.getElementById("chat-window");
        chatWindow.innerHTML = "";
        
        messages.forEach(m => {
            const msgDiv = document.createElement("div");
            msgDiv.className = `message ${m.role === "user" ? "user" : "bot"}`;
            msgDiv.innerHTML = m.content.replace(/\n/g, "<br>");
            chatWindow.appendChild(msgDiv);
        });
        
        chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
        
        // Show PDFs for this chat
        displayChatPDFs();
        
    } catch (e) {
        console.error("Failed to load chat:", e);
        document.getElementById("chat-window").innerHTML = `
            <div class="empty-chat">
                <h3>❌ Failed to load chat</h3>
                <p>Please try again.</p>
            </div>`;
    }
}

// 🔥 OPTIMIZED INDIVIDUAL CHAT DELETE
async function deleteSingleChat(chatId, event) {
    event.stopPropagation();
    
    if (!confirm('Delete this chat? This will also delete its PDFs.')) return;
    
    // Immediately remove from UI
    const chatItem = event.target.closest('.history-item');
    if (chatItem) {
        chatItem.style.opacity = '0.5';
        chatItem.style.pointerEvents = 'none';
    }
    
    // Update local database immediately
    delete pdfDatabase[chatId];
    localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));
    
    // If current chat is deleted, clear chat window
    if (currentChatId === chatId) {
        currentChatId = null;
        localStorage.removeItem("chat_id");
        document.getElementById("chat-window").innerHTML = `
            <div class="empty-chat">
                <h3>📄 Upload a PDF to start chatting</h3>
                <p>Ask questions and get instant AI answers from your document.</p>
            </div>`;
        document.getElementById('chat-pdfs-container').style.display = 'none';
    }
    
    // Remove from UI immediately
    if (chatItem) {
        chatItem.remove();
    }
    
    // Clear cache so next load will be fresh
    chatsCache = null;
    
    // Background API call
    try {
        await apiFetch(`${API_BASE}/chats/${chatId}`, { 
            method: "DELETE" 
        });
        console.log(`✅ Chat ${chatId} deleted from backend`);
    } catch (e) {
        console.error("Background delete failed, will retry:", e);
        // If fails, reload chats to sync
        setTimeout(() => loadChats(true), 2000);
    }
}

// 🔥 OPTIMIZED DELETE ALL CHATS
async function deleteHistory() {
    if (!confirm('Delete ALL chats? This will also delete associated PDFs.')) return;
    
    // Clear UI immediately
    document.getElementById("chat-history").innerHTML = '';
    document.getElementById("chat-window").innerHTML = `
        <div class="empty-chat">
            <h3>📄 Upload a PDF to start chatting</h3>
            <p>Ask questions and get instant AI answers from your document.</p>
        </div>`;
    document.getElementById('chat-pdfs-container').style.display = 'none';
    
    // Clear local data immediately
    pdfDatabase = {};
    localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));
    currentChatId = null;
    localStorage.removeItem("chat_id");
    
    // Clear cache
    chatsCache = null;
    
    // Background API call
    try {
        await apiFetch(`${API_BASE}/delete-chat-history`, { method: "DELETE" });
        console.log("✅ All chats deleted from backend");
    } catch (e) {
        console.error("Background delete failed:", e);
        setTimeout(() => loadChats(true), 2000);
    }
}

// ========== PDF FUNCTIONS ==========
async function uploadPDFs() {
    const files = document.getElementById("pdf-files").files;
    const status = document.getElementById("uploadStatus");
    document.getElementById("question-input").disabled = true;

    status.style.display = "block";
    status.innerHTML = "⏳ Uploading...";

    if (!files || files.length === 0) {
        alert("Please select PDF files first.");
        return;
    }

    const formData = new FormData();
    for (let f of files) formData.append("files", f);

    try {
        const res = await apiFetch(`${API_BASE}/upload-multiple`, {
            method: "POST", body: formData
        });

        const data = await res.json();
        if (res.ok) {
            currentChatId = data.chat_id;
            localStorage.setItem("chat_id", currentChatId);
            
            // Save PDFs to database
            if (!pdfDatabase[currentChatId]) pdfDatabase[currentChatId] = [];
            for (let file of files) {
                pdfDatabase[currentChatId].push({
                    name: file.name,
                    uploadedAt: new Date().toISOString()
                });
            }
            localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));

            // Professional upload message
            const pdfCount = files.length;
            const pdfText = pdfCount === 1 ? 'PDF' : 'PDFs';
            addChatMessage("bot", `✅ **${pdfCount} ${pdfText} uploaded successfully!**`);
            
            status.innerHTML = "✅ Upload complete!";
            setTimeout(() => status.style.display = "none", 3000);

            // Show PDFs for this chat
            displayChatPDFs();
            
            // Clear cache and reload chats
            chatsCache = null;
            await loadChats(true);
        } else {
            alert("Upload failed: " + (data.detail || "Unknown error"));
        }
    } catch (e) {
        alert("Backend not reachable!");
        console.error(e);
    } finally {
        document.getElementById("question-input").disabled = false;
        document.getElementById("pdf-files").value = "";
    }
}

// ========== MESSAGE FUNCTIONS ==========
async function askQuestion() {
    if (!token) { alert("Please login first"); return; }
    const question = document.getElementById("question-input").value.trim();
    if (!question) return;
    if (!currentChatId) { alert("Please upload PDF first."); return; }

    addChatMessage("user", question);
    showTyping();
    
    // Format chat title
    const rawTitle = question.slice(0, 40);
    const formattedTitle = rawTitle.charAt(0).toUpperCase() + rawTitle.slice(1).replace(/\.$/, '');
    
    document.querySelectorAll(".history-title").forEach(el => {
        if (el.dataset.chatId === currentChatId) el.textContent = formattedTitle;
    });
    
    document.getElementById("question-input").value = "";
    const btn = document.getElementById("send-btn");
    btn.disabled = true;

    try {
        const res = await apiFetch(`${API_BASE}/ask`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, chat_id: currentChatId })
        });
        const data = await res.json();
        removeTyping();
        
        let reply = data.answer ? data.answer.trim() : "No response received.";
        const msgDiv = document.createElement("div");
        msgDiv.className = "message bot";
        document.getElementById("chat-window").appendChild(msgDiv);
        typeWriter(msgDiv, reply);
        
        // Clear cache to refresh chat list (title might have changed)
        chatsCache = null;
        
    } catch (e) {
        alert("Backend not reachable!");
        console.error(e);
    } finally { btn.disabled = false; }
}

function addChatMessage(sender, text) {
    const chatWindow = document.getElementById("chat-window");
    const empty = document.querySelector(".empty-chat");
    if (empty) empty.remove();
    
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;
    chatWindow.appendChild(msgDiv);
    
    if (sender === "bot") typeWriter(msgDiv, text);
    else msgDiv.textContent = text;
    
    chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
}

function showTyping() {
    const typing = document.createElement("div");
    typing.className = "message bot typing";
    typing.id = "typing-indicator";
    typing.innerHTML = "Typing...";
    document.getElementById("chat-window").appendChild(typing);
    typing.scrollIntoView({ behavior: "smooth" });
}

function removeTyping() {
    const typing = document.getElementById("typing-indicator");
    if (typing) typing.remove();
}

function typeWriter(element, text, speed = 10) {
    element.innerHTML = "";
    const parts = text.split(/<br\s*\/?>/);
    let i = 0;
    function typing() {
        if (i < parts.length) {
            element.innerHTML += parts[i] + "<br>";
            i++;
            element.scrollIntoView({ behavior: "smooth", block: "nearest" });
            setTimeout(typing, speed);
        }
    }
    typing();
}

function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
}

// ========== UI FUNCTIONS ==========
function showApp() {
    document.getElementById("auth-container").style.display = "none";
    document.getElementById("app-container").style.display = "block";
    document.getElementById("uploadStatus").style.display = "none";
    
    // Show PDFs if chat is selected
    if (currentChatId) {
        displayChatPDFs();
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("active");
    if (sidebar.classList.contains("active")) loadChats();
}

function toggleSection(section) {
    const chatsSection = document.getElementById('chats-section');
    const chatsIcon = document.getElementById('chats-icon');
    
    chatsSection.classList.toggle('collapsed');
    chatsIcon.textContent = chatsSection.classList.contains('collapsed') ? '▶' : '▼';
}

// ========== INIT ==========
window.addEventListener("DOMContentLoaded", async () => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
        document.getElementById("auth-container").style.display = "block";
        document.getElementById("app-container").style.display = "none";
        return;
    }
    token = storedToken;
    try {
        const res = await fetch(`${API_BASE}/chats`, { headers: { "Authorization": `Bearer ${token}` } });
        if (res.status === 401) logout();
        else {
            showApp();
            loadChats(true); // Force fresh load on init
        }
    } catch (e) { logout(); }
    document.getElementById("question-input")?.focus();
});