const socket = io();
var thread_id = 0;

var startedMessaging = false;
var assistantMessageSection = null;
var markdownMessage = null;

const userTemplate = document.getElementById("user-template");
const assistantTemplate = document.getElementById("assistant-template");
const statusElement = document.getElementById("status");

var firstUserInput = "";

document.getElementById("question-form").onsubmit = function (event) {
    event.preventDefault();
    const userInput = document.getElementById("user-input").innerText;
    firstUserInput = userInput;

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

newMessage = function (message) {
    const assistantMessage = assistantTemplate.cloneNode(true);
    assistantMessage.classList.remove('hidden');
    assistantMessage.querySelector('.response').innerHTML = marked.parse(bible_handler(message));
    document.getElementById("response").appendChild(assistantMessage);
}

newUserMessage = function (message) {
    const userMessage = userTemplate.cloneNode(true);
    userMessage.classList.remove('hidden');
    userMessage.querySelector('div').innerHTML = marked.parse(bible_handler(message));
    document.getElementById("response").appendChild(userMessage);
}

// Écoute les réponses de l'API
socket.on('response', function (data) {
    console.log(data);

    if ("thread_id" in data) {
        thread_id = data.thread_id;
        addHistory(firstUserInput, thread_id);
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

    if ("jw_links" in data) {
        // pub contains the url, title, and image of the pub to put on the left side of the message
        const jw_links = data.jw_links;

        for (var i = 0; i < jw_links.length; i++) {
            const jw_link = jw_links[i];

            const jwElement = document.createElement('button');
            jwElement.classList.add('mt-4');
            jwElement.onclick = function () {
                const modalTemplate = document.getElementById("modal-articles-template");
                const newModal = modalTemplate.cloneNode(true);
                newModal.id = "modal-" + Math.random().toString(36).substr(2, 9);

                for (var i = 0; i < jw_links.length; i++) {
                    const jw_link = jw_links[i];

                    const articleElement = document.createElement('a');
                    articleElement.classList.add('flex', 'items-center', 'mt-4', 'p-4', 'bg-white', 'dark:bg-neutral-800', 'rounded-lg', 'shadow-md', 'hover:shadow-lg', 'transition-shadow', 'duration-300');
                    articleElement.href = jw_link.url;
                    articleElement.target = "_blank";

                    const articleImage = document.createElement('img');
                    articleImage.src = jw_link.image;
                    articleImage.classList.add('w-12', 'h-12', 'mr-4', 'rounded-md', 'shadow');

                    const articleTitle = document.createElement('span');
                    articleTitle.innerText = jw_link.title;
                    articleTitle.classList.add('text-lg', 'font-semibold', 'text-gray-900', 'dark:text-gray-100');

                    articleElement.appendChild(articleImage);
                    articleElement.appendChild(articleTitle);

                    newModal.querySelector('.articles').appendChild(articleElement);
                }

                document.getElementById("body").appendChild(newModal);

                modal.init();
                modal.openModal(newModal.id);
            }
            jwElement.innerHTML = "<img src='" + jw_link.image + "' class='first:z-10 last:z-0 size-8 border-2 border-white rounded-full'>";

            document.getElementById("response").lastChild.querySelector('.links').appendChild(jwElement);
        }
    }

    if ("pub" in data) {
        // pub contains the url, title, and image of the pub to put on the left side of the message
        const pub = data.pub;
        const pubElement = document.createElement('a');
        pubElement.classList.add('mt-4');

        if (pub && "url" in pub && pub.url) {
            pubElement.href = pub.url;
            pubElement.target = "_blank";
        }

        pubElement.innerHTML = "<img src='" + pub.image + "' class='first:z-10 last:z-0 size-8 border-2 border-white rounded-full'>";

        document.getElementById("response").lastChild.querySelector('.links').appendChild(pubElement);
        
        console.log("publication: ", pub);
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
        if (data.status == "end") {
            startedMessaging = false;
            statusElement.innerText = "";

            var messages_containers = document.getElementById("response").children;

            for (let i = 0; i < messages_containers.length; i++) {
                const element = messages_containers[i];
                
                var responseElement = element.querySelector('.response');
                if (responseElement) {
                    var message = responseElement.innerHTML;
                    
                    responseElement.innerHTML = bible_handler(message);
                }
            }
        } else if (data.status == "in_progress") {
            statusElement.innerText = "...";
        } else if (data.status == "completed") {
            statusElement.innerText = "";
        } else if (data.status == "source_search") {
            statusElement.innerText = "Recherche d'informations dans la bibliothèque...";
        } else if (data.status == "function_call") {
            statusElement.innerText = "Recherche d'informations sur JW.ORG et WOL...";
        } else if (data.status == "new_chat_started") {
            // remove all messages
            document.getElementById("response").innerHTML = "";
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
}, { passive: true });

document.getElementById("user-input-placeholder").addEventListener('touchstart', function () {
    document.getElementById("user-input").focus();
}, { passive: true });

document.getElementById("user-input").addEventListener('blur', function () {
    window.scrollTo(0, document.body.scrollHeight);
});

document.getElementById("question-form").addEventListener('submit', function () {
    document.getElementById("user-input").blur();
});

// on closing webpage, disconnect socket
window.addEventListener('beforeunload', function () {
    socket.disconnect();
});


function closeModal() {
    document.getElementById("modal").classList.add("hidden");
}

function newChat() {
    socket.emit('action', "new_chat");
}