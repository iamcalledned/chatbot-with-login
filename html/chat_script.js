// Define functions in the global scope
let socket; // Declare the WebSocket outside of the functions
let reconnectInterval = 1000; // Start with 1 second
const MAX_RECONNECT_INTERVAL = 30000; // Max interval 30 seconds

function showTypingIndicator() {
    $('#typing-container').removeClass('hidden');
}

function hideTypingIndicator() {
    $('#typing-container').addClass('hidden');
}

function initializeShoppingList() {
    $('#shopping-list-button').click(function() {
        $('#shopping-list-overlay').removeClass('hidden');
    });

    $('#close-shopping-list').click(function() {
        $('#shopping-list-overlay').addClass('hidden');
    });
}

function initializeRecipeBox() {
    $('#recipe-box-button').click(function() {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'get_user_recipes' }));
        }
    });

    $('#close-recipe-box').click(function() {
        $('#recipe-box-overlay').addClass('hidden');
    });
}

function displayRecentMessages(messages) {
    messages.reverse().forEach(function(message) {
        var messageElement;

        if (message.MessageType === 'user') {
            messageElement = $('<div class="message user">').text('You: ' + message.Message);
        } else if (message.MessageType === 'bot') {
            messageElement = $('<div class="message bot">').text('Ned: ' + message.Message);
        } else {
            messageElement = $('<div class="message">').text(message.Message);
        }
        messageElement.attr('data-timestamp', message.Timestamp);

        $('#messages').append(messageElement);
    });

    $('#messages').scrollTop($('#messages')[0].scrollHeight);
}

function displayMoreMessages(messages) {
    messages.forEach(function(message) {
        var messageElement;

        if (message.MessageType === 'user') {
            messageElement = $('<div class="message user">').text('You: ' + message.Message);
        } else if (message.MessageType === 'bot') {
            messageElement = $('<div class="message bot">').text('Ned: ' + message.Message);
        } else {
            messageElement = $('<div class="message">').text(message.Message);
        }

        messageElement.attr('data-timestamp', message.Timestamp);

        $('#messages').prepend(messageElement);
    });
}

function getOldestMessageTimestamp() {
    var oldestMessage = $('#messages .message:first');
    return oldestMessage.data('timestamp');
}

function initializeWebSocket() {
    if (!socket || socket.readyState === WebSocket.CLOSED) {
        socket = new WebSocket('wss://www.iamcalledned.ai/ws');

        socket.onopen = function() {
            var messageObject = {
                action: 'load_messages'
            };

            socket.send(JSON.stringify(messageObject));
            reconnectInterval = 1000;
        };

        socket.onclose = function(event) {
            setTimeout(reconnectWebSocket, reconnectInterval);
            reconnectInterval = Math.min(reconnectInterval * 2, MAX_RECONNECT_INTERVAL);
        };

        socket.onmessage = function(event) {
            var msg = JSON.parse(event.data);

            if (msg.action === 'ping') {
                var pongMessage = {
                    action: 'pong'
                };
                socket.send(JSON.stringify(pongMessage));
            } else if (msg.action === 'shopping_list_update') {
                updateShoppingListUI(msg.shoppingList);
            } else if (msg.action === 'recent_messages') {
                displayRecentMessages(msg.messages);
            } else if (msg.action === 'older_messages') {
                displayMoreMessages(msg.messages);
            } else if (msg.action === 'user_recipes_list') {
                displayUserRecipes(msg.recipes);
            } else if (msg.action === 'force_logout') {
                window.location.href = '/login';
            } else if (msg.action === 'redirect_login') {
                alert('Your session is invalid. Please log in again.');
                window.location.href = '/login';
            } else if (msg.action === 'recipe_saved') {
                if (msg.status === 'success') {
                    $('.save-recipe-button').text('Recipe Saved');
                    $('.save-recipe-button').addClass('recipe-saved-button');
                    $('.save-recipe-button').prop('disabled', true);
                    showNotificationBubble('Recipe saved');
                } else {
                    showNotificationBubble('Failed to save recipe');
                }
            } else if (msg.action === 'recipe_printed') {
                var recipeHtml = msg.data;
                var printWindow = window.open('', '_blank');
                printWindow.document.write('<html><head><title>Print Recipe</title></head><body>');
                printWindow.document.write(recipeHtml);
                printWindow.document.write('</body></html>');
                printWindow.onload = function() {
                    printWindow.print();
                    printWindow.close();
                };
            } else {
                hideTypingIndicator();
                var messageElement;
                if (msg.type === 'recipe') {
                    messageElement = $('<div class="message-bubble recipe-message">');
                    var messageContent = $('<div class="message-content">').html(msg.response);
                    var printButton = $('<button class="print-recipe-button" data-recipe-id="' + msg.recipe_id + '">Print Recipe</button>');
                    var saveButton = $('<button class="save-recipe-button" data-recipe-id="' + msg.recipe_id + '">Save Recipe</button>');
                    messageElement.append(messageContent, saveButton, printButton);
                } else if (msg.type === 'shopping_list') {
                    messageElement = $('<div class="message-bubble shopping-list-message">');
                    var messageContent = $('<div class="message-content">').html(msg.response);
                    var saveButton = $('<button class="save-shopping-list-button">Save Shopping List</button>');
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
            var messageObject = {
                action: 'chat_message',
                message: message
            };

            socket.send(JSON.stringify(messageObject));
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
    initializeWebSocket();
    initializeShoppingList();
    initializeRecipeBox();

    $('#send-button').click(sendMessage);
    $('#message-input').keypress(function(e) {
        if (e.which == 13) {
            sendMessage();
            return false;
        }
    });

    hideTypingIndicator();

    $(document).on('mouseenter', '.save-recipe-button', function() {
        if ($(this).prop('disabled')) {
        } else {
            $(this).append($('<span class="tooltip">Click to add this to your recipe box!</span>'));
        }
    }).on('mouseleave', '.save-recipe-button', function() {
        $(this).find('.tooltip').remove();
    });

    $(document).on('click', '.save-recipe-button', function() {
        var recipeId = $(this).data('recipe-id');
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

    $(document).on('click', '.save-shopping-list-button', function() {
        var recipeId = $(this).data('recipe-id');
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

    $(document).on('click', '.print-recipe-button', function() {
        var recipeId = $(this).data('recipe-id');
        var messageContent = $(this).siblings('.message-content');

        if (messageContent.length) {
            var recipeContent = messageContent.text();

            if (socket && socket.readyState === WebSocket.OPEN) {
                var PrintCommand = {
                    action: 'print_recipe',
                    content: recipeId
                };
                socket.send(JSON.stringify(PrintCommand));
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
                reconnectWebSocket();
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
        window.location.href = '/login';
    });

    document.getElementById('messages').addEventListener('scroll', function() {
        if (this.scrollTop === 0) {
            loadMoreMessages();
        }
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

function loadMoreMessages() {
    var lastMessageTimestamp = getOldestMessageTimestamp();
    if (lastMessageTimestamp) {
        socket.send(JSON.stringify({
            action: 'load_more_messages',
            last_loaded_timestamp: lastMessageTimestamp
        }));
    }
}

function displayUserRecipes(recipes) {
    const recipeBox = $('#recipe-box');
    recipeBox.empty();

    recipes.forEach(function(recipe) {
        const recipeItem = $('<li class="flex justify-between items-center p-2 bg-base-200 rounded-lg">');
        const recipeTitle = $('<span class="font-medium">').text(recipe.title);
        const removeButton = $('<button class="btn btn-sm btn-error">Remove</button>');

        recipeTitle.click(function() {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ action: 'print_recipe', content: recipe.recipe_id }));
            }
        });

        removeButton.click(function() {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ action: 'remove_recipe', content: recipe.recipe_id }));
            }
            recipeItem.remove();
        });

        recipeItem.append(recipeTitle, removeButton);
        recipeBox.append(recipeItem);
    });

    $('#recipe-box-overlay').removeClass('hidden');
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
    window.location.href = '/login';
}

function showNotificationBubble(message) {
    var bubble = $('<div class="notification-bubble">' + message + '</div>');

    $('body').append(bubble);
    bubble.fadeIn(200).delay(3000).fadeOut(200, function() {
        $(this).remove();
    });
}

function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
        if (!socket || socket.readyState === WebSocket.CLOSED) {
            initializeWebSocket();
        }
    } else if (document.visibilityState === 'hidden') {
    }
}

function reconnectWebSocket() {
    if (!socket || socket.readyState === WebSocket.CLOSED) {
        initializeWebSocket();
    }
}