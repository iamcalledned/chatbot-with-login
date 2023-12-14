// websocket.js

// Function to initialize WebSocket connection
function initializeWebSocket(sessionId, userId) {
    var socket = new WebSocket('wss://www.whattogrill.com:8055');
    socket.onopen = function() {
        console.log('WebSocket connected!', userId);
        // Send session_id when the WebSocket connection is established
        socket.send(JSON.stringify({ session_id: sessionId }));
        // Store session_id in local storage
        localStorage.setItem('session_id', sessionId);
    };

    socket.onmessage = function(event) {
        var msg = JSON.parse(event.data);
        hideTypingIndicator(); // Assuming hideTypingIndicator() is available in your module
        $('#messages').append($('<div class="message bot">').html(msg.response));
        $('#messages').scrollTop($('#messages')[0].scrollHeight);
    };

    socket.onerror = function(error) {
        console.error('WebSocket Error:', error);
    };

    socket.onclose = function(event) {
        // WebSocket close handling code
        handleWebSocketClose(event); // Assuming handleWebSocketClose() is available in your module
    }

    // Function to send a message via WebSocket
    function sendMessage(message) {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ 'message': message }));
            $('#message-input').val('');
            $('#messages').append($('<div class="message user">').text('You: ' + message));
            showTypingIndicator(); // Assuming showTypingIndicator() is available in your module
            $('#messages').scrollTop($('#messages')[0].scrollHeight);
        } else {
            console.error('WebSocket is not open. ReadyState:', socket.readyState);
        }
    }

    // Expose the sendMessage function
    return sendMessage;
}

// Export the initializeWebSocket function
export { initializeWebSocket };
