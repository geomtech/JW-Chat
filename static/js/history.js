function history() {
    modal.init();
    modal.openModal("historyModal");

    const historyList = document.getElementById("historyList");
    historyList.innerHTML = "";

    fetch("/api/v1/history")
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                const noHistory = document.createElement("span");
                noHistory.innerHTML = "No history found.";
                historyList.appendChild(noHistory);
            } else {
                data.forEach(history => {
                    const historyItem = document.createElement("button");
                    historyItem.classList.add("bg-gray-200", "hover:bg-gray-300", "text-left", "p-2", "w-full", "text-sm", "text-gray-800", "rounded-md", "focus:outline-none", "focus:ring-2", "focus:ring-gray-500", "focus:ring-offset-2", "focus:ring-offset-gray-200");
                    historyItem.innerHTML = history.title;
                    historyItem.onclick = function () {
                        retrieveMessages(history.thread_id);
                    };
                    historyList.appendChild(historyItem);
                });
            }
        });
}

function retrieveMessages(threadId) {
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
            document.getElementById("closeHistory").click();
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