const API_BASE = "http://127.0.0.1:8000";

let token = localStorage.getItem("token") || "";
let currentChatId = null;

/* ---------------- TOGGLE AUTH ---------------- */
function toggleAuth(form){
    document.getElementById("signup-form").style.display = form==='signup'?'block':'none';
    document.getElementById("login-form").style.display = form==='login'?'block':'none';
}

/* ---------------- SIGNUP ---------------- */
async function signup() {
    const email = document.getElementById("signup-email").value;
    const password = document.getElementById("signup-password").value;
    const btn = document.querySelector("#signup-form button");
    const msg = document.getElementById("auth-message");

    btn.disabled = true;
    msg.innerText = "Please wait...";

    try {
        const res = await fetch(`${API_BASE}/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (data.message) {
            msg.className = "message-text success";
            msg.innerText = "Signup successful! Please login.";
            toggleAuth("login");
        } else {
            msg.className = "message-text error";
            msg.innerText = data.detail || "Something went wrong!";
        }

    } catch (e) {
        msg.innerText = "Backend not reachable!";
        console.error(e);
    } finally {
        btn.disabled = false;
    }
}

/* ---------------- LOGIN ---------------- */
async function login() {
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const btn = document.querySelector("#login-form button");
    const msg = document.getElementById("auth-message");

    btn.disabled = true;
    msg.innerText = "Please wait...";

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (data.access_token) {
            token = data.access_token;
            localStorage.setItem("token", token);
            msg.innerText = "";
            showApp();
        } else {
            msg.innerText = data.detail || "Something went wrong!";
        }

    } catch (e) {
        msg.innerText = "Backend not reachable!";
        console.error(e);
    } finally {
        btn.disabled = false;
    }
}

/* ---------------- LOGOUT ---------------- */
function logout(){
    token="";
    localStorage.removeItem("token");
    document.getElementById("app-container").style.display="none";
    document.getElementById("auth-container").style.display="block";
}

/* ---------------- CREATE CHAT ---------------- */
async function createNewChat() {
    const res = await fetch(`${API_BASE}/chats`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await res.json();
    currentChatId = data.id;
    document.getElementById("chat-window").innerHTML = "";
    loadChats();
}

/* ---------------- SHOW APP ---------------- */
function showApp(){
    document.getElementById("auth-container").style.display="none";
    document.getElementById("app-container").style.display="block";
}

/* ---------------- UPLOAD PDF ---------------- */
async function uploadPDFs(){
    const files = document.getElementById("pdf-files").files;
    if(files.length === 0) return;

    const formData = new FormData();
    for(let f of files) formData.append("files", f);

    const btn = document.getElementById("upload-btn");
    const spinner = document.getElementById("upload-spinner");

    btn.disabled = true;
    spinner.style.display = "inline";

    try {
        const res = await fetch(`${API_BASE}/upload-multiple`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` },
            body: formData
        });

        const data = await res.json();
        document.getElementById("upload-message").innerText =
            data.message || data.detail || "Upload completed.";

    } catch(e) {
        alert("Backend not reachable!");
        console.error(e);
    } finally {
        btn.disabled = false;
        spinner.style.display = "none";
    }
}

/* ---------------- ASK QUESTION ---------------- */
async function askQuestion(){
    const question = document.getElementById("question-input").value;
    if(!question) return;

    if (!currentChatId) {
        await createNewChat();
    }

    addChatMessage("user", question);
    document.getElementById("question-input").value = "";

    const btn = document.getElementById("send-btn");
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                question,
                chat_id: currentChatId,
                word_limit: 120
            })
        });

        const data = await res.json();
        addChatMessage("bot", data.answer || "No response received.");
        loadChats();

    } catch(e) {
        alert("Backend not reachable!");
        console.error(e);
    } finally {
        btn.disabled = false;
    }
}

/* ---------------- ADD MESSAGE ---------------- */
function addChatMessage(sender, text){
    const chatWindow = document.getElementById("chat-window");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;

    sender === "bot"
        ? msgDiv.innerHTML = text
        : msgDiv.innerText = text;

    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

/* ---------------- LOAD CHATS ---------------- */
async function loadChats(){
    try {
        const res = await fetch(`${API_BASE}/chats`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        const chats = await res.json();
        const ul = document.getElementById("chat-history");
        ul.innerHTML = "";

        chats.forEach(chat => {
            const li = document.createElement("li");
            li.textContent = chat.title || "New Chat";
            li.onclick = () => openChat(chat.id);
            ul.appendChild(li);
        });

        ul.style.display = "block";

    } catch(e) {
        console.error("Failed to load chats", e);
    }
}

/* ---------------- OPEN CHAT ---------------- */
async function openChat(chatId){
    currentChatId = chatId;

    const res = await fetch(`${API_BASE}/chats/${chatId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const messages = await res.json();
    const chatWindow = document.getElementById("chat-window");
    chatWindow.innerHTML = "";

    messages.forEach(m => {
        addChatMessage(m.role === "user" ? "user" : "bot", m.content);
    });
}

/* ---------------- DELETE HISTORY ---------------- */
async function deleteHistory(){
    try {
        await fetch(`${API_BASE}/delete-chat-history`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });
        loadChats();
    } catch(e) {
        alert("Backend not reachable!");
        console.error(e);
    }
}
