// Define functions in the global scope
let socket; // Declare the WebSocket outside of the functions

function showTypingIndicator() {
    $('#typing-container').show();
}

function hideTypingIndicator() {
    $('#typing-container').hide();
}

function getSessionIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('sessionId');
}

// Initialize the shopping list UI
function initializeShoppingList() {
    $('#shopping-list-button').click(function() {
        $('#shopping-list-overlay').removeClass('hidden');
    });

    $('#close-shopping-list').click(function() {
        $('#shopping-list-overlay').addClass('hidden');
    });

    // Add more functions here to handle adding items, checking them off, etc.
    // You will likely need to send and receive specific messages through the WebSocket for these actions.
}

function initializeWebSocket(sessionId) {
    if (!socket || socket.readyState === WebSocket.CLOSED) {
        // Only create a new WebSocket if it doesn't exist or is closed
        socket = new WebSocket('wss://www.whattogrill.com:8055');

        socket.onopen = function() {
            console.log('WebSocket connected!');
            socket.send(JSON.stringify({ session_id: sessionId }));
            localStorage.setItem('session_id', sessionId);
        };
        initializeShoppingList();

        socket.onmessage = function(event) {
            var msg = JSON.parse(event.data);
            if (msg.action === 'shopping_list_update') {
                // Update the UI with the new shopping list data
                updateShoppingListUI(msg.shoppingList);
            } else {
            hideTypingIndicator();
            var messageElement = $('<div class="message bot">').html(msg.response);
        // Check if the message type is 'recipe' and append a Save button if it is
        if (msg.type === 'recipe') {
            var saveButton = $('<button class="save-recipe-button">Save Recipe</button>');
            saveButton.click(function() {
                // Logic to handle saving the recipe
                console.log('Save Recipe button clicked');
                // You can also pass the recipe text or an identifier to the save function
            });
            messageElement.append(saveButton);
        }

        $('#messages').append(messageElement);
        $('#messages').scrollTop($('#messages')[0].scrollHeight);
        };

    }

        socket.onerror = function(error) {
            console.error('WebSocket Error:', error);
        };

        socket.onclose = function(event) {
            console.log('WebSocket closed:', event);
            if (!event.wasClean) {
                console.warn('WebSocket closed unexpectedly.');
            }
            // Don't initialize WebSocket here; it will be initialized only once
        };
    }
}
function sendMessage() {
    var message = $('#message-input').val();
    if (message.trim().length > 0) {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({'message': message}));
            $('#message-input').val('');
            $('#messages').append($('<div class="message user">').text('You: ' + message));
            showTypingIndicator();
            $('#messages').scrollTop($('#messages')[0].scrollHeight);
        } else {
            console.error('WebSocket is not open. ReadyState:', socket.readyState);
        }
    }
}


    $('#send-button').click(sendMessage);
    $('#message-input').keypress(function(e) {
        if (e.which == 13) { // Enter key has a keycode of 13
            sendMessage();
            return false; // Prevent form submission
        }
    });

    hideTypingIndicator();


// Use the document ready function to initialize WebSocket connection
$(document).ready(function() {
    let sessionId = getSessionIdFromUrl();
    if (sessionId) {
        initializeWebSocket(sessionId);
        initializeShoppingList();
    } else {
        window.location.href = '/'; // Redirect to login if no session ID
    }
});

function addToShoppingList(item) {
    // Send a message to the WebSocket server to add an item to the shopping list
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({'action': 'add_to_shopping_list', 'item': item}));
    } else {
        console.error('WebSocket is not open. ReadyState:', socket.readyState);
    }
}
function removeItemFromShoppingList(item) {
    // Send a message to remove the item from the shopping list
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({'action': 'remove_from_shopping_list', 'item': item}));
    }
}


function showOverlay(title, content) {
    const overlay = $('<div class="overlay"></div>');
    const overlayContent = $('<div class="overlay-content"></div>');
    const overlayTitle = $('<h2></h2>').text(title);
    const overlayText = $('<p></p>').text(content);
    const closeButton = $('<button>Close</button>');

    closeButton.click(function() {
        overlay.remove();
    });

    overlayContent.append(overlayTitle, overlayText, closeButton);
    overlay.append(overlayContent);
    overlay.append(overlayContent);
    $('body').append(overlay);
}

function logout() {
    // Example: Clear session storage and redirect to login page
    sessionStorage.clear();
    window.location.href = '/login'; // Adjust the URL as needed
}
function updateShoppingListUI(shoppingList) {
    // Clear the existing list
    $('#shopping-list').empty();

    // Add the new items to the list
    shoppingList.forEach(function(item) {
        var listItem = $('<li></li>').text(item.name);
        if (item.checked) {
            listItem.addClass('checked');
        }
        // Append additional buttons/actions for each item here
        $('#shopping-list').append(listItem);
    });
}



document.addEventListener('DOMContentLoaded', function() {
    console.log("DOMContentLoaded");

    document.querySelector('.hamburger-menu').addEventListener('click', function() {
        console.log("Hamburger clicked");
        document.querySelector('.options-menu').classList.toggle('show');
    });

    // Event listener for Logout button
    document.getElementById('logout').addEventListener('click', function() {
        console.log("Logout clicked");
        logout();
    });
});
