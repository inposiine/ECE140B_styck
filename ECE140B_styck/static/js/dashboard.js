import("https://unpkg.com/i18next@21.6.16/dist/umd/i18next.min.js").then(() => {
    window.i18next = i18next;
    i18next.init({
        lng: 'en',
        debug: true,
        resources: {
            en: {
                translation: {
                    dashboardTitle: "IoT Stick Dashboard",
                    logout: "Logout",
                    deviceStatus: "Device Status",
                    userInfo: "User Information",
                    userWeight: "User Weight (kg)",
                    update: "Update",
                    forceWarningTitle: "Force Warning",
                    forceWarning: "Warning: Excessive force detected! Please adjust your walking pattern.",
                    forceNormal: "Force levels are normal.",
                    gaitAnalysis: "Gait Analysis Data",
                    selectDate: "Select Date",
                    selectSession: "Select Session",
                    selectSessionOption: "Select a session..."
                }
            },
            zh: {
                translation: {
                    dashboardTitle: "IoT 棒仪表板",
                    logout: "登出",
                    deviceStatus: "设备状态",
                    userInfo: "用户信息",
                    userWeight: "用户体重 (公斤)",
                    update: "更新",
                    forceWarningTitle: "力量警告",
                    forceWarning: "警告：检测到过大的力量！请调整您的步态。",
                    forceNormal: "力量水平正常。",
                    gaitAnalysis: "步态分析数据",
                    selectDate: "选择日期",
                    selectSession: "选择会话",
                    selectSessionOption: "选择一个会话..."
                }
            },
            es: {
                translation: {
                    dashboardTitle: "Panel de IoT Stick",
                    logout: "Cerrar sesión",
                    deviceStatus: "Estado del dispositivo",
                    userInfo: "Información del usuario",
                    userWeight: "Peso del usuario (kg)",
                    update: "Actualizar",
                    forceWarningTitle: "Advertencia de fuerza",
                    forceWarning: "¡Advertencia: fuerza excesiva detectada! Por favor, ajuste su forma de caminar.",
                    forceNormal: "Los niveles de fuerza son normales.",
                    gaitAnalysis: "Datos de análisis de la marcha",
                    selectDate: "Seleccionar fecha",
                    selectSession: "Seleccionar sesión",
                    selectSessionOption: "Seleccione una sesión..."
                }
            },
            fr: {
                translation: {
                    dashboardTitle: "Tableau de bord IoT Stick",
                    logout: "Se déconnecter",
                    deviceStatus: "Statut de l'appareil",
                    userInfo: "Informations utilisateur",
                    userWeight: "Poids de l'utilisateur (kg)",
                    update: "Mettre à jour",
                    forceWarningTitle: "Avertissement de force",
                    forceWarning: "Attention : force excessive détectée ! Veuillez ajuster votre démarche.",
                    forceNormal: "Les niveaux de force sont normaux.",
                    gaitAnalysis: "Données d'analyse de la marche",
                    selectDate: "Sélectionner une date",
                    selectSession: "Sélectionner une session",
                    selectSessionOption: "Sélectionnez une session..."
                }
            }
        }
    }, function(err, t) {
        updateContent();
    });

    // Update all elements with data-i18n attribute
    function updateContent() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            el.textContent = i18next.t(el.getAttribute('data-i18n'));
        });
    }

    // Listen for language toggle
    document.getElementById('languageToggle').addEventListener('change', function(e) {
        i18next.changeLanguage(e.target.value, updateContent);
    });

    // Initial update
    updateContent();
});

let currentPosition;
let gaitChart;
let currentSessionData = [];
let userWeight = 100; // Default user weight
let userId = null; // To store user ID
let forceThresholdKg = parseFloat(localStorage.getItem('forceThresholdKg')) || 5; // Default 5kg
let stepChart;
let currentUserId = 2;

// Function to load user data from localStorage
function loadUserData() {
    const storedWeight = localStorage.getItem('userWeight');
    if (storedWeight) {
        userWeight = parseFloat(storedWeight);
        document.getElementById('userWeight').value = userWeight; // Pre-fill form if exists
    }
    userId = localStorage.getItem('userId');
    const username = localStorage.getItem('username');
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
            datasets: [
                {
                    label: 'Peak Force (kg)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Peak Force (kg)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Step Index'
                    }
                }
            }
        }
    });
}

// Update the chart with new data
function updateChart(steps) {
    // steps is now the step data array
    const labels = steps.map((step, i) => `Step ${i + 1}`);
    const peakForces = steps.map(step => step.peak_force);
    gaitChart.data.labels = labels;
    gaitChart.data.datasets[0].data = peakForces;
    gaitChart.update();

    // Check for excessive force (15% of user's weight)
    const maxForce = peakForces.length > 0 ? Math.max(...peakForces) : 0;
    const forceWarning = document.getElementById('forceWarning');
    const forceNormal = document.getElementById('forceNormal');
    
    if (userWeight > 0 && maxForce > forceThresholdKg) {
        forceWarning.style.display = 'block';
        forceNormal.style.display = 'none';
        forceWarning.textContent = `Warning: Force (${maxForce.toFixed(2)} kg) exceeds your set threshold (${forceThresholdKg.toFixed(2)} kg).`;
    } else if (userWeight > 0) {
        forceWarning.style.display = 'none';
        forceNormal.style.display = 'block';
        forceNormal.textContent = `Force is within safe limits. Threshold: (${forceThresholdKg.toFixed(2)} kg).`;
    } else {
        forceWarning.style.display = 'none';
        forceNormal.style.display = 'block';
        forceNormal.textContent = 'Please set your weight to activate force monitoring.';
    }
}

// Helper to get userId from localStorage
function getUserId() {
    return 2;
}

// Handle device switch
const deviceSwitch = document.getElementById('deviceSwitch');
deviceSwitch.addEventListener('change', async (e) => {
    const isOn = e.target.checked;
    const userId = localStorage.getItem('userId');
    
    console.log('Current userId from localStorage:', userId); // Debug log
    
    if (!userId) {
        console.error('No userId found in localStorage'); // Debug log
        alert("Please log in again. Your session may have expired.");
        window.location.href = '/';
        return;
    }

    const parsedUserId = parseInt(userId, 10);
    console.log('Parsed userId:', parsedUserId); // Debug log
    
    if (isNaN(parsedUserId)) {
        console.error('Invalid userId format:', userId); // Debug log
        alert("Please log in again. Your session may have expired.");
        window.location.href = '/';
        return;
    }

    try {
        const requestBody = {
            status: isOn,
            user_id: parsedUserId
        };
        console.log('Sending request with body:', requestBody); // Debug log
        
        const response = await fetch('/api/device-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        const responseData = await response.json();
        console.log('Server response:', responseData); // Debug log

        if (!response.ok) {
            throw new Error(responseData.detail || 'Failed to update device status');
        }
    } catch (error) {
        console.error('Error updating device status:', error);
        alert('Failed to update device status. Please try again.');
        e.target.checked = !isOn; // Revert the switch
    }
});

// Handle user weight form - This will now update the displayed weight and localStorage
// The server endpoint /api/user-weight could be used to update the DB if desired for persistence beyond the session
document.getElementById('userInfoForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const newWeight = parseFloat(document.getElementById('userWeight').value);
    if (isNaN(newWeight) || newWeight <= 0) {
        alert("Please enter a valid weight.");
        return;
    }
    userWeight = newWeight;
    localStorage.setItem('userWeight', userWeight);
    alert("User weight updated locally. Chart will use this new weight.");
    updateChart(currentSessionData); // Re-evaluate warnings with new weight

    // Optionally, send to server to update database if you have a user session
    // if (userId) { ... fetch('/api/user-weight', { body: JSON.stringify({ userId: userId, weight: userWeight }) ... } ...)
});

// Handle date selection
document.getElementById('dateSelector').addEventListener('change', async (e) => {
    const date = e.target.value;
    const userId = getUserId();
    console.log('Fetching sessions for date:', date, 'user_id:', userId);
    
    try {
        const response = await fetch(`/api/sessions?date=${date}&user_id=${userId}`);
        const sessions = await response.json();
        console.log('Received sessions:', sessions);
        
        const sessionSelector = document.getElementById('sessionSelector');
        sessionSelector.innerHTML = '<option value="">Select a session...</option>';
        
        if (sessions.length === 0) {
            console.log('No sessions found for this date');
            const option = document.createElement('option');
            option.value = "";
            option.textContent = "No sessions available for this date";
            sessionSelector.appendChild(option);
        } else {
            sessions.forEach(session => {
                console.log('Adding session to selector:', session);
                const option = document.createElement('option');
                option.value = session.id;
                option.textContent = `${session.label}: ${session.startTime} - ${session.endTime}`;
                sessionSelector.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error fetching sessions:', error);
        alert('Error loading sessions. Please try again.');
    }
});

// Handle session selection
document.getElementById('sessionSelector').addEventListener('change', async (e) => {
    const sessionId = e.target.value;
    if (!sessionId) return;
    const userId = getUserId();

    // Fetch step data (for both charts)
    const stepResponse = await fetch(`/api/steps/${sessionId}?user_id=${userId}`);
    const steps = await stepResponse.json();
    console.log("Fetched steps:", steps);
    displayGaitMetrics(steps);
    updateStepChart(steps);
    updateChart(steps);

    // Fetch posture alerts (new)
    const alertResponse = await fetch(`/api/posture-alerts/${sessionId}?user_id=${userId}`);
    const alerts = await alertResponse.json();
    console.log("Fetched posture alerts:", alerts);
    displayPostureAlerts(alerts);
});

function displayGaitMetrics(steps) {
    console.log("displayGaitMetrics called with:", steps);
    // Example: display in a div with id="gaitMetrics"
    const metricsDiv = document.getElementById('gaitMetrics');
    if (!steps.length) {
        metricsDiv.innerHTML = "No step data.";
        return;
    }
    const stepCount = steps.length;
    const avgGaitSpeed = steps.reduce((a, b) => a + b.gait_speed, 0) / stepCount;
    const cadence = 60 / (1 / avgGaitSpeed); // Convert gait speed to steps per minute
    const avgForce = steps.reduce((a, b) => a + b.peak_force, 0) / stepCount;
    // Gait symmetry: stddev of peak_force or gait_speed
    const forceStd = Math.sqrt(steps.reduce((a, b) => a + Math.pow(b.peak_force - avgForce, 2), 0) / stepCount);
    metricsDiv.innerHTML = `
        <b>Step Count:</b> ${stepCount}<br>
        <b>Cadence:</b> ${cadence.toFixed(1)} steps/min<br>
        <b>Avg Gait Speed:</b> ${avgGaitSpeed.toFixed(2)} m/s<br>
        <b>Avg Peak Force:</b> ${avgForce.toFixed(2)} kg<br>
        <b>Step Force StdDev (Symmetry):</b> ${forceStd.toFixed(2)} kg
    `;
}

// WebSocket connection for real-time data
let ws;
function connectWebSocket() {
    ws = new WebSocket('ws://' + window.location.host + '/ws');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'force') {
            currentSessionData.push({
                timestamp: Date.now(),
                force_value: data.value
            });
            // Keep only last 100 data points
            if (currentSessionData.length > 100) {
                currentSessionData.shift();
            }
            updateChart(currentSessionData);
        }
    };
    
    ws.onclose = () => {
        setTimeout(connectWebSocket, 1000);
    };
}

function initStepChart() {
    const ctx = document.getElementById('stepChart').getContext('2d');
    stepChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Gait Speed (m/s)',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    yAxisID: 'y1',
                },
                {
                    label: 'Step Duration (s)',
                    data: [],
                    borderColor: 'rgb(255, 205, 86)',
                    backgroundColor: 'rgba(255, 205, 86, 0.2)',
                    yAxisID: 'y2',
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y1: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Gait Speed (m/s)' }
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Step Duration (s)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function updateStepChart(steps) {
    if (!stepChart) return;
    const labels = steps.map((step, i) => `Step ${i + 1}`);
    const gaitSpeeds = steps.map(step => step.gait_speed);
    // Calculate step durations (difference in timestamp between steps, in seconds)
    const stepDurations = steps.map((step, i, arr) => {
        if (i === 0) return null;
        const prev = arr[i - 1];
        return (new Date(step.timestamp) - new Date(prev.timestamp)) / 1000.0;
    });
    // Remove the first null value for step durations
    const durations = stepDurations.slice(1);
    const durationLabels = labels.slice(1);
    // Pad the first value to keep arrays aligned
    const paddedDurations = [null, ...durations];

    stepChart.data.labels = labels;
    stepChart.data.datasets[0].data = gaitSpeeds;
    stepChart.data.datasets[1].data = paddedDurations;
    stepChart.update();
    console.log("updateStepChart called with:", steps);
    console.log("Step durations:", paddedDurations);
}

function displayPostureAlerts(alerts) {
    const alertDiv = document.getElementById('postureAlerts');
    if (!alerts.length) {
        alertDiv.innerHTML = "No posture anomalies detected.";
        return;
    }

    // Group by anomaly type
    const grouped = {};
    alerts.forEach(alert => {
        if (!grouped[alert.anomaly]) grouped[alert.anomaly] = [];
        grouped[alert.anomaly].push(alert);
    });

    // Format output
    let html = '';
    Object.keys(grouped).forEach(anomaly => {
        const count = grouped[anomaly].length;
        html += `<b style="color:red">${anomaly.replace('_', ' ')}:</b> ${count} times<br>`;
        html += grouped[anomaly].map(alert => {
            // Convert timestamp to LA time
            const date = new Date(alert.timestamp);
            // If your backend returns UTC, convert to LA time:
            const laTime = date.toLocaleString("en-US", { timeZone: "America/Los_Angeles" });
            return `<span style="margin-left:1em;font-size:0.95em;">${laTime} (value: ${alert.value})</span>`;
        }).join('<br>');
        html += '<br><br>';
    });

    alertDiv.innerHTML = html;
}

// Initialize everything when the page loads
window.onload = () => {
    loadUserData(); // Load user data first
    initChart();
    connectWebSocket();
    initStepChart();
    
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    const dateSelector = document.getElementById('dateSelector');
    dateSelector.value = today;
    console.log('Setting default date to:', today);
    
    // Trigger the date change event to load sessions
    dateSelector.dispatchEvent(new Event('change'));
    
    updateChart(currentSessionData); // Initial chart update (might be empty)
    const input = document.getElementById('forceThresholdInput');
    if (input) input.value = forceThresholdKg;
    getAISuggestion();

    // Add event listener for refresh button
    document.getElementById('refreshSuggestion').addEventListener('click', getAISuggestion);
};

document.getElementById('updateForceThresholdBtn').addEventListener('click', async () => {
    const input = document.getElementById('forceThresholdInput');
    let value = parseFloat(input.value);
    if (isNaN(value) || value <= 0) {
        alert("Please enter a valid force threshold in kg.");
        return;
    }
    forceThresholdKg = value;
    localStorage.setItem('forceThresholdKg', forceThresholdKg);
    alert(`Force alert threshold updated to ${value} kg.`);
    updateChart(currentSessionData); // Re-evaluate warnings

    // Send to backend to update device
    await fetch('/api/force-threshold', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(forceThresholdKg)
    });
});

// Function to get AI suggestion
async function getAISuggestion() {
    console.log("getAISuggestion called");
    try {
        const response = await fetch('/api/suggestion', {
            method: 'POST',
            body: new URLSearchParams({ user_id: 2 }),
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        if (!response.ok) {
            throw new Error('Failed to get suggestion');
        }
        const data = await response.json();
        document.getElementById('aiSuggestion').textContent = data.suggestion;
    } catch (error) {
        console.error('Error getting AI suggestion:', error);
        document.getElementById('aiSuggestion').textContent = 'Error getting suggestion. Please try again.';
    }
} 
