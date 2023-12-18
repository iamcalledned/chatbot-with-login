let socket; // Declare the WebSocket outside of the functions
let sessionId;

function showTypingIndicator() {
    $('#typing-container').show();
}

function hideTypingIndicator() {
    $('#typing-container').hide();
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
            socket.send(JSON.stringify({ session_id: sessionId }));
            console.log('WebSocket connected!');
        };
                socket.onmessage = function(event) {
            var msg = JSON.parse(event.data);
            
            if (msg.error && msg.error === 'Invalid session') {
                alert("Session expired. Please log in again.");
                localStorage.removeItem('session_id');
                window.location.href = '/login';
            }

            if (msg.action === 'shopping_list_update') {
                updateShoppingListUI(msg.shoppingList);
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
                    var saveButton = $('<button class="save-recipe-button">Save Recipe</button>');
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

        socket.onclose = function(event) {
            console.log('WebSocket closed:', event);
            if (!event.wasClean) {
                alert("Lost connection to the server. Please log in again.");
                localStorage.removeItem('session_id');
                window.location.href = '/login';
            }
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
    // Assigning to the global variable, not redeclaring it
    sessionId = localStorage.getItem('session_id');
    if (sessionId) {
        // ... (rest of your code)
    } else {
        window.location.href = '/login'; // Redirect to login if no session ID
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
        $(this).append($('<span class="tooltip">Click to save this recipe!</span>'));
    }).on('mouseleave', '.save-recipe-button', function() {
        $(this).find('.tooltip').remove();
    });

    $(document).on('click', '.save-recipe-button', function() {
        var messageContent = $(this).siblings('.message-content');
        if (messageContent.length) {
            var recipeContent = messageContent.text();
            

            if (socket && socket.readyState === WebSocket.OPEN) {
                var saveCommand = {
                    action: 'save_recipe',
                    content: recipeContent
                };
                socket.send(JSON.stringify(saveCommand));
                
                
            } else {
                console.error('WebSocket is not open.');
            
            }
        } else {
            console.error("No .message-content found alongside the Save Recipe button.");
        }
    
    
    });
    

    document.querySelector('.hamburger-menu').addEventListener('click', function() {
        document.querySelector('.options-menu').classList.toggle('show');
    });

    let sessionId = localStorage.getItem('session_id');

    if (sessionId) {
        fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            localStorage.removeItem('session_id');
            sessionStorage.clear();
            window.location.href = '/login';
        })
        .catch(error => {
            console.error('Error during logout:', error);
        });
    } else {
        sessionStorage.clear();
        window.location.href = '/login';
    }
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
    // Here we are using the global variable, not redeclaring it
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        localStorage.removeItem('session_id');
        sessionStorage.clear();
        window.location.href = '/login';
    })
    .catch(error => {
        console.error('Error during logout:', error);
    });
}

function checkSessionValidity() {
    // Use the global `sessionId` variable
    if (!sessionId) {
        window.location.href = '/login';
        return;
    }

    fetch('/validate_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status !== 'valid') {
            window.location.href = '/login';
        }
    })
    .catch(error => {
        console.error('Error checking session:', error);
        window.location.href = '/login';
    });
}
 
document.getElementById('logout').addEventListener('click', function() {
    sessionStorage.clear();
    window.location.href = '/login'; // Adjust the URL as needed
});


// Attach the logout function to the logout button
document.getElementById('logout-button').addEventListener('click', logout);
function showNotificationBubble(message) {
    var bubble = $('<div class="notification-bubble">' + message + '</div>');
    
    $('body').append(bubble);
    bubble.fadeIn(200).delay(3000).fadeOut(200, function() {
        $(this).remove(); // Remove the bubble from the DOM after it fades out
    });
}
document.addEventListener('DOMContentLoaded', (event) => {
    let logoutElement = document.getElementById('logout');
    if (logoutElement) {
        logoutElement.addEventListener('click', function() {
            // Your logout logic here
        });
    }

    let logoutButtonElement = document.getElementById('logout-button');
    if (logoutButtonElement) {
        logoutButtonElement.addEventListener('click', logout);
    }
});