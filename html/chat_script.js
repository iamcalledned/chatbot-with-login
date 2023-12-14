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

function initializeWebSocket(sessionId) {
    const socketUrl = `wss://www.whattogrill.com/ws?session_id=${sessionId}`;
    if (!socket || socket.readyState === WebSocket.CLOSED) {
        socket = new WebSocket(socketUrl);

        socket.onopen = function() {
            console.log('WebSocket connected!');
            socket.send(JSON.stringify({ session_id: sessionId }));
            localStorage.setItem('session_id', sessionId);
        };

        socket.onmessage = function(event) {
            var msg = JSON.parse(event.data);
            hideTypingIndicator();
            $('#messages').append($('<div class="message bot">').html(msg.response));
            $('#messages').scrollTop($('#messages')[0].scrollHeight);
        };

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
    } else {
        window.location.href = '/'; // Redirect to login if no session ID
    }
});

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
    $('body').append(overlay);
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('.hamburger-menu').addEventListener('click', function() {
        document.querySelector('.options-menu').classList.toggle('show');
    });

    document.getElementById('about').addEventListener('click', function() {
        showOverlay('About', 'This is some information about our service...');
    });
});
