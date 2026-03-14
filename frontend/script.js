

// const API_BASE = "http://127.0.0.1:8000";
// let token = localStorage.getItem("token") || "";
// let currentChatId = null;
// let pdfDatabase = {};

// // ========== UPLOAD TRACKING VARIABLES ==========
// let uploadTime = null;
// let uploadFileSize = 0;
// let isProcessingLargePDF = false;
// let processingStartTime = null;

// try {
//     pdfDatabase = JSON.parse(localStorage.getItem('pdfDatabase')) || {};
// } catch(e) {
//     pdfDatabase = {};
//     console.error("Error loading PDF database:", e);
// }

// let chatsCache = null;
// let chatsCacheTime = null;
// const CACHE_DURATION = 5000; 

// // ========== API FETCH WITH AUTH ==========
// async function apiFetch(url, options = {}) {
//     if (!token) throw new Error("No auth token");
//     options.headers = { ...(options.headers || {}), "Authorization": `Bearer ${token}` };
//     const res = await fetch(url, options);
//     if (res.status === 401) {
//         alert("Session expired. Please login again.");
//         logout();
//         throw new Error("Unauthorized");
//     }
//     return res;
// }

// // ========== AUTH FUNCTIONS ==========
// function toggleAuth(form) {
//     document.getElementById("signup-form").style.display = form === 'signup' ? 'block' : 'none';
//     document.getElementById("login-form").style.display = form === 'login' ? 'block' : 'none';
// }

// async function signup() {
//     const email = document.getElementById("signup-email").value;
//     const password = document.getElementById("signup-password").value;
//     const btn = document.querySelector("#signup-form button");
//     const msg = document.getElementById("auth-message");
//     btn.disabled = true;
//     msg.innerText = "Creating your account...";
//     try {
//         const res = await fetch(`${API_BASE}/signup`, {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ email, password })
//         });
//         const data = await res.json();
//         if (data.message) {
//             msg.className = "message-text success";
//             msg.innerText = "Account created successfully! Please log in.";
//             toggleAuth("login");
//         } else {
//             msg.className = "message-text error";
//             msg.innerText = data.detail || "Something went wrong!";
//         }
//     } catch (e) {
//         msg.innerText = "Backend not reachable!";
//         console.error(e);
//     } finally { btn.disabled = false; }
// }

// async function login() {
//     const email = document.getElementById("login-email").value;
//     const password = document.getElementById("login-password").value;
//     const btn = document.querySelector("#login-form button");
//     const msg = document.getElementById("auth-message");
//     btn.disabled = true;
//     msg.innerText = "Processing...";
//     try {
//         const res = await fetch(`${API_BASE}/login`, {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ email, password })
//         });
//         const data = await res.json();
//         if (data.access_token) {
//             token = data.access_token;
//             localStorage.setItem("token", token);
//             msg.innerText = "";
//             showApp();
//             loadChats(true); 
//         } else {
//             msg.className = "message-text error";
//             msg.innerText = "Invalid email or password";
//         }
//     } catch (e) {
//         msg.innerText = "Backend not reachable!";
//         console.error(e);
//     } finally { btn.disabled = false; }
// }

// function logout() {
//     token = "";
//     currentChatId = null;
//     sidebarLoaded = false;
//     uploadTime = null;
//     uploadFileSize = 0;
//     isProcessingLargePDF = false;
//     processingStartTime = null;
//     localStorage.removeItem("token");
//     localStorage.removeItem("chat_id");
//     document.getElementById("app-container").style.display = "none";
//     document.getElementById("auth-container").style.display = "flex";
// }

// // ========== CHAT MANAGEMENT ==========
// let isCreatingChat = false; 

// async function createNewChat() {
//     if (isCreatingChat) {
//         console.log("Already creating a chat, please wait...");
//         return;
//     }
    
//     isCreatingChat = true;
//     const btn = document.getElementById("new-chat-btn");
//     btn.disabled = true;
//     btn.style.opacity = "0.6";
    
//     try {
//         const res = await apiFetch(`${API_BASE}/chats`, { method: "POST" });
//         const data = await res.json();
        
//         if (!data || !data.id) {
//             throw new Error("Invalid response from server");
//         }
        
//         currentChatId = data.id;
//         localStorage.setItem("chat_id", currentChatId);
        
//         document.getElementById("chat-window").innerHTML = `
//             <div class="empty-chat">
//                 <h3>✨ New Chat Started</h3>
//                 <p>Upload a PDF and ask questions to get instant AI answers.</p>
//             </div>`;
        
//         document.getElementById("sidebar").classList.remove("active");
        
//         // Reset upload tracking for new chat
//         uploadTime = null;
//         uploadFileSize = 0;
//         isProcessingLargePDF = false;
//         processingStartTime = null;
        
//         // Clear cache and reload chats
//         chatsCache = null;
//         await loadChats(true);
        
//         console.log("✅ New chat created:", currentChatId);
        
//     } catch (e) {
//         console.error("Failed to create new chat:", e);
//         alert("Failed to create new chat. Please try again.");
//     } finally {
//         setTimeout(() => {
//             isCreatingChat = false;
//             btn.disabled = false;
//             btn.style.opacity = "1";
//         }, 3000);
//     }
// }
 
// async function loadChats(forceRefresh = false) {
//     try {
//         if (!forceRefresh && chatsCache && chatsCacheTime && (Date.now() - chatsCacheTime < CACHE_DURATION)) {
//             renderChats(chatsCache);
//             return;
//         }
        
//         const res = await apiFetch(`${API_BASE}/chats`);
//         const chats = await res.json();
        
//         // Sort by created_at (newest first)
//         const sortedChats = chats.sort((a, b) => {
//             const dateA = a.created_at ? new Date(a.created_at) : new Date(0);
//             const dateB = b.created_at ? new Date(b.created_at) : new Date(0);
//             return dateB - dateA;
//         });
        
//         // Only check by ID - no title-based filtering
//         const uniqueChats = [];
//         const seenIds = new Set();
        
//         sortedChats.forEach(chat => {
//             if (!seenIds.has(chat.id)) {
//                 seenIds.add(chat.id);
//                 uniqueChats.push(chat);
//             }
//         });
        
//         console.log(`Loaded ${uniqueChats.length} unique chats`);
        
//         chatsCache = uniqueChats;
//         chatsCacheTime = Date.now();
        
//         renderChats(uniqueChats);
        
//     } catch (e) { 
//         console.error("Failed to load chats", e); 
//     }
// }

// function renderChats(chats) {
//     const ul = document.getElementById("chat-history");
//     ul.innerHTML = "";
    
//     chats.forEach(chat => {
//         const li = document.createElement("li");
//         li.className = "history-item";
//         if (chat.id === currentChatId) {
//             li.classList.add("active");
//         }
        
//         const span = document.createElement("span");
//         span.className = "history-title";
//         span.textContent = chat.title || "New Chat";
//         span.dataset.chatId = chat.id;
        
//         if (pdfDatabase[chat.id] && pdfDatabase[chat.id].length > 0) {
//             span.innerHTML += ' <span style="font-size:11px;">📄</span>';
//         }
        
//         span.onclick = () => openChat(chat.id);
//         li.appendChild(span);
        
//         const deleteBtn = document.createElement("button");
//         deleteBtn.className = "delete-chat-btn";
//         deleteBtn.innerHTML = "✕";
//         deleteBtn.onclick = (e) => deleteSingleChat(chat.id, e);
//         li.appendChild(deleteBtn);
        
//         ul.appendChild(li);
//     });
    
//     ul.style.display = "block";
// }

// function displayChatPDFs() {
//     const container = document.getElementById('chat-pdfs-container');
//     const pdfList = document.getElementById('chat-pdfs-list');
    
//     if (!container || !pdfList) return;
    
//     if (!currentChatId || !pdfDatabase[currentChatId] || pdfDatabase[currentChatId].length === 0) {
//         container.style.display = 'none';
//         return;
//     }
    
//     container.style.display = 'block';
//     pdfList.innerHTML = '';
    
//     const pdfs = pdfDatabase[currentChatId].sort((a, b) => 
//         new Date(b.uploadedAt) - new Date(a.uploadedAt)
//     );
    
//     pdfs.forEach(pdf => {
//         const li = document.createElement("li");
//         li.className = "pdf-item";
        
//         const date = new Date(pdf.uploadedAt).toLocaleDateString('en-US', {
//             month: 'short',
//             day: 'numeric',
//             year: 'numeric'
//         });
        
//         li.innerHTML = `
//             <span class="pdf-name">📄 ${pdf.name}</span>
//             <span class="pdf-date">${date}</span>
//         `;
        
//         li.onclick = () => {
//             addChatMessage("bot", `📄 **${pdf.name}**\n_Uploaded on ${date}_`);
//         };
        
//         pdfList.appendChild(li);
//     });
// }

// async function openChat(chatId) {
//     if (currentChatId === chatId) {
//         document.getElementById("sidebar").classList.remove("active");
//         return;
//     }
    
//     currentChatId = chatId;
//     localStorage.setItem("chat_id", chatId);
//     document.getElementById("sidebar").classList.remove("active");
    
//     document.querySelectorAll(".history-item").forEach(item => {
//         item.classList.remove("active");
//     });
    
//     const activeItem = document.querySelector(`.history-title[data-chat-id="${chatId}"]`);
//     if (activeItem) {
//         activeItem.parentElement.classList.add("active");
//     }
    
//     // Reset processing state when switching chats
//     uploadTime = null;
//     uploadFileSize = 0;
//     isProcessingLargePDF = false;
//     processingStartTime = null;
    
//     document.getElementById("chat-window").innerHTML = `
//         <div class="empty-chat">
//             <h3>⏳ Loading chat...</h3>
//         </div>`;

//     try {
//         const res = await apiFetch(`${API_BASE}/chats/${chatId}`);
//         const messages = await res.json();
//         const chatWindow = document.getElementById("chat-window");
//         chatWindow.innerHTML = "";
        
//         messages.forEach(m => {
//             const msgDiv = document.createElement("div");
//             msgDiv.className = `message ${m.role === "user" ? "user" : "bot"}`;
//             msgDiv.innerHTML = m.content.replace(/\n/g, "<br>");
//             chatWindow.appendChild(msgDiv);
//         });
        
//         chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
        
//         displayChatPDFs();
        
//     } catch (e) {
//         console.error("Failed to load chat:", e);
//         document.getElementById("chat-window").innerHTML = `
//             <div class="empty-chat">
//                 <h3>❌ Failed to load chat</h3>
//                 <p>Please try again.</p>
//             </div>`;
//     }
// }

// // ========== DELETE FUNCTIONS ==========
// async function deleteSingleChat(chatId, event) {
//     event.stopPropagation();
    
//     if (!confirm('Delete this chat? This will also delete its PDFs.')) return;
    
//     const chatItem = event.target.closest('.history-item');
//     if (chatItem) {
//         chatItem.style.opacity = '0.5';
//         chatItem.style.pointerEvents = 'none';
//     }
    
//     delete pdfDatabase[chatId];
//     localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));
    
//     if (currentChatId === chatId) {
//         currentChatId = null;
//         localStorage.removeItem("chat_id");
//         document.getElementById("chat-window").innerHTML = `
//             <div class="empty-chat">
//                 <h3>📄 Upload a PDF to start chatting</h3>
//                 <p>Ask questions and get instant AI answers from your document.</p>
//             </div>`;
//         document.getElementById('chat-pdfs-container').style.display = 'none';
        
//         // Reset upload tracking
//         uploadTime = null;
//         uploadFileSize = 0;
//         isProcessingLargePDF = false;
//         processingStartTime = null;
//     }
    
//     if (chatItem) {
//         chatItem.remove();
//     }
    
//     chatsCache = null;
    
//     try {
//         await apiFetch(`${API_BASE}/chats/${chatId}`, { 
//             method: "DELETE" 
//         });
//         console.log(`✅ Chat ${chatId} deleted from backend`);
//     } catch (e) {
//         console.error("Background delete failed, will retry:", e);
//         setTimeout(() => loadChats(true), 2000);
//     }
// }

// async function deleteHistory() {
//     if (!confirm('Delete ALL chats? This will also delete associated PDFs.')) return;
    
//     document.getElementById("chat-history").innerHTML = '';
//     document.getElementById("chat-window").innerHTML = `
//         <div class="empty-chat">
//             <h3>📄 Upload a PDF to start chatting</h3>
//             <p>Ask questions and get instant AI answers from your document.</p>
//         </div>`;
//     document.getElementById('chat-pdfs-container').style.display = 'none';
    
//     pdfDatabase = {};
//     localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));
//     currentChatId = null;
//     localStorage.removeItem("chat_id");
    
//     // Reset upload tracking
//     uploadTime = null;
//     uploadFileSize = 0;
//     isProcessingLargePDF = false;
//     processingStartTime = null;
    
//     chatsCache = null;
    
//     try {
//         await apiFetch(`${API_BASE}/delete-chat-history`, { method: "DELETE" });
//         console.log("✅ All chats deleted from backend");
//     } catch (e) {
//         console.error("Background delete failed:", e);
//         setTimeout(() => loadChats(true), 2000);
//     }
// }

// // ========== STATUS CHECKING ==========
// let statusCheckInterval = null;

// // ========== UPLOAD PDFS - WITH BEAUTIFUL MESSAGES ==========
// async function uploadPDFs() {
//     const files = document.getElementById("pdf-files").files;
//     const status = document.getElementById("uploadStatus");
//     document.getElementById("question-input").disabled = true;

//     // Calculate total file size
//     let totalSize = 0;
//     for (let file of files) {
//         totalSize += file.size;
//     }
//     const sizeInMB = (totalSize / (1024 * 1024)).toFixed(1);

//     status.style.display = "block";
//     status.innerHTML = `⏳ Uploading ${files.length} PDF(s) (${sizeInMB} MB)...`;

//     if (!files || files.length === 0) {
//         alert("Please select PDF files first.");
//         return;
//     }

//     // Agar currentChatId null hai to pehle chat create karo
//     if (!currentChatId) {
//         try {
//             const chatRes = await apiFetch(`${API_BASE}/chats`, { method: "POST" });
//             const chatData = await chatRes.json();
            
//             if (!chatData || !chatData.id) {
//                 throw new Error("Failed to create chat");
//             }
            
//             currentChatId = chatData.id;
//             localStorage.setItem("chat_id", currentChatId);
            
//             // Update UI
//             document.getElementById("chat-window").innerHTML = `
//                 <div class="empty-chat">
//                     <h3>New Chat Started</h3>
//                     <p>Upload a PDF and ask questions to get instant AI answers.</p>
//                 </div>`;
            
//             console.log("✅ Auto-created new chat:", currentChatId);
            
//         } catch (e) {
//             console.error("Failed to create chat:", e);
//             alert("Failed to create chat. Please try again.");
//             document.getElementById("question-input").disabled = false;
//             return;
//         }
//     }

//     const formData = new FormData();
//     for (let f of files) formData.append("files", f);
    
//     const url = `${API_BASE}/upload-multiple?chat_id=${currentChatId}`;

//     try {
//         const res = await apiFetch(url, {
//             method: "POST", body: formData
//         });

//         const data = await res.json();
//         if (res.ok) {
//             currentChatId = data.chat_id;
//             localStorage.setItem("chat_id", currentChatId);
            
//             if (!pdfDatabase[currentChatId]) pdfDatabase[currentChatId] = [];
//             for (let file of files) {
//                 pdfDatabase[currentChatId].push({
//                     name: file.name,
//                     uploadedAt: new Date().toISOString()
//                 });
//             }
//             localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));

//             const pdfCount = files.length;
//             const pdfText = pdfCount === 1 ? 'PDF' : 'PDFs';
            
//             // ✅ Upload successful message (top banner) - Already beautiful
//             showUploadMessage(`✅ **${pdfCount} ${pdfText} uploaded successfully!**`);
            
//             // ✅ BEAUTIFUL PROCESSING MESSAGE - Compact version
//             const processingHTML = `
//                 <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 20px 24px; border-radius: 16px; margin: 10px 0; box-shadow: 0 8px 20px -4px rgba(59, 130, 246, 0.4); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(8px);">
//                     <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
//                         <div style="width: 24px; height: 24px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
//                         <span style="font-weight: 600; font-size: 16px;">PROCESSING YOUR ${pdfCount === 1 ? 'PDF' : 'PDFS'}</span>
//                     </div>
//                     <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 12px;">
//                         <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
//                             <span>📄 Pages:</span>
//                             <span style="font-weight: 600;">estimating...</span>
//                         </div>
//                         <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
//                             <span>⏱️ Time:</span>
//                             <span style="font-weight: 600;">${sizeInMB > 10 ? '30-45s' : sizeInMB > 5 ? '15-20s' : 'few sec'}</span>
//                         </div>
//                         <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.2); border-radius: 3px; margin: 12px 0;">
//                             <div style="width: 40%; height: 100%; background: white; border-radius: 3px; animation: progress 2s ease-in-out infinite;"></div>
//                         </div>
//                         <div style="font-style: italic; opacity: 0.9; font-size: 13px; text-align: center;">
//                             ✨ You'll be notified when ready
//                         </div>
//                     </div>
//                 </div>
//             `;

//             // Add to chat
//             const chatWindow = document.getElementById("chat-window");
//             const empty = document.querySelector(".empty-chat");
//             if (empty) empty.remove();

//             const msgDiv = document.createElement("div");
//             msgDiv.className = "message bot";
//             msgDiv.innerHTML = processingHTML;
//             chatWindow.appendChild(msgDiv);
//             chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
            
//             // Track processing status
//             if (sizeInMB > 5) {
//                 isProcessingLargePDF = true;
//             }
            
//             startStatusCheck(currentChatId);
            
//             status.innerHTML = "✅ Upload complete!";
//             setTimeout(() => status.style.display = "none", 3000);

//             displayChatPDFs();
            
//             chatsCache = null;
//             await loadChats(true);
//         } else {
//             alert("Upload failed: " + (data.detail || "Unknown error"));
//         }
//     } catch (e) {
//         alert("Backend not reachable!");
//         console.error(e);
//     } finally {
//         document.getElementById("question-input").disabled = false;
//         document.getElementById("pdf-files").value = "";
//     }
// }

// // ========== START STATUS CHECK WITH BEAUTIFUL MESSAGES ==========
// function startStatusCheck(chatId) {
//     // Clear any existing interval
//     if (statusCheckInterval) {
//         clearInterval(statusCheckInterval);
//     }
    
//     // Flag to prevent duplicate messages
//     let readyShown = false;
    
//     // Check every 2 seconds
//     statusCheckInterval = setInterval(async () => {
//         try {
//             const res = await apiFetch(`${API_BASE}/processing-status/${chatId}`);
//             const status = await res.json();
            
//             if (status.status === "completed" && !readyShown) {
//                 // Processing complete!
//                 clearInterval(statusCheckInterval);
//                 statusCheckInterval = null;
//                 isProcessingLargePDF = false;
//                 readyShown = true;
                
//                 // ✅ BEAUTIFUL READY MESSAGE - Same style as upload message
//                 const readyHTML = `
//                     <div style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 20px 24px; border-radius: 16px; margin: 10px 0; box-shadow: 0 8px 20px -4px rgba(16, 185, 129, 0.4); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(8px);">
//                         <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
//                             <span style="font-size: 28px;">✅</span>
//                             <span style="font-weight: 600; font-size: 18px;">READY TO ANSWER!</span>
//                         </div>
//                         <div style="background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 8px;">
//                             <div style="margin-bottom: 4px;">Your PDF has been processed.</div>
//                             <div>You can now ask anything about it.</div>
//                         </div>
//                     </div>
//                 `;
                
//                 // Add to chat
//                 const chatWindow = document.getElementById("chat-window");
//                 const empty = document.querySelector(".empty-chat");
//                 if (empty) empty.remove();
                
//                 const msgDiv = document.createElement("div");
//                 msgDiv.className = "message bot";
//                 msgDiv.innerHTML = readyHTML;
//                 chatWindow.appendChild(msgDiv);
//                 chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
                
//             } else if (status.status === "failed" && !readyShown) {
//                 // Processing failed
//                 clearInterval(statusCheckInterval);
//                 statusCheckInterval = null;
//                 isProcessingLargePDF = false;
//                 readyShown = true;
                
//                 // Failed message - red gradient
//                 const failedHTML = `
//                     <div style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 20px 24px; border-radius: 12px; margin: 10px 0; box-shadow: 0 8px 20px -4px rgba(239, 68, 68, 0.3); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(8px); animation: slideIn 0.3s ease-out;">
//                         <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
//                             <span style="font-size: 28px;">❌</span>
//                             <span style="font-weight: 700; font-size: 18px;">PROCESSING FAILED</span>
//                         </div>
//                         <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px; text-align: center;">
//                             ${status.error || 'Unknown error'}.<br>Please try uploading again.
//                         </div>
//                     </div>
//                 `;
                
//                 const chatWindow = document.getElementById("chat-window");
//                 const msgDiv = document.createElement("div");
//                 msgDiv.className = "message bot";
//                 msgDiv.innerHTML = failedHTML;
//                 chatWindow.appendChild(msgDiv);
//                 chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
//             }
            
//         } catch (e) {
//             console.error("Status check failed:", e);
//         }
//     }, 2000);
// }

// // ========== ASK QUESTION ==========
// async function askQuestion() {
//     if (!token) { alert("Please login first"); return; }
//     const question = document.getElementById("question-input").value.trim();
//     if (!question) return;
//     if (!currentChatId) { alert("Please upload PDF first."); return; }

//     // Check if still processing
//     if (statusCheckInterval) {
//         try {
//             const res = await apiFetch(`${API_BASE}/processing-status/${currentChatId}`);
//             const status = await res.json();
            
//             if (status.status === "processing") {
//                 addChatMessage("bot", 
//                     `⏳ **Please wait...**\n\n` +
//                     `Your PDF is still being processed.\n` +
//                     `📊 **Progress:** ${status.progress || 0}%\n` +
//                     `⏱️ **Status:** ${status.message || 'Processing'}\n\n` +
//                     `_You'll be notified when ready._`
//                 );
//                 document.getElementById("question-input").value = question;
//                 return;
//             }
//         } catch (e) {
//             console.error("Status check failed:", e);
//         }
//     }

//     addChatMessage("user", question);
//     showTyping();
    
//     const rawTitle = question.slice(0, 40);
//     const formattedTitle = rawTitle.charAt(0).toUpperCase() + rawTitle.slice(1).replace(/\.$/, '');
    
//     document.querySelectorAll(".history-title").forEach(el => {
//         if (el.dataset.chatId === currentChatId) el.textContent = formattedTitle;
//     });
    
//     document.getElementById("question-input").value = "";
//     const btn = document.getElementById("send-btn");
//     btn.disabled = true;

//     try {
//         const res = await apiFetch(`${API_BASE}/ask`, {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ question, chat_id: currentChatId })
//         });
//         const data = await res.json();
//         removeTyping();
        
//         let reply = data.answer ? data.answer.trim() : "No response received.";
//         const msgDiv = document.createElement("div");
//         msgDiv.className = "message bot";
//         document.getElementById("chat-window").appendChild(msgDiv);
//         typeWriter(msgDiv, reply);
        
//         chatsCache = null;
        
//     } catch (e) {
//         alert("Backend not reachable!");
//         console.error(e);
//     } finally { btn.disabled = false; }
// }

// // ========== CHAT UI FUNCTIONS ==========
// function addChatMessage(sender, text) {
//     const chatWindow = document.getElementById("chat-window");
//     const empty = document.querySelector(".empty-chat");
//     if (empty) empty.remove();
    
//     const msgDiv = document.createElement("div");
//     msgDiv.className = `message ${sender}`;
//     chatWindow.appendChild(msgDiv);
    
//     if (sender === "bot") typeWriter(msgDiv, text);
//     else msgDiv.textContent = text;
    
//     chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
// }

// function showTyping() {
//     const typing = document.createElement("div");
//     typing.className = "message bot typing";
//     typing.id = "typing-indicator";
//     typing.innerHTML = `
//         <span></span>
//         <span></span>
//         <span></span>
//     `;
//     document.getElementById("chat-window").appendChild(typing);
//     typing.scrollIntoView({ behavior: "smooth", block: "nearest" });
// }

// function removeTyping() {
//     const typing = document.getElementById("typing-indicator");
//     if (typing) typing.remove();
// }

// function typeWriter(element, text, speed = 10) {
//     element.innerHTML = "";
//     const parts = text.split(/<br\s*\/?>/);
//     let i = 0;
//     function typing() {
//         if (i < parts.length) {
//             element.innerHTML += parts[i] + "<br>";
//             i++;
//             element.scrollIntoView({ behavior: "smooth", block: "nearest" });
//             setTimeout(typing, speed);
//         }
//     }
//     typing();
// }

// function handleKey(e) {
//     if (e.key === "Enter" && !e.shiftKey) {
//         e.preventDefault();
//         askQuestion();
//     }
// }

// function showApp() {
//     document.getElementById("auth-container").style.display = "none";
//     document.getElementById("app-container").style.display = "block";
//     document.getElementById("uploadStatus").style.display = "none";
    
//     if (currentChatId) {
//         displayChatPDFs();
//     }
// }

// // ========== SIDEBAR FUNCTIONS ==========
// let sidebarLoaded = false;

// function toggleSidebar() {
//     const sidebar = document.getElementById("sidebar");
//     sidebar.classList.toggle("active");
    
//     // Only load chats once
//     if (sidebar.classList.contains("active") && !sidebarLoaded) {
//         console.log("📋 Loading chats for first time...");
//         loadChats();
//         sidebarLoaded = true;
//     }
// }

// function toggleSection(section) {
//     const chatsSection = document.getElementById('chats-section');
//     const chatsIcon = document.getElementById('chats-icon');
    
//     chatsSection.classList.toggle('collapsed');
//     chatsIcon.textContent = chatsSection.classList.contains('collapsed') ? '▶' : '▼';
// }

// // ========== INITIALIZATION ==========
// window.addEventListener("DOMContentLoaded", async () => {
//     const storedToken = localStorage.getItem("token");
//     if (!storedToken) {
//         document.getElementById("auth-container").style.display = "block";
//         document.getElementById("app-container").style.display = "none";
//         return;
//     }
//     token = storedToken;
//     try {
//         const res = await fetch(`${API_BASE}/chats`, { headers: { "Authorization": `Bearer ${token}` } });
//         if (res.status === 401) logout();
//         else {
//             showApp();
//             loadChats(true); 
//         }
//     } catch (e) { logout(); }
//     document.getElementById("question-input")?.focus();
// });

// // ========== UPLOAD MESSAGE FUNCTION (ALREADY BEAUTIFUL) ==========
// function showUploadMessage(message) {
//     const chatWindow = document.getElementById("chat-window");
    
//     const oldMsg = document.getElementById("upload-message");
//     if (oldMsg) oldMsg.remove();
    
//     const msgDiv = document.createElement("div");
//     msgDiv.id = "upload-message";
//     msgDiv.className = "upload-message";
//     msgDiv.innerHTML = message;
    
//     chatWindow.insertBefore(msgDiv, chatWindow.firstChild);
    
//     setTimeout(() => {
//         if (msgDiv) msgDiv.remove();
//     }, 3000);
// }







































































































const API_BASE = "http://127.0.0.1:8000";
let token = localStorage.getItem("token") || "";
let currentChatId = null;
let pdfDatabase = {};

// ========== UPLOAD TRACKING VARIABLES ==========
let uploadTime = null;
let uploadFileSize = 0;
let isProcessingLargePDF = false;
let processingStartTime = null;

try {
    pdfDatabase = JSON.parse(localStorage.getItem('pdfDatabase')) || {};
} catch(e) {
    pdfDatabase = {};
    console.error("Error loading PDF database:", e);
}

let chatsCache = null;
let chatsCacheTime = null;
const CACHE_DURATION = 5000; 

// ========== API FETCH WITH AUTH ==========
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
            loadChats(true); 
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
    sidebarLoaded = false;
    uploadTime = null;
    uploadFileSize = 0;
    isProcessingLargePDF = false;
    processingStartTime = null;
    localStorage.removeItem("token");
    localStorage.removeItem("chat_id");
    document.getElementById("app-container").style.display = "none";
    document.getElementById("auth-container").style.display = "flex";
}

// ========== CHAT MANAGEMENT ==========
let isCreatingChat = false; 

async function createNewChat() {
    if (isCreatingChat) {
        console.log("Already creating a chat, please wait...");
        return;
    }
    
    isCreatingChat = true;
    const btn = document.getElementById("new-chat-btn");
    btn.disabled = true;
    btn.style.opacity = "0.6";
    
    try {
        const res = await apiFetch(`${API_BASE}/chats`, { method: "POST" });
        const data = await res.json();
        
        if (!data || !data.id) {
            throw new Error("Invalid response from server");
        }
        
        currentChatId = data.id;
        localStorage.setItem("chat_id", currentChatId);
        
        document.getElementById("chat-window").innerHTML = `
            <div class="empty-chat">
                <h3>✨ New Chat Started</h3>
                <p>Upload a PDF and ask questions to get instant AI answers.</p>
            </div>`;
        
        document.getElementById("sidebar").classList.remove("active");
        
        // Reset upload tracking for new chat
        uploadTime = null;
        uploadFileSize = 0;
        isProcessingLargePDF = false;
        processingStartTime = null;
        
        // Clear cache and reload chats
        chatsCache = null;
        await loadChats(true);
        
        console.log("✅ New chat created:", currentChatId);
        
    } catch (e) {
        console.error("Failed to create new chat:", e);
        alert("Failed to create new chat. Please try again.");
    } finally {
        setTimeout(() => {
            isCreatingChat = false;
            btn.disabled = false;
            btn.style.opacity = "1";
        }, 3000);
    }
}
 
async function loadChats(forceRefresh = false) {
    try {
        if (!forceRefresh && chatsCache && chatsCacheTime && (Date.now() - chatsCacheTime < CACHE_DURATION)) {
            renderChats(chatsCache);
            return;
        }
        
        const res = await apiFetch(`${API_BASE}/chats`);
        const chats = await res.json();
        
        // Sort by created_at (newest first)
        const sortedChats = chats.sort((a, b) => {
            const dateA = a.created_at ? new Date(a.created_at) : new Date(0);
            const dateB = b.created_at ? new Date(b.created_at) : new Date(0);
            return dateB - dateA;
        });
        
        // Only check by ID - no title-based filtering
        const uniqueChats = [];
        const seenIds = new Set();
        
        sortedChats.forEach(chat => {
            if (!seenIds.has(chat.id)) {
                seenIds.add(chat.id);
                uniqueChats.push(chat);
            }
        });
        
        console.log(`Loaded ${uniqueChats.length} unique chats`);
        
        chatsCache = uniqueChats;
        chatsCacheTime = Date.now();
        
        renderChats(uniqueChats);
        
    } catch (e) { 
        console.error("Failed to load chats", e); 
    }
}

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
        
        if (pdfDatabase[chat.id] && pdfDatabase[chat.id].length > 0) {
            span.innerHTML += ' <span style="font-size:11px;">📄</span>';
        }
        
        span.onclick = () => openChat(chat.id);
        li.appendChild(span);
        
        const deleteBtn = document.createElement("button");
        deleteBtn.className = "delete-chat-btn";
        deleteBtn.innerHTML = "✕";
        deleteBtn.onclick = (e) => deleteSingleChat(chat.id, e);
        li.appendChild(deleteBtn);
        
        ul.appendChild(li);
    });
    
    ul.style.display = "block";
}

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

async function openChat(chatId) {
    if (currentChatId === chatId) {
        document.getElementById("sidebar").classList.remove("active");
        return;
    }
    
    currentChatId = chatId;
    localStorage.setItem("chat_id", chatId);
    document.getElementById("sidebar").classList.remove("active");
    
    document.querySelectorAll(".history-item").forEach(item => {
        item.classList.remove("active");
    });
    
    const activeItem = document.querySelector(`.history-title[data-chat-id="${chatId}"]`);
    if (activeItem) {
        activeItem.parentElement.classList.add("active");
    }
    
    // Reset processing state when switching chats
    uploadTime = null;
    uploadFileSize = 0;
    isProcessingLargePDF = false;
    processingStartTime = null;
    
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

// ========== DELETE FUNCTIONS ==========
async function deleteSingleChat(chatId, event) {
    event.stopPropagation();
    
    if (!confirm('Delete this chat? This will also delete its PDFs.')) return;
    
    const chatItem = event.target.closest('.history-item');
    if (chatItem) {
        chatItem.style.opacity = '0.5';
        chatItem.style.pointerEvents = 'none';
    }
    
    delete pdfDatabase[chatId];
    localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));
    
    if (currentChatId === chatId) {
        currentChatId = null;
        localStorage.removeItem("chat_id");
        document.getElementById("chat-window").innerHTML = `
            <div class="empty-chat">
                <h3>📄 Upload a PDF to start chatting</h3>
                <p>Ask questions and get instant AI answers from your document.</p>
            </div>`;
        document.getElementById('chat-pdfs-container').style.display = 'none';
        
        // Reset upload tracking
        uploadTime = null;
        uploadFileSize = 0;
        isProcessingLargePDF = false;
        processingStartTime = null;
    }
    
    if (chatItem) {
        chatItem.remove();
    }
    
    chatsCache = null;
    
    try {
        await apiFetch(`${API_BASE}/chats/${chatId}`, { 
            method: "DELETE" 
        });
        console.log(`✅ Chat ${chatId} deleted from backend`);
    } catch (e) {
        console.error("Background delete failed, will retry:", e);
        setTimeout(() => loadChats(true), 2000);
    }
}

async function deleteHistory() {
    if (!confirm('Delete ALL chats? This will also delete associated PDFs.')) return;
    
    document.getElementById("chat-history").innerHTML = '';
    document.getElementById("chat-window").innerHTML = `
        <div class="empty-chat">
            <h3>📄 Upload a PDF to start chatting</h3>
            <p>Ask questions and get instant AI answers from your document.</p>
        </div>`;
    document.getElementById('chat-pdfs-container').style.display = 'none';
    
    pdfDatabase = {};
    localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));
    currentChatId = null;
    localStorage.removeItem("chat_id");
    
    // Reset upload tracking
    uploadTime = null;
    uploadFileSize = 0;
    isProcessingLargePDF = false;
    processingStartTime = null;
    
    chatsCache = null;
    
    try {
        await apiFetch(`${API_BASE}/delete-chat-history`, { method: "DELETE" });
        console.log("✅ All chats deleted from backend");
    } catch (e) {
        console.error("Background delete failed:", e);
        setTimeout(() => loadChats(true), 2000);
    }
}

// ========== STATUS CHECKING ==========
let statusCheckInterval = null;

// ========== UPLOAD PDFS - WITH PROFESSIONAL MESSAGES ==========
async function uploadPDFs() {
    const files = document.getElementById("pdf-files").files;
    const status = document.getElementById("uploadStatus");
    document.getElementById("question-input").disabled = true;

    // Calculate total file size
    let totalSize = 0;
    for (let file of files) {
        totalSize += file.size;
    }
    const sizeInMB = (totalSize / (1024 * 1024)).toFixed(1);

    status.style.display = "block";
    status.innerHTML = `⏳ Uploading ${files.length} PDF(s) (${sizeInMB} MB)...`;

    if (!files || files.length === 0) {
        alert("Please select PDF files first.");
        return;
    }

    // Agar currentChatId null hai to pehle chat create karo
    if (!currentChatId) {
        try {
            const chatRes = await apiFetch(`${API_BASE}/chats`, { method: "POST" });
            const chatData = await chatRes.json();
            
            if (!chatData || !chatData.id) {
                throw new Error("Failed to create chat");
            }
            
            currentChatId = chatData.id;
            localStorage.setItem("chat_id", currentChatId);
            
            // Update UI
            document.getElementById("chat-window").innerHTML = `
                <div class="empty-chat">
                    <h3>New Chat Started</h3>
                    <p>Upload a PDF and ask questions to get instant AI answers.</p>
                </div>`;
            
            console.log("✅ Auto-created new chat:", currentChatId);
            
        } catch (e) {
            console.error("Failed to create chat:", e);
            alert("Failed to create chat. Please try again.");
            document.getElementById("question-input").disabled = false;
            return;
        }
    }

    const formData = new FormData();
    for (let f of files) formData.append("files", f);
    
    const url = `${API_BASE}/upload-multiple?chat_id=${currentChatId}`;

    try {
        const res = await apiFetch(url, {
            method: "POST", body: formData
        });

        const data = await res.json();
        if (res.ok) {
            currentChatId = data.chat_id;
            localStorage.setItem("chat_id", currentChatId);
            
            if (!pdfDatabase[currentChatId]) pdfDatabase[currentChatId] = [];
            for (let file of files) {
                pdfDatabase[currentChatId].push({
                    name: file.name,
                    uploadedAt: new Date().toISOString()
                });
            }
            localStorage.setItem('pdfDatabase', JSON.stringify(pdfDatabase));

            const pdfCount = files.length;
            const pdfText = pdfCount === 1 ? 'PDF' : 'PDFs';
            
            // ✅ Upload successful message (top banner)
            showUploadMessage(`✅ **${pdfCount} ${pdfText} uploaded successfully!**`);
            
            // ✅ PROFESSIONAL PROCESSING MESSAGE - Blue with spinner
            const processingHTML = `
                <div id="processing-message" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 20px 24px; border-radius: 16px; margin: 10px 0; box-shadow: 0 8px 20px -4px rgba(59, 130, 246, 0.4); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(8px);">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                        <div style="width: 24px; height: 24px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                        <span style="font-weight: 600; font-size: 16px;">PROCESSING YOUR ${pdfCount === 1 ? 'PDF' : 'PDFS'}</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>📄 Pages:</span>
                            <span style="font-weight: 600;">estimating...</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                            <span>⏱️ Time:</span>
                            <span style="font-weight: 600;">${sizeInMB > 10 ? '30-45s' : sizeInMB > 5 ? '15-20s' : 'few sec'}</span>
                        </div>
                        <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.2); border-radius: 3px; margin: 12px 0;">
                            <div style="width: 40%; height: 100%; background: white; border-radius: 3px; animation: progress 2s ease-in-out infinite;"></div>
                        </div>
                        <div style="font-style: italic; opacity: 0.9; font-size: 13px; text-align: center;">
                            ✨ You'll be notified when ready
                        </div>
                    </div>
                </div>
            `;

            // Add to chat
            const chatWindow = document.getElementById("chat-window");
            const empty = document.querySelector(".empty-chat");
            if (empty) empty.remove();

            const msgDiv = document.createElement("div");
            msgDiv.className = "message bot";
            msgDiv.id = "processing-message-container";
            msgDiv.innerHTML = processingHTML;
            chatWindow.appendChild(msgDiv);
            chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
            
            // Track processing status
            if (sizeInMB > 5) {
                isProcessingLargePDF = true;
            }
            
            startStatusCheck(currentChatId);
            
            status.innerHTML = "✅ Upload complete!";
            setTimeout(() => status.style.display = "none", 3000);

            displayChatPDFs();
            
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

// ========== START STATUS CHECK WITH PROPER REPLACEMENT ==========
function startStatusCheck(chatId) {
    // Clear any existing interval
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    // Flag to prevent duplicate messages
    let readyShown = false;
    
    // Check every 2 seconds
    statusCheckInterval = setInterval(async () => {
        try {
            const res = await apiFetch(`${API_BASE}/processing-status/${chatId}`);
            const status = await res.json();
            
            if (status.status === "completed" && !readyShown) {
                // Processing complete!
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
                isProcessingLargePDF = false;
                readyShown = true;
                
                // ✅ PROFESSIONAL READY MESSAGE - Green success (no spinner)
                const readyHTML = `
                    <div style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 20px 24px; border-radius: 16px; margin: 10px 0; box-shadow: 0 8px 20px -4px rgba(16, 185, 129, 0.4); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(8px);">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <span style="font-size: 28px;">✅</span>
                            <span style="font-weight: 600; font-size: 18px;">READY TO ANSWER!</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 8px;">
                            <div style="margin-bottom: 4px;">Your PDF has been processed.</div>
                            <div>You can now ask anything about it.</div>
                        </div>
                    </div>
                `;
                
                // 🔥 Remove processing message
                const processingContainer = document.getElementById("processing-message-container");
                if (processingContainer) {
                    processingContainer.remove();
                }
                
                // Add ready message
                const chatWindow = document.getElementById("chat-window");
                const msgDiv = document.createElement("div");
                msgDiv.className = "message bot";
                msgDiv.innerHTML = readyHTML;
                chatWindow.appendChild(msgDiv);
                chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
                
            } else if (status.status === "failed" && !readyShown) {
                // Processing failed
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
                isProcessingLargePDF = false;
                readyShown = true;
                
                // Failed message - red gradient
                const failedHTML = `
                    <div style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 20px 24px; border-radius: 16px; margin: 10px 0; box-shadow: 0 8px 20px -4px rgba(239, 68, 68, 0.4); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(8px);">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <span style="font-size: 28px;">❌</span>
                            <span style="font-weight: 600; font-size: 18px;">PROCESSING FAILED</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 8px;">
                            ${status.error || 'Something went wrong'}. Please try again.
                        </div>
                    </div>
                `;
                
                const processingContainer = document.getElementById("processing-message-container");
                if (processingContainer) {
                    processingContainer.remove();
                }
                
                const chatWindow = document.getElementById("chat-window");
                const msgDiv = document.createElement("div");
                msgDiv.className = "message bot";
                msgDiv.innerHTML = failedHTML;
                chatWindow.appendChild(msgDiv);
                chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
            }
            
        } catch (e) {
            console.error("Status check failed:", e);
        }
    }, 2000);
}

// ========== ASK QUESTION ==========
async function askQuestion() {
    if (!token) { alert("Please login first"); return; }
    const question = document.getElementById("question-input").value.trim();
    if (!question) return;
    if (!currentChatId) { alert("Please upload PDF first."); return; }

    // Check if still processing
    if (statusCheckInterval) {
        try {
            const res = await apiFetch(`${API_BASE}/processing-status/${currentChatId}`);
            const status = await res.json();
            
            if (status.status === "processing") {
                addChatMessage("bot", 
                    `⏳ **Please wait...**\n\n` +
                    `Your PDF is still being processed.\n` +
                    `📊 **Progress:** ${status.progress || 0}%\n` +
                    `⏱️ **Status:** ${status.message || 'Processing'}\n\n` +
                    `_You'll be notified when ready._`
                );
                document.getElementById("question-input").value = question;
                return;
            }
        } catch (e) {
            console.error("Status check failed:", e);
        }
    }

    addChatMessage("user", question);
    showTyping();
    
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
        
        chatsCache = null;
        
    } catch (e) {
        alert("Backend not reachable!");
        console.error(e);
    } finally { btn.disabled = false; }
}

// ========== CHAT UI FUNCTIONS ==========
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
    typing.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    document.getElementById("chat-window").appendChild(typing);
    typing.scrollIntoView({ behavior: "smooth", block: "nearest" });
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

function showApp() {
    document.getElementById("auth-container").style.display = "none";
    document.getElementById("app-container").style.display = "block";
    document.getElementById("uploadStatus").style.display = "none";
    
    if (currentChatId) {
        displayChatPDFs();
    }
}

// ========== SIDEBAR FUNCTIONS ==========
let sidebarLoaded = false;

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("active");
    
    // Only load chats once
    if (sidebar.classList.contains("active") && !sidebarLoaded) {
        console.log("📋 Loading chats for first time...");
        loadChats();
        sidebarLoaded = true;
    }
}

function toggleSection(section) {
    const chatsSection = document.getElementById('chats-section');
    const chatsIcon = document.getElementById('chats-icon');
    
    chatsSection.classList.toggle('collapsed');
    chatsIcon.textContent = chatsSection.classList.contains('collapsed') ? '▶' : '▼';
}

// ========== INITIALIZATION ==========
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
            loadChats(true); 
        }
    } catch (e) { logout(); }
    document.getElementById("question-input")?.focus();
});

// ========== UPLOAD MESSAGE FUNCTION ==========
function showUploadMessage(message) {
    const chatWindow = document.getElementById("chat-window");
    
    const oldMsg = document.getElementById("upload-message");
    if (oldMsg) oldMsg.remove();
    
    const msgDiv = document.createElement("div");
    msgDiv.id = "upload-message";
    msgDiv.className = "upload-message";
    msgDiv.innerHTML = message;
    
    chatWindow.insertBefore(msgDiv, chatWindow.firstChild);
    
    setTimeout(() => {
        if (msgDiv) msgDiv.remove();
    }, 3000);
}