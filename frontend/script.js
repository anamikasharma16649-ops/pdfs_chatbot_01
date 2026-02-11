let token = localStorage.getItem("token") || "";

// Toggle between Signup/Login
function toggleAuth(form){
    document.getElementById("signup-form").style.display = form==='signup'?'block':'none';
    document.getElementById("login-form").style.display = form==='login'?'block':'none';
}

// ------------------- SIGNUP -------------------
async function signup() {
    const email = document.getElementById("signup-email").value;
    const password = document.getElementById("signup-password").value;
    const btn = document.querySelector("#signup-form button"); ////////
    const msg = document.getElementById("auth-message");  /////////

    btn.disabled = true;               // button disable  ////////
    msg.innerText = "Please wait...";  // loader message/////////////

    try {
        const res = await fetch("http://127.0.0.1:8000/signup", {
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
            msg.innerText = data.detail;
        }

    } catch (e) {
        msg.innerText = "Backend not reachable!";
        console.error(e);
    } finally {
        btn.disabled = false; // button enable again
    }
}

// ------------------- LOGIN -------------------
async function login() {
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
     const btn = document.querySelector("#login-form button");
    const msg = document.getElementById("auth-message");

    btn.disabled = true;
    msg.innerText = "Please wait...";
    try {
        const res = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (data.access_token) {
            token = data.access_token;
            localStorage.setItem("token", token);
            showApp();
        } else {
            msg.innerText = data.detail;
        }
    } catch (e) {
        msg.innerText = "Backend not reachable!";
        console.error(e);
    } finally {
        btn.disabled = false;
    }
}

// ------------------- LOGOUT -------------------
function logout(){
    token="";
    localStorage.removeItem("token");
    document.getElementById("app-container").style.display="none";
    document.getElementById("auth-container").style.display="block";
}

// ------------------- SHOW APP -------------------
function showApp(){
    document.getElementById("auth-container").style.display="none";
    document.getElementById("app-container").style.display="block";
}

// ------------------- PDF UPLOAD -------------------
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
        const res = await fetch("http://127.0.0.1:8000/upload-multiple", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` },
            body: formData
        });
        const data = await res.json();
        document.getElementById("upload-message").innerText = data.message || data.detail;
    } catch(e) {
        alert("Backend not reachable!");
        console.error(e);
    } finally {
        btn.disabled = false;
        spinner.style.display = "none";
    }
}

// ------------------- ASK QUESTION -------------------
async function askQuestion(){
    const question = document.getElementById("question-input").value;
    if(!question) return;

    addChatMessage("user", question);
    document.getElementById("question-input").value = "";

    const btn = document.getElementById("send-btn");
    btn.disabled = true;

    try {
        const res = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        addChatMessage("bot", data.answer);
        loadHistory();
    } catch(e) {
        alert("Backend not reachable!");
        console.error(e);
    } finally {
        btn.disabled = false;
    }
}

// ------------------- ADD MESSAGE -------------------
function addChatMessage(sender, text){
    const chatWindow = document.getElementById("chat-window");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;

    if(sender === "bot"){
        msgDiv.innerHTML = text; // Bot messages me formatting allow
    } else {
        msgDiv.innerText = text; // User messages plain text
    }

    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ------------------- LOAD CHAT HISTORY -------------------
async function loadHistory(){
    try {
        const res = await fetch("http://127.0.0.1:8000/chat-history", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        const ul = document.getElementById("chat-history");
        ul.innerHTML = "";
        data.forEach(chat => {
            const li = document.createElement("li");
            // li.innerHTML = `<b>Q:</b> ${chat.question} → <b>A:</b> ${chat.answer}`; // HTML formatting
            li.textContent = `Q: ${chat.question} → A: ${chat.answer}`;
            ul.appendChild(li);
        });
    } catch(e) {
        console.error("Failed to load chat history", e);
    }
}
// ------------------- TOGGLE CHAT HISTORY -------------------
function toggleHistory(){
    const ul = document.getElementById("chat-history");

    if (ul.style.display === "none" || ul.style.display === "") {
        ul.style.display = "block";
        loadHistory();   // history tabhi load hogi jab user click kare
    } else {
        ul.style.display = "none";
    }
}


// ------------------- DELETE CHAT HISTORY -------------------
async function deleteHistory(){
    try {
        await fetch("http://127.0.0.1:8000/delete-chat-history", {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });
        loadHistory();
    } catch(e) {
        alert("Backend not reachable!");
        console.error(e);
    }
}
