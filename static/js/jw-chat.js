const socket = io();
var thread_id = 0;

var startedMessaging = false;
var assistantMessageSection = null;

const userTemplate = document.getElementById("user-template");
const assistantTemplate = document.getElementById("assistant-template");
const statusElement = document.getElementById("status");

document.getElementById("question-form").onsubmit = function (event) {
    event.preventDefault();
    const userInput = document.getElementById("user-input").value;

    // Envoie la question via WebSocket
    if (thread_id == 0) {
        socket.emit('ask_openai', { user_input: userInput });
    } else {
        socket.emit('ask_openai', { user_input: userInput, thread_id: thread_id });
    }

    const userMessage = userTemplate.cloneNode(true);
    userMessage.classList.remove('hidden');
    userMessage.querySelector('div').innerText = userInput;
    document.getElementById("response").appendChild(userMessage);

    window.scrollTo(0, document.body.scrollHeight);
    document.getElementById("user-input").value = "";
};

function formatMessage(message) {
    // Transformer les textes entre ** en gras (y compris les numéros et suffixes comme ':')
    message = message.replace(/(\d+\.\s)?\*\*(.*?)\s*\*\*\s*:/g, (match, prefix = "", boldText) => {
        // Inclure le numéro et ":" dans la balise <b>, en supprimant les espaces autour du texte
        return `<b class="font-bold">${(prefix || "")}${boldText.trim()} :</b>`;
    });

    // Traiter les niveaux de titres Markdown
    message = message.replace(/^###### (.+)$/gm, "<h6>$1</h6>");
    message = message.replace(/^##### (.+)$/gm, "<h5>$1</h5>");
    message = message.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
    message = message.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    message = message.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    message = message.replace(/^# (.+)$/gm, "<h1>$1</h1>");

    // Gérer les listes numérotées (ex: "1. Texte")
    message = message.replace(/^(\d+)\.\s+(.+)$/gm, "<li>$2</li>");

    // Ajouter des sauts de ligne en <br>
    message = message.replace(/\n/g, "<br>");

    // Remettre les <li> dans des balises <ul> pour des listes bien formées
    message = message.replace(/(<li>.*?<\/li>)/g, "<ul>$1</ul>");

    return message;
}

// Écoute les réponses de l'API
socket.on('response', function (data) {
    console.log(data);

    if ("thread_id" in data) {
        thread_id = data.thread_id;
    }

    if ("message" in data) {
        if (startedMessaging == false) {
            assistantMessageSection = assistantTemplate.cloneNode(true);
            document.getElementById("response").appendChild(assistantMessageSection);
            startedMessaging = true;
        }

        var message_text = assistantMessageSection.querySelector('div').innerHTML += data.message;

        message_text = formatMessage(message_text);

        assistantMessageSection.classList.remove('hidden');
        assistantMessageSection.querySelector('div').innerHTML = message_text;

        // scroll to the bottom of document
        window.scrollTo(0, document.body.scrollHeight);
    }

    if ("article" in data) {
        // article contains the url, title, and image of the article to put on the left side of the message
        const article = data.article;
        const articleElement = document.createElement('a');
        articleElement.classList.add('flex', 'flex-row', 'gap-2', 'w-full', 'mt-4', 'items-center');
        articleElement.href = article.url;
        articleElement.target = "_blank";
        articleElement.innerHTML = "<img src='" + article.image + "' class='w-10 h-10 rounded-md'>";
        articleElement.innerHTML += "<span>" + article.title + "</span>";
        document.getElementById("response").lastChild.querySelector('div').appendChild(articleElement);
    }

    if ("pub" in data) {
        // pub contains the url, title, and image of the pub to put on the left side of the message
        const pub = data.pub;
        const pubElement = document.createElement('a');
        pubElement.classList.add('flex', 'flex-row', 'gap-2', 'w-full', 'mt-4', 'items-center');
        pubElement.href = pub.url;
        pubElement.target = "_blank";
        pubElement.innerHTML = "<img src='" + pub.image + "' class='w-10 h-10 rounded-md'>";
        pubElement.innerHTML += "<span>" + pub.title + "</span>";
        document.getElementById("response").lastChild.querySelector('div').appendChild(pubElement);
    }

    if ("sources" in data) {
        if (data.sources.length == 0) {
            return;
        }

        last_message = document.getElementById("response").lastChild.querySelector('div');

        last_message.innerHTML += "<br><br><b>Source(s):</b><br>";

        for (var i = 0; i < data.sources.length; i++) {
            last_message.innerHTML += "<a href='" + data.sources[i].url + "' target='_blank'>" + data.sources[i].title + "</a><br>";
        }
    }

    if ("error" in data) {
        console.log(data);
        const errorMessage = assistantTemplate.cloneNode(true);
        errorMessage.classList.remove('hidden');
        errorMessage.querySelector('div').innerText = data.error;
        errorMessage.style.color = "red";
        document.getElementById("response").appendChild(errorMessage);
    }

    if ("status" in data) {
        console.log(data);

        if (data.status == "end") {
            startedMessaging = false;
            statusElement.innerText = "";

            // Format every messages
            for (var i = 0; i < document.getElementById("response").children.length; i++) {
                var message = document.getElementById("response").children[i].querySelector('div').innerHTML;
                message = formatMessage(message);
                document.getElementById("response").children[i].querySelector('div').innerHTML = message;
            }
        } else if (data.status == "in_progress") {
            statusElement.innerText = "...";
        } else if (data.status == "completed") {
            statusElement.innerText = "";
        } else if (data.status == "source_search") {
            statusElement.innerText = "Recherche d'informations dans la bibliothèque...";
        } else if (data.status == "function_call") {
            statusElement.innerText = "Recherche d'informations sur JW.ORG ou la Bibliothèque en ligne...";
        } else {
            statusElement.innerText = data.status;
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    if (!sessionStorage.getItem('rgpdAccepted')) {
        window.location.href = '/rgpd';
    }
    document.getElementById("user-input").focus();
});

document.getElementById("user-input").addEventListener('keydown', function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        document.getElementById("question-form").dispatchEvent(new Event('submit'));
    }
});

// Handle the creation and switching of tabs
function switchTab(tabId) {
    // Hide all chat windows
    const chatWindows = document.querySelectorAll('.chat-window');
    chatWindows.forEach(window => window.classList.add('hidden'));

    // Show the selected chat window
    const selectedChatWindow = document.getElementById(tabId);
    selectedChatWindow.classList.remove('hidden');

    // Update the thread_id to the selected chat window's thread_id
    thread_id = selectedChatWindow.dataset.threadId;
}

// Ensure each tab has a unique session identifier
function createNewTab() {
    const newTabId = `tab${Date.now()}`;
    const newTabButton = document.createElement('button');
    newTabButton.classList.add('tab', 'bg-neutral-200', 'dark:bg-neutral-800', 'text-gray-900', 'dark:text-gray-100', 'p-2', 'rounded-md');
    newTabButton.innerText = `Chat ${newTabId}`;
    newTabButton.setAttribute('onclick', `switchTab('${newTabId}')`);

    const tabsContainer = document.getElementById('tabs');
    tabsContainer.appendChild(newTabButton);

    const newChatWindow = document.createElement('div');
    newChatWindow.id = newTabId;
    newChatWindow.classList.add('chat-window', 'hidden');
    newChatWindow.dataset.threadId = newTabId;

    const responseContainer = document.getElementById('response');
    responseContainer.appendChild(newChatWindow);
}
