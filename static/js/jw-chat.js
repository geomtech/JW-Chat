const socket = io();
var thread_id = 0;

var startedMessaging = false;
var assistantMessageSection = null;
var markdownMessage = null;

const userTemplate = document.getElementById("user-template");
const assistantTemplate = document.getElementById("assistant-template");
const statusElement = document.getElementById("status");

document.getElementById("question-form").onsubmit = function (event) {
    event.preventDefault();
    const userInput = document.getElementById("user-input").innerText;

    if (userInput.trim() == "") {
        alert("Vous ne pouvez pas envoyer un message vide.", "error");
        return;
    }

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
    document.getElementById("user-input").innerText = "";
    placeholderUpdate();
};

// Écoute les réponses de l'API
socket.on('response', function (data) {
    if ("thread_id" in data) {
        thread_id = data.thread_id;
    }

    if ("message" in data) {
        if (startedMessaging == false) {
            markdownMessage = "";
            assistantMessageSection = assistantTemplate.cloneNode(true);
            document.getElementById("response").appendChild(assistantMessageSection);
            startedMessaging = true;
        }

        markdownMessage = markdownMessage += data.message;

        assistantMessageSection.classList.remove('hidden');
        assistantMessageSection.querySelector('.response').innerHTML = marked.parse(markdownMessage);

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
        document.getElementById("response").lastChild.querySelector('.links').appendChild(articleElement);
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
        document.getElementById("response").lastChild.querySelector('.links').appendChild(pubElement);
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
        } else if (data.status == "in_progress") {
            statusElement.innerText = "...";
        } else if (data.status == "completed") {
            statusElement.innerText = "";
        } else if (data.status == "source_search") {
            statusElement.innerText = "Recherche d'informations dans la bibliothèque...";
        } else if (data.status == "function_call") {
            statusElement.innerText = "Recherche d'informations sur JW.ORG et WOL...";
        } else {
            statusElement.innerText = data.status;
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById("user-input").focus();
});

document.getElementById("user-input").addEventListener('keydown', function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        document.getElementById("question-form").dispatchEvent(new Event('submit'));

        // restore the height of the textarea
        this.style.height = 'auto';
    }
});

function placeholderUpdate() {
    if (document.getElementById("user-input").innerText == "") {
        document.getElementById("user-input-placeholder").innerText = "Message JW CH.AT";
    } else {
        document.getElementById("user-input-placeholder").innerText = "";
    }
}

document.getElementById("user-input").addEventListener('input', function () {
    placeholderUpdate();
});

document.getElementById("user-input").addEventListener('touchstart', function () {
    this.focus();
});

document.getElementById("user-input-placeholder").addEventListener('touchstart', function () {
    document.getElementById("user-input").focus();
});

document.getElementById("user-input").addEventListener('blur', function () {
    window.scrollTo(0, document.body.scrollHeight);
});

document.getElementById("question-form").addEventListener('submit', function () {
    document.getElementById("user-input").blur();
});