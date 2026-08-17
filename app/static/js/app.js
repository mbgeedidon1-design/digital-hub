function toggleAI(){
    document.getElementById("aiChat").classList.toggle("open");
}

let gimmieVoice = null;
let gimmieListening = false;

function setupGimmieVoice(){
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        return false;
    }

    gimmieVoice = new SpeechRecognition();
    gimmieVoice.lang = "en-KE";
    gimmieVoice.interimResults = false;
    gimmieVoice.continuous = false;

    gimmieVoice.onstart = function(){
        gimmieListening = true;
        const button = document.getElementById("gimmieVoice");
        if(button){
            button.textContent = "🔴 Listening...";
            button.classList.add("listening");
        }
    };

    gimmieVoice.onend = function(){
        gimmieListening = false;
        const button = document.getElementById("gimmieVoice");
        if(button){
            button.textContent = "🎤 Talk to Gimmie";
            button.classList.remove("listening");
        }
    };

    gimmieVoice.onerror = function(event){
        gimmieListening = false;
        const button = document.getElementById("gimmieVoice");

        if(button){
            button.textContent = "🎤 Talk to Gimmie";
            button.classList.remove("listening");
        }

        const box = document.getElementById("aiMessages");

        if(event.error === "not-allowed"){
            addAIMessage(
                "🎤 Microphone permission was blocked. Please allow microphone access in your browser."
            );
        } else if(event.error !== "aborted"){
            addAIMessage(
                "I couldn't hear that. Please try speaking again."
            );
        }
    };

    gimmieVoice.onresult = function(event){
        const transcript = event.results[0][0].transcript;

        const input = document.getElementById("aiInput");
        input.value = transcript;

        sendAIMessage(transcript);
    };

    return true;
}

function startGimmieVoice(){
    if(!gimmieVoice){
        if(!setupGimmieVoice()){
            addAIMessage(
                "🎤 Voice input isn't supported by this browser. You can still type your question."
            );
            return;
        }
    }

    if(gimmieListening){
        gimmieVoice.stop();
        return;
    }

    try{
        gimmieVoice.start();
    }catch(error){
        console.log("Voice start:", error);
    }
}

function speakGimmie(text){
    if(!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    const cleanText = text
        .replace(/\*\*/g, "")
        .replace(/[#*_]/g, "");

    const speech = new SpeechSynthesisUtterance(cleanText);
    speech.lang = "en-KE";
    speech.rate = 1;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
}

function addAIMessage(text){
    const box = document.getElementById("aiMessages");

    const bubble = document.createElement("div");
    bubble.className = "ai-bubble";
    bubble.textContent = text;

    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
}

async function sendAI(e){
    if(e) e.preventDefault();

    const input = document.getElementById("aiInput");
    const msg = input.value.trim();

    if(!msg) return;

    input.value = "";
    sendAIMessage(msg);
}

async function sendAIMessage(msg){
    const box = document.getElementById("aiMessages");

    box.innerHTML +=
        `<div class="user-bubble">${escapeHTML(msg)}</div>`;

    const typing = document.createElement("div");
    typing.className = "ai-bubble";
    typing.textContent = "Thinking…";

    box.appendChild(typing);
    box.scrollTop = box.scrollHeight;

    try{
        const r = await fetch("/api/ai", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: msg
            })
        });

        const data = await r.json();

        const answer =
            data.answer ||
            "Please contact our Digital Hub team for help.";

        typing.textContent = answer;

        box.scrollTop = box.scrollHeight;

        speakGimmie(answer);

    }catch(err){
        typing.textContent =
            "I couldn't connect right now. Please use the Order or Send a Photo page.";

        box.scrollTop = box.scrollHeight;
    }
}

function escapeHTML(s){
    return s.replace(
        /[&<>"']/g,
        c => ({
            '&':'&amp;',
            '<':'&lt;',
            '>':'&gt;',
            '"':'&quot;',
            "'":'&#039;'
        }[c])
    );
}

document.addEventListener("DOMContentLoaded", function(){
    setupGimmieVoice();
});
