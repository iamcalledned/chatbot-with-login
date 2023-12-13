// overlay.js

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

// Export the showOverlay function
export { showOverlay };
