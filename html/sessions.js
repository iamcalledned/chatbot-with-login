// session.js

// Function to fetch session data
function fetchSessionData() {
    return new Promise(function(resolve, reject) {
        $.getJSON('/get_session_data', function(data) {
            // Process session data and resolve the promise
            initializeWebSocket(data.sessionId);
            console.log('Session data:', data);
            resolve(data);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error('Error fetching session data:', textStatus, errorThrown);
            reject(errorThrown);
        });
    });
}

// Export the fetchSessionData function
export { fetchSessionData };
