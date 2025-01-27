function history() {
    modal.init();
    modal.openModal("historyModal");

    const historyList = document.getElementById("historyList");
    const historyListWithElements = historyList.cloneNode(true);

    fetch("/api/v1/history")
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                const noHistory = document.createElement("span");
                noHistory.innerHTML = "No history found.";
                historyList.appendChild(noHistory);
            } else {
                historyListWithElements.innerHTML = "";
                data.forEach(history => {
                    const historyItem = document.createElement("li");
                    historyItem.classList.add("flex", "flex-row", "items-center", "gap-x-2", "w-full", "history-item");

                    const historyButton = document.createElement("button");
                    historyButton.type = "button";
                    historyButton.classList.add("flex-1", "text-left", "bg-neutral-200", "hover:bg-neutral-300", 'dark:bg-neutral-800', 'dark:hover:bg-neutral-700', "p-2", "rounded", "m-1", "truncate");
                    historyButton.innerHTML = history.title;
                    historyButton.onclick = function () {
                        retrieveMessages(history.thread_id);
                    };

                    const historyDeleteButton = document.createElement("button");
                    historyDeleteButton.type = "button";
                    historyDeleteButton.classList.add("bg-red-500", "hover:bg-red-600", "p-2", "rounded", "m-1");
                    historyDeleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-trash"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 7l16 0" /><path d="M10 11l0 6" /><path d="M14 11l0 6" /><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /></svg>';
                    historyDeleteButton.onclick = function () {
                        if (confirm("Are you sure you want to delete this history? This will remove the messages from JW Chat servers as well as OpenAI servers.")) {
                            fetch("/api/v1/history/" + history.thread_id, {
                                method: "DELETE"
                            }).then(() => {
                                historyItem.remove();
                            });
                        }
                    };

                    historyItem.appendChild(historyButton);
                    historyItem.appendChild(historyDeleteButton);
                    historyListWithElements.appendChild(historyItem);
                });
            }
        })
        .finally(() => {
            historyList.replaceWith(historyListWithElements);
        });
}

function retrieveMessages(threadId) {
    document.getElementById("closeHistory").click();

    fetch("/api/v1/history/" + threadId)
        .then(response => response.json())
        .then(data => {
            console.log(data);
            const messages = data;
            
            const response = document.getElementById("response");
            response.innerHTML = "";

            messages.forEach(message => {
                if (message.role == "user") {
                    newUserMessage(message.content);
                } else if (message.role == "assistant") {
                    newMessage(message.content);
                }
            });
        })
        .finally(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });
}

function addHistory(userInput, threadId) {
    console.log("addHistory", userInput, threadId);
    fetch("/api/v1/history", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user_input: userInput,
            thread_id: threadId
        })
    });
}