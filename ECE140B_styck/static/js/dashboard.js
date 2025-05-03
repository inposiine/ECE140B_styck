let map;
let directionsService;
let directionsRenderer;
let currentPosition;
let gaitChart;
let currentSessionData = [];
let userWeight = 0;
const forceThreshold = 0.7; // 70% of user's weight

// Initialize the map and services
function initMap() {
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();
    
    // Default center (will be updated with device location)
    const defaultCenter = { lat: 0, lng: 0 };
    
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 15,
        center: defaultCenter,
    });
    
    directionsRenderer.setMap(map);
    
    // Try to get current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                map.setCenter(currentPosition);
            },
            () => {
                console.error('Error getting current location');
            }
        );
    }
}

// Calculate and display route
function calculateRoute() {
    if (!currentPosition) {
        alert('Current location not available');
        return;
    }

    const destination = document.getElementById('destination').value;
    
    const request = {
        origin: currentPosition,
        destination: destination,
        travelMode: 'WALKING'
    };

    directionsService.route(request, (result, status) => {
        if (status === 'OK') {
            directionsRenderer.setDirections(result);
        } else {
            alert('Could not calculate directions: ' + status);
        }
    });
}

// Update device status
function updateDeviceStatus(isConnected) {
    const statusIndicator = document.getElementById('deviceStatus');
    const statusText = document.getElementById('deviceStatusText');
    
    statusIndicator.className = 'status-indicator ' + (isConnected ? 'connected' : 'disconnected');
    statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
}

// Update emergency button status
function updateEmergencyStatus(isTriggered) {
    const emergencyIndicator = document.getElementById('emergencyStatus');
    const emergencyText = document.getElementById('emergencyStatusText');
    
    emergencyIndicator.className = 'status-indicator ' + (isTriggered ? 'warning' : 'connected');
    emergencyText.textContent = isTriggered ? 'TRIGGERED!' : 'Not Triggered';
}

// Update pressure data
function updatePressureData(pressure) {
    document.getElementById('pressureValue').textContent = `${pressure} kPa`;
    document.getElementById('pressureUpdateTime').textContent = new Date().toLocaleTimeString();
}

// Update battery level
function updateBatteryLevel(percentage) {
    const batteryLevel = document.getElementById('batteryLevel');
    const batteryText = document.getElementById('batteryPercentage');
    
    batteryLevel.style.width = `${percentage}%`;
    batteryText.textContent = `${percentage}%`;
    
    if (percentage < 20) {
        batteryLevel.className = 'progress-bar bg-danger';
    } else if (percentage < 50) {
        batteryLevel.className = 'progress-bar bg-warning';
    } else {
        batteryLevel.className = 'progress-bar bg-success';
    }
}

// Simulate device updates (replace with actual WebSocket connection)
function simulateDeviceUpdates() {
    // Simulate device connection status
    setInterval(() => {
        updateDeviceStatus(Math.random() > 0.1);
    }, 5000);

    // Simulate emergency button status
    setInterval(() => {
        updateEmergencyStatus(Math.random() > 0.9);
    }, 3000);

    // Simulate pressure data updates
    setInterval(() => {
        const pressure = (Math.random() * 100 + 900).toFixed(1);
        updatePressureData(pressure);
    }, 2000);

    // Simulate battery updates
    setInterval(() => {
        const batteryLevel = Math.floor(Math.random() * 100);
        updateBatteryLevel(batteryLevel);
    }, 10000);
}

// Initialize the chart
function initChart() {
    const ctx = document.getElementById('gaitChart').getContext('2d');
    gaitChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Force (kg)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Force (kg)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time (seconds)'
                    }
                }
            }
        }
    });
}

// Update the chart with new data
function updateChart(data) {
    const labels = data.map((_, index) => index);
    const values = data.map(point => point.force);
    
    gaitChart.data.labels = labels;
    gaitChart.data.datasets[0].data = values;
    gaitChart.update();

    // Check for excessive force
    const maxForce = Math.max(...values);
    const forceWarning = document.getElementById('forceWarning');
    const forceNormal = document.getElementById('forceNormal');
    
    if (maxForce > userWeight * forceThreshold) {
        forceWarning.style.display = 'block';
        forceNormal.style.display = 'none';
    } else {
        forceWarning.style.display = 'none';
        forceNormal.style.display = 'block';
    }
}

// Handle device switch
document.getElementById('deviceSwitch').addEventListener('change', (e) => {
    const isOn = e.target.checked;
    // Send device status to server
    fetch('/api/device-status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: isOn }),
    });
});

// Handle user weight form
document.getElementById('userInfoForm').addEventListener('submit', (e) => {
    e.preventDefault();
    userWeight = parseFloat(document.getElementById('userWeight').value);
    // Send user weight to server
    fetch('/api/user-weight', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ weight: userWeight }),
    });
});

// Handle date selection
document.getElementById('dateSelector').addEventListener('change', async (e) => {
    const date = e.target.value;
    // Fetch sessions for selected date
    const response = await fetch(`/api/sessions?date=${date}`);
    const sessions = await response.json();
    
    const sessionSelector = document.getElementById('sessionSelector');
    sessionSelector.innerHTML = '<option value="">Select a session...</option>';
    
    sessions.forEach(session => {
        const option = document.createElement('option');
        option.value = session.id;
        option.textContent = `${session.startTime} - ${session.endTime}`;
        sessionSelector.appendChild(option);
    });
});

// Handle session selection
document.getElementById('sessionSelector').addEventListener('change', async (e) => {
    const sessionId = e.target.value;
    if (!sessionId) return;
    
    // Fetch session data
    const response = await fetch(`/api/session-data/${sessionId}`);
    const data = await response.json();
    currentSessionData = data;
    updateChart(data);
});

// WebSocket connection for real-time data
let ws;
function connectWebSocket() {
    ws = new WebSocket('ws://' + window.location.host + '/ws');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'force') {
            currentSessionData.push({
                timestamp: Date.now(),
                force: data.value
            });
            updateChart(currentSessionData);
        }
    };
    
    ws.onclose = () => {
        setTimeout(connectWebSocket, 1000);
    };
}

// Initialize everything when the page loads
window.onload = () => {
    initMap();
    initChart();
    connectWebSocket();
}; 