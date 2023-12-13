// event-handlers.js

// Function to set up event handlers for DOM elements
function setupEventHandlers() {
    // Event handler for the hamburger menu button
    document.querySelector('.hamburger-menu').addEventListener('click', function() {
        document.querySelector('.options-menu').classList.toggle('show');
    });

    // Event handler for the "About" button
    document.getElementById('about').addEventListener('click', function() {
        showOverlay('About', 'This is some information about our service...');
    });

    // Event handler for handling Enter key press in message input
    $('#message-input').keypress(function(e) {
        if (e.which == 13) { // Enter key has a keycode of 13
            sendMessage();
            return false; // Prevent form submission
        }
    });

    // Event handler for the send button click
    $('#send-button').click(function() {
        sendMessage();
    });
}

// Export the setupEventHandlers function
export { setupEventHandlers };
