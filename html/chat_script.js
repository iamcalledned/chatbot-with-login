// Define the functions in the global scope
function showTypingIndicator() {
    $('#typing-container').show();
}

function hideTypingIndicator() {
    $('#typing-container').hide();
}

// Function to fetch session data
function fetchSessionData() {
    $.getJSON('/get_session_data', function(data) {
        console.log('Session data:', data);
        // Call initializeWebSocket here with the retrieved session_id
        initializeWebSocket(data.sessionId);
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Error fetching session data:', textStatus, errorThrown);
    });
}

// Function to initialize WebSocket connection
function initializeWebSocket(sessionId) {
    var socket = new WebSocket('wss://www.whattogrill.com:8055');
    socket.onopen = function() {
        console.log('WebSocket connected!');
        // Send session_id when the WebSocket connection is established
        socket.send(JSON.stringify({ session_id: sessionId }));
        // Store session_id in local storage
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
        // Basic logging
        console.log('WebSocket closed:', event);
    
        // Detailed logging
        console.log('Close event properties:');
        console.log('  - wasClean:', event.wasClean); // Indicates whether the connection was closed cleanly or not
        console.log('  - code:', event.code); // Numeric code indicating the status code explaining why the connection has been closed
        console.log('  - reason:', event.reason); // Human-readable string explaining why the connection was closed
        console.log('  - type:', event.type); // Type of the event ('close' in this case)
        console.log('  - target URL:', event.target.url); // URL of the WebSocket connection
        console.log('  - readyState:', event.target.readyState); // The readyState of the WebSocket at the time it was closed
    
        // Additional diagnostics
        if (!event.wasClean) {
            console.warn('WebSocket closed unexpectedly.');
        }
    
    // Reconnect after 5 seconds
    setTimeout(function() {
        initializeWebSocket(sessionId); // Pass sessionId and userId here
    }, 5000);

    };

    function sendMessage() {
        var message = $('#message-input').val();
        if (message.trim().length > 0) {
            if (socket.readyState === WebSocket.OPEN) {
                // Send message in the correct format
                socket.send(JSON.stringify({'message': message}));
                $('#message-input').val('');
                // ... rest of the sendMessage function ...
            }
        }
    }

    $('#send-button').click(function() {
        sendMessage();
    });

    $('#message-input').keypress(function(e) {
        if (e.which == 13) { // Enter key has a keycode of 13
            sendMessage();
            return false; // Prevent form submission
        }
    });

    // Initially, hide the typing indicator
    hideTypingIndicator();

    // Expose the sendMessage function to the global scope
    window.sendMessage = sendMessage;
}

// Use the document ready function to initialize WebSocket connection
$(document).ready(function() {
    fetchSessionData(); // This will call initializeWebSocket after fetching session data


// Function to show the overlay with dynamic content
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
});
document.addEventListener('DOMContentLoaded', function() {
document.querySelector('.hamburger-menu').addEventListener('click', function() {
    document.querySelector('.options-menu').classList.toggle('show');
});
document.addEventListener('DOMContentLoaded', (event) => {
let sessionId = localStorage.getItem('session_id');
if (sessionId) {
    // Re-establish websocket connection with the session ID
    // replace 'initWebSocket' with your actual function to initialize the websocket connection
    initWebSocket(sessionId);
} else {
    // Redirect to login or show an error message
    window.location.href = '/login'; // Redirect to login
}
});


document.getElementById('about').addEventListener('click', function() {
    showOverlay('About', 'This is some information about our service...');
});
});