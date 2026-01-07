const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

const SESSION_URL = "/api/session";
const CHAT_URL = "/api/chat/stream";
let sessionId = null;
let captchaToken = null; // Store the token here

async function getSessionId() {
  try {
    const res = await fetch(SESSION_URL, { method: "POST" });
    const data = await res.json();
    sessionId = data.session_id;
  } catch (err) {
    addMessage("⚠️ Error iniciando la sesión con el servidor.", "ai");
  }
}

function addMessage(text, sender, isMarkdown = true) {
  const msg = document.createElement("div");
  msg.classList.add("message", `${sender}-message`);
  msg.innerHTML = isMarkdown ? marked.parse(text) : text;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
  return msg;
}

async function sendMessage() {  
  const inputText = userInput.value.trim();
  if (!inputText || !sessionId) return;

  addMessage(inputText, "user", false);
  userInput.value = "";
  userInput.disabled = true;
  sendBtn.disabled = true;

  const aiMessageElement = addMessage("...", "ai", false);
  aiMessageElement.classList.add("typing");

  try {
    const response = await fetch(CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_input: inputText,
        session_id: sessionId,
        captcha_token: captchaToken, // Will be sent on the first message
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      const errorMessage = errorData.detail || "Ocurrió un error inesperado.";
      aiMessageElement.classList.remove("typing");
      aiMessageElement.innerHTML = marked.parse(`⚠️ **Error:** ${errorMessage}`);
      return;
    }

    // The token has been used, nullify it for subsequent requests
    captchaToken = null; 
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = "";
    aiMessageElement.classList.remove("typing");

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      fullResponse += chunk;
      aiMessageElement.innerHTML = marked.parse(fullResponse);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  } catch (error) {
    aiMessageElement.textContent = "❌ Ocurrió un error al procesar tu mensaje.";
  } finally {
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
  }
}

// This function is called by hCaptcha upon successful verification
function onCaptchaSuccess(token) {
  console.log("Captcha solved successfully.");
  captchaToken = token;
  
  const overlay = document.getElementById("captcha-overlay");
  if (overlay) {
    overlay.style.opacity = "0";
    setTimeout(() => overlay.style.display = "none", 300);
  }

  // Enable chat
  userInput.disabled = false;
  sendBtn.disabled = false;
  userInput.placeholder = "Escribe tu mensaje aquí...";
  userInput.focus();
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keyup", (e) => {
  if (e.key === "Enter") sendMessage();
});

document.addEventListener("click", (e) => {
  if (e.target.classList.contains("suggestion-btn")) {
    userInput.value = e.target.textContent;
    sendMessage();
  }
});

//CANVAS
const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");

let particles = [];
let w, h;

function resizeCanvas() {
  w = canvas.width = window.innerWidth;
  h = canvas.height = window.innerHeight;
  particles = [];
  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 2 + 1,
      dx: (Math.random() - 0.5) * 0.6,
      dy: (Math.random() - 0.5) * 0.6,
    });
  }
}

function drawParticles() {
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  particles.forEach((p) => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fill();

    p.x += p.dx;
    p.y += p.dy;

    if (p.x < 0 || p.x > w) p.dx *= -1;
    if (p.y < 0 || p.y > h) p.dy *= -1;
  });
  requestAnimationFrame(drawParticles);
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();
drawParticles();

window.onload = getSessionId;