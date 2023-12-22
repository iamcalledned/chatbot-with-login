// Define functions in the global scope
let socket; // Declare the WebSocket outside of the functions
let reconnectInterval = 1000; // Start with 1 second
const MAX_RECONNECT_INTERVAL = 30000; // Max interval 30 seconds


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

function initializeShoppingList() {
    $('#shopping-list-button').click(function() {
        $('#shopping-list-overlay').removeClass('hidden');
    });

    $('#close-shopping-list').click(function() {
        $('#shopping-list-overlay').addClass('hidden');
    });
}

function initializeWebSocket(sessionId) {
    if (!socket || socket.readyState === WebSocket.CLOSED) {
        socket = new WebSocket('wss://www.whattogrill.com:8055');

        socket.onopen = function() {
            displayConnectionMessage('Connected to the server.', 'success');
            reconnectInterval = 1000; // Reset reconnect interval on successful connection
            socket.send(JSON.stringify({ session_id: sessionId }));
            localStorage.setItem('session_id', sessionId);
            console.log('WebSocket connected!');
        };

        socket.onclose = function(event) {
            displayConnectionMessage('Connection lost. Reconnecting...', 'warning');
            setTimeout(reconnectWebSocket, reconnectInterval);
            reconnectInterval = Math.min(reconnectInterval * 2, MAX_RECONNECT_INTERVAL); // Exponential backoff
            console.log('WebSocket closed:', event);
        };


        socket.onmessage = function(event) {
            var msg = JSON.parse(event.data);
        
            if (msg.action === 'ping') {
                // Respond with pong when a ping message is received
                console.log('Received ping message');
                
                socket.send(JSON.stringify({'action': 'pong'}));
            
            } else if (msg.action === 'shopping_list_update') {
                updateShoppingListUI(msg.shoppingList);
            
            } else if (msg.action === 'force_logout') {
                // Redirect to login page
                window.location.href = '/login'; // Adjust URL as needed

            } else if (msg.action === 'redirect_login') {
                // Optionally display an alert or notification to the user
                alert('Your session is invalid. Please log in again.');
        
                // Redirect to the login page
                window.location.href = '/login';  // Adjust this URL as needed
                          
            
            } else if (msg.action === 'recipe_saved') {
                // Check if the recipe was successfully saved and show a notification
                if (msg.status === 'success') {
                    $('.save-recipe-button').text('Recipe Saved'); // Change button text
                    $('.save-recipe-button').addClass('recipe-saved-button'); // Add a new class for styling (optional)
                    $('.save-recipe-button').prop('disabled', true); // Disable the button
                    showNotificationBubble('Recipe saved');
                } else {
                    // Handle other statuses, like errors
                    showNotificationBubble('Failed to save recipe');
                }
            } else {
                hideTypingIndicator();
                var messageElement;
                if (msg.type === 'recipe') {
                    messageElement = $('<div class="message-bubble recipe-message">'); // Add 'recipe-message' class
                    var messageContent = $('<div class="message-content">').html(msg.response);
                    var saveButton = $('<button class="save-recipe-button" data-recipe-id="' + msg.recipe_id + '">Save Recipe</button>');
                    messageElement.append(messageContent, saveButton);
                } else {
                    messageElement = $('<div class="message bot">').html(msg.response);
                }
                $('#messages').append(messageElement);
                $('#messages').scrollTop($('#messages')[0].scrollHeight);
            }
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket Error:', error);
        };

        
    }
}

function sendMessage() {
    var message = $('#message-input').val();
    if (message.trim().length > 0) {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({'message': message}));
            $('#message-input').val('');
            var userMessageElement = $('<div class="message user">').text('You: ' + message);
            $('#messages').append(userMessageElement);
            showTypingIndicator();
            $('#messages').scrollTop($('#messages')[0].scrollHeight);
        } else {
            console.error('WebSocket is not open. ReadyState:', socket.readyState);
        }
    }
}

$(document).ready(function() {
    let sessionId = getSessionIdFromUrl();
    if (sessionId) {
        initializeWebSocket(sessionId);
        initializeShoppingList();
    } else {
        window.location.href = '/'; // Redirect to login if no session ID
    }

    $('#send-button').click(sendMessage);
    $('#message-input').keypress(function(e) {
        if (e.which == 13) {
            sendMessage();
            return false; // Prevent form submission
        }
    });

    hideTypingIndicator();

    
    $(document).on('mouseenter', '.save-recipe-button', function() {
        $(this).append($('<span class="tooltip">Click to add this to your recipe box!</span>'));
    }).on('mouseleave', '.save-recipe-button', function() {
        $(this).find('.tooltip').remove();
    });

    $(document).on('click', '.save-recipe-button', function() {
        var recipeId = $(this).data('recipe-id')
        var messageContent = $(this).siblings('.message-content');
        if (messageContent.length) {
            var recipeContent = messageContent.text();
            

            if (socket && socket.readyState === WebSocket.OPEN) {
                var saveCommand = {
                    action: 'save_recipe',
                    content: recipeId
                };
                socket.send(JSON.stringify(saveCommand));
                
                
            } else {
                console.error('WebSocket is not open.');
            
            }
        } else {
            console.error("No .message-content found alongside the Save Recipe button.");
        }
    
    
    });
    
    window.addEventListener('load', () => {
        function updateOnlineStatus() {
            if (navigator.onLine) {
                reconnectWebSocket(); // Attempt to reconnect WebSocket if not connected
            } else {
                displayConnectionMessage('You are offline. Trying to reconnect...', 'warning');
            }
        }
    
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
    });
    
    
    document.addEventListener("visibilitychange", handleVisibilityChange);
    
    document.querySelector('.hamburger-menu').addEventListener('click', function() {
        document.querySelector('.options-menu').classList.toggle('show');
    });

    document.getElementById('logout').addEventListener('click', function() {
        sessionStorage.clear();
        window.location.href = '/login'; // Adjust the URL as needed
    });
});

function addToShoppingList(item) {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({'action': 'add_to_shopping_list', 'item': item}));
    } else {
        console.error('WebSocket is not open. ReadyState:', socket.readyState);
    }
}

function removeItemFromShoppingList(item) {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({'action': 'remove_from_shopping_list', 'item': item}));
    }
}

function updateShoppingListUI(shoppingList) {
    $('#shopping-list').empty();
    shoppingList.forEach(function(item) {
        var listItem = $('<li></li>').text(item.name);
        if (item.checked) {
            listItem.addClass('checked');
        }
        $('#shopping-list').append(listItem);
    });
}

function showOverlay(title, content) {
    const overlay = $('<div class="overlay"></div>');
    const overlayContent = $('<div class="overlay-content"></div>');
    overlayContent.append($('<h2></h2>').text(title), $('<p></p>').text(content), $('<button>Close</button>').click(function() { overlay.remove(); }));
    overlay.append(overlayContent);
    $('body').append(overlay);
}
 
function logout() {
    sessionStorage.clear();
    window.location.href = '/login'; // Adjust the URL as needed
}
function showNotificationBubble(message) {
    var bubble = $('<div class="notification-bubble">' + message + '</div>');
    
    $('body').append(bubble);
    bubble.fadeIn(200).delay(3000).fadeOut(200, function() {
        $(this).remove(); // Remove the bubble from the DOM after it fades out
    });
}
function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
        console.log("Page is now visible");
        // Reconnect WebSocket if needed
        let sessionId = getSessionIdFromUrl();
        if (sessionId && (!socket || socket.readyState === WebSocket.CLOSED)) {
            initializeWebSocket(sessionId);
        }
    } else if (document.visibilityState === 'hidden') {
        console.log("Page is now hidden");
        // Additional actions when the page is not visible (if needed)
    }
}
function displayConnectionMessage(message, type) {
    // Display a connection message to the user
    // Implement this function to show messages using a banner or similar UI element
    console.log(`${type.toUpperCase()}: ${message}`);
}

function reconnectWebSocket() {
    let sessionId = getSessionIdFromUrl();
    if (sessionId && (!socket || socket.readyState === WebSocket.CLOSED)) {
        initializeWebSocket(sessionId);
    }
}