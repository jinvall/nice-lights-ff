$(document).ready(function() {
    $('#convoyTable').DataTable({
        "order": [[0, "desc"]],
        "pageLength": 50
    });
    $('#hitsTable').DataTable({
        "order": [[0, "desc"]],
        "pageLength": 50
    });
    $('#detailsTable').DataTable({
        "order": [[0, "desc"]],
        "pageLength": 50
    });
});

const socket = io();
socket.on('new_data', function(data) {
    // Update table and charts with new data
    // Add code to handle real-time updates
    console.log('New data received:', data);
});
