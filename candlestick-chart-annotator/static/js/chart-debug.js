/**
 * Chart Annotation Debugging Tool
 * 
 * This script adds tools to diagnose and fix issues with annotation display on charts.
 */

// Constants for local storage
const DEBUG_ENABLED_KEY = 'chart_debug_enabled';
const DEBUG_VISIBLE_KEY = 'chart_debug_visible';

// Check if debug is disabled by user preference
function isDebugEnabled() {
    return localStorage.getItem(DEBUG_ENABLED_KEY) !== 'false';
}

// Check if debug panel should be visible
function isDebugVisible() {
    return localStorage.getItem(DEBUG_VISIBLE_KEY) !== 'false';
}

// Set debug enabled/disabled state
function setDebugEnabled(enabled) {
    localStorage.setItem(DEBUG_ENABLED_KEY, enabled.toString());
}

// Set debug visible/hidden state
function setDebugVisible(visible) {
    localStorage.setItem(DEBUG_VISIBLE_KEY, visible.toString());
}

// Create main debug UI component
function createDebugUI() {
    // If debug is completely disabled, don't create UI
    if (!isDebugEnabled()) {
        console.log('Chart debug tools are disabled. To re-enable, call localStorage.removeItem("chart_debug_enabled") in the console.');
        return;
    }
    
    const debugContainer = document.createElement('div');
    debugContainer.id = 'chartDebugContainer';
    debugContainer.className = 'chart-debug-container';
    
    // Set initial visibility based on stored preference
    if (!isDebugVisible()) {
        debugContainer.classList.add('collapsed');
    }
    
    // Create toggle tab
    const toggleTab = document.createElement('div');
    toggleTab.className = 'chart-debug-toggle';
    toggleTab.innerHTML = isDebugVisible() ? '◀' : '▶';
    toggleTab.title = isDebugVisible() ? 'Hide debug panel' : 'Show debug panel';
    
    // Add toggle functionality
    toggleTab.addEventListener('click', function() {
        const isCurrentlyVisible = !debugContainer.classList.contains('collapsed');
        debugContainer.classList.toggle('collapsed');
        
        // Update toggle button text and title
        this.innerHTML = isCurrentlyVisible ? '▶' : '◀';
        this.title = isCurrentlyVisible ? 'Show debug panel' : 'Hide debug panel';
        
        // Store preference
        setDebugVisible(!isCurrentlyVisible);
    });
    
    // Create header with title and remove button
    const header = document.createElement('div');
    header.className = 'chart-debug-header';
    header.innerHTML = '<h4>Chart Debug Tools</h4>';
    
    // Add remove button to completely disable debug tools
    const removeButton = document.createElement('button');
    removeButton.className = 'chart-debug-remove-btn';
    removeButton.innerHTML = 'Remove Debug Tools';
    removeButton.title = 'Completely remove debug tools (refresh to restore)';
    
    removeButton.addEventListener('click', function() {
        if (confirm('This will completely remove the debug tools. You can restore them by refreshing the page.\n\nAre you sure you want to remove the debug tools?')) {
            // Set preference to disabled
            setDebugEnabled(false);
            
            // Remove the container
            document.body.removeChild(debugContainer);
            
            alert('Debug tools removed. Refresh the page to restore them if needed.');
        }
    });
    
    header.appendChild(removeButton);
    
    // Create content container
    const content = document.createElement('div');
    content.className = 'chart-debug-content';
    
    // Add status panel
    const statusPanel = document.createElement('div');
    statusPanel.className = 'chart-debug-panel';
    statusPanel.innerHTML = `
        <h5>Status</h5>
        <div class="status-items">
            <div class="status-item">
                <span class="status-label">Chart Initialized:</span>
                <span id="chart-status" class="status-value">Checking...</span>
            </div>
            <div class="status-item">
                <span class="status-label">Annotations Loaded:</span>
                <span id="annotations-status" class="status-value">Checking...</span>
            </div>
            <div class="status-item">
                <span class="status-label">Socket Connected:</span>
                <span id="socket-status" class="status-value">Checking...</span>
            </div>
        </div>
    `;
    
    // Add controls panel
    const controlsPanel = document.createElement('div');
    controlsPanel.className = 'chart-debug-panel';
    controlsPanel.innerHTML = `
        <h5>Controls</h5>
        <div class="debug-controls">
            <button id="refresh-annotations-btn" class="debug-btn">Refresh Annotations</button>
            <button id="create-test-annotation-btn" class="debug-btn">Create Test Annotation</button>
        </div>
    `;
    
    // Add debug info panel
    const infoPanel = document.createElement('div');
    infoPanel.className = 'chart-debug-panel';
    infoPanel.innerHTML = `
        <h5>Debug Info</h5>
        <div id="debugInfo" class="debug-info-content"></div>
    `;
    
    // Assemble the container
    content.appendChild(statusPanel);
    content.appendChild(controlsPanel);
    content.appendChild(infoPanel);
    
    debugContainer.appendChild(toggleTab);
    debugContainer.appendChild(header);
    debugContainer.appendChild(content);
    
    // Add debug container to the document
    document.body.appendChild(debugContainer);
    
    // Add CSS styles
    addDebugStyles();
    
    // Setup control handlers
    setupDebugControls();
    
    // Start status monitoring
    monitorStatus();
    
    return debugContainer;
}

// Add required CSS styles for the debug UI
function addDebugStyles() {
    if (document.getElementById('chart-debug-styles')) return;
    
    const styleTag = document.createElement('style');
    styleTag.id = 'chart-debug-styles';
    styleTag.textContent = `
        .chart-debug-container {
            position: fixed;
            top: 20%;
            left: 0;
            width: 300px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-left: none;
            border-radius: 0 8px 8px 0;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            z-index: 9999;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            transition: transform 0.3s ease;
        }
        
        .chart-debug-container.collapsed {
            transform: translateX(-100%);
        }
        
        .chart-debug-container.collapsed .chart-debug-toggle {
            transform: translateX(100%);
        }
        
        .chart-debug-toggle {
            position: absolute;
            top: 50%;
            right: -30px;
            width: 30px;
            height: 60px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-left: none;
            border-radius: 0 8px 8px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 18px;
            box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
            z-index: 9998;
        }
        
        .chart-debug-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background: #212529;
            color: white;
            border-radius: 0 8px 0 0;
        }
        
        .chart-debug-header h4 {
            margin: 0;
            font-size: 16px;
        }
        
        .chart-debug-remove-btn {
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .chart-debug-content {
            padding: 10px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .chart-debug-panel {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            margin-bottom: 10px;
            padding: 8px;
        }
        
        .chart-debug-panel h5 {
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 14px;
            color: #495057;
            border-bottom: 1px solid #e9ecef;
            padding-bottom: 5px;
        }
        
        .status-items {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
        }
        
        .status-label {
            font-weight: bold;
        }
        
        .status-value.success {
            color: #28a745;
        }
        
        .status-value.error {
            color: #dc3545;
        }
        
        .status-value.warning {
            color: #ffc107;
        }
        
        .debug-controls {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .debug-btn {
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            cursor: pointer;
        }
        
        .debug-btn:hover {
            background: #0069d9;
        }
        
        .debug-info-content {
            max-height: 150px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
            background: #f1f3f5;
            padding: 5px;
            border-radius: 3px;
        }
    `;
    
    document.head.appendChild(styleTag);
}

// Set up event handlers for debug control buttons
function setupDebugControls() {
    const refreshBtn = document.getElementById('refresh-annotations-btn');
    const testAnnotationBtn = document.getElementById('create-test-annotation-btn');
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            updateDebugInfo('Manual refresh requested');
            if (typeof socket !== 'undefined' && socket) {
                socket.emit('get_annotations');
                updateDebugInfo('Annotations refresh request sent');
            } else {
                updateDebugInfo('ERROR: Socket not available for refresh');
            }
        });
    }
    
    if (testAnnotationBtn) {
        testAnnotationBtn.addEventListener('click', function() {
            createTestAnnotation();
        });
    }
}

// Create a test annotation for debugging
function createTestAnnotation() {
    try {
        if (!window.currentStock || !window.currentDate) {
            updateDebugInfo('ERROR: No stock or date selected');
            return;
        }
        
        // Get the middle of the visible chart data
        let testDate = new Date();
        if (window.currentDate) {
            // Parse the date portion from currentDate
            const dateParts = window.currentDate.split('-');
            testDate = new Date(
                parseInt(dateParts[0]), 
                parseInt(dateParts[1]) - 1, 
                parseInt(dateParts[2]),
                12, 0, 0
            );
        }
        
        // Find a reasonable price if available
        let testPrice = 100;
        if (window.candlestickSeries && window.candlestickSeries.data) {
            const data = window.candlestickSeries.data();
            if (data && data.length > 0) {
                // Use the close price from the middle of the data set
                const midIndex = Math.floor(data.length / 2);
                testPrice = data[midIndex].close;
            }
        }
        
        // Create a test annotation
        const testAnnotation = {
            stock: window.currentStock,
            timestamp: testDate.toISOString(),
            price: testPrice,
            signal: 'long_entry',
            reason: 'Test annotation from debug tools'
        };
        
        updateDebugInfo('Creating test annotation: ' + JSON.stringify(testAnnotation));
        
        // Call the addAnnotation function if available
        if (typeof addAnnotation === 'function') {
            addAnnotation(testAnnotation);
            updateDebugInfo('Test annotation created');
        } else {
            updateDebugInfo('ERROR: addAnnotation function not available');
        }
    } catch (e) {
        updateDebugInfo('ERROR creating test annotation: ' + e.message);
    }
}

// Monitor status of various components
function monitorStatus() {
    // Check chart status
    function checkChartStatus() {
        const chartStatus = document.getElementById('chart-status');
        if (!chartStatus) return;
        
        if (window.chart || window.Plotly) {
            chartStatus.textContent = 'Ready';
            chartStatus.className = 'status-value success';
        } else {
            chartStatus.textContent = 'Not Ready';
            chartStatus.className = 'status-value error';
        }
    }
    
    // Check annotations status
    function checkAnnotationsStatus() {
        const annotationsStatus = document.getElementById('annotations-status');
        if (!annotationsStatus) return;
        
        if (window.annotations || window.currentAnnotations) {
            const count = (window.annotations || window.currentAnnotations || []).length;
            annotationsStatus.textContent = `Loaded (${count})`;
            annotationsStatus.className = 'status-value success';
        } else {
            annotationsStatus.textContent = 'Not Loaded';
            annotationsStatus.className = 'status-value warning';
        }
    }
    
    // Check socket status
    function checkSocketStatus() {
        const socketStatus = document.getElementById('socket-status');
        if (!socketStatus) return;
        
        if (typeof socket !== 'undefined' && socket) {
            if (socket.connected) {
                socketStatus.textContent = 'Connected';
                socketStatus.className = 'status-value success';
            } else {
                socketStatus.textContent = 'Disconnected';
                socketStatus.className = 'status-value error';
            }
        } else {
            socketStatus.textContent = 'Not Available';
            socketStatus.className = 'status-value error';
        }
    }
    
    // Run all checks immediately
    checkChartStatus();
    checkAnnotationsStatus();
    checkSocketStatus();
    
    // Then set up interval to update every 3 seconds
    setInterval(() => {
        checkChartStatus();
        checkAnnotationsStatus();
        checkSocketStatus();
    }, 3000);
}

// Add a debug message to the info panel
window.updateDebugInfo = function(message) {
    console.log("Debug:", message);
    const debugEl = document.getElementById('debugInfo');
    if (debugEl) {
        const timestamp = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.textContent = `[${timestamp}] ${message}`;
        debugEl.appendChild(entry);
        debugEl.scrollTop = debugEl.scrollHeight;
    }
};

// Initialize debug UI when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only create the debug UI if it's enabled
    if (isDebugEnabled()) {
        setTimeout(createDebugUI, 1000);
    } else {
        console.log('Chart debug tools are disabled. To re-enable, call localStorage.removeItem("chart_debug_enabled") in the console.');
    }
}); 