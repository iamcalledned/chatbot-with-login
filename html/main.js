// main.js

import { fetchSessionData } from './session.js';
import { initializeWebSocket } from './websocket.js';
import { showOverlay } from './overlay.js';
import { setupEventHandlers } from './event-handlers.js';

// Function to show the typing indicator
function showTypingIndicator() {
    $('#typing-container').show();
}

// Function to hide the typing indicator
function hideTypingIndicator() {
    $('#typing-container').hide();
}

// Function to send a message via WebSocket
function sendMessage(message) {
    // Code to send messages via WebSocket
}

// Initialize WebSocket connection and other functionality on document ready
$(document).ready(function() {
    fetchSessionData()
        .then(function(data) {
            initializeWebSocket(data.sessionId);
        })
        .catch(function(error) {
            console.error('Error fetching session data:', error);
        });

    // Initialize event handlers
    setupEventHandlers();
});

// Add any additional code for your application here
