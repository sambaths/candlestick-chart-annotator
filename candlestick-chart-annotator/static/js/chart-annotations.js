// Function to update chart annotations
function updateChartAnnotations(annotations) {
    console.log("Updating chart annotations");
    
    try {
        if (!window.Plotly || !document.getElementById('candlestick-chart')) {
            console.warn("Plotly or chart container not available");
            return;
        }
        
        const currentStock = window.currentStock;
        const currentDate = window.currentDate;
        
        if (!currentStock || !currentDate) {
            console.warn("No stock or date selected for annotations");
            return;
        }
        
        // Filter annotations for current stock and date
        const relevantAnnotations = annotations.filter(annotation => {
            try {
                // Match stock
                const matchesStock = annotation.stock === currentStock;
                
                // Parse timestamp
                let timestamp;
                if (annotation.timestamp) {
                    timestamp = new Date(annotation.timestamp);
                    // Check if valid date
                    if (isNaN(timestamp.getTime())) {
                        console.warn("Invalid timestamp:", annotation.timestamp);
                        return false;
                    }
                    
                    // Extract date part for comparison
                    const annotationDate = timestamp.toISOString().split('T')[0];
                    const matchesDate = annotationDate === currentDate;
                    
                    return matchesStock && matchesDate;
                }
                return false;
            } catch (e) {
                console.error("Error filtering annotation:", e, annotation);
                return false;
            }
        });
        
        console.log(`Found ${relevantAnnotations.length} relevant annotations for ${currentStock} on ${currentDate}`);
        
        // Create annotation shapes
        const shapes = [];
        const annotations = [];
        
        relevantAnnotations.forEach(annotation => {
            try {
                // Parse timestamp
                const timestamp = new Date(annotation.timestamp);
                const price = parseFloat(annotation.price);
                
                if (isNaN(timestamp.getTime()) || isNaN(price)) {
                    console.warn("Invalid annotation data:", annotation);
                    return;
                }
                
                // Set color and symbol type based on signal
                let markerColor;
                let markerSymbol;
                
                switch(annotation.signal) {
                    case 'long_entry':
                        markerColor = '#2ca02c'; // Green
                        markerSymbol = 'triangle-up';
                        break;
                    case 'long_exit':
                        markerColor = '#1f77b4'; // Blue
                        markerSymbol = 'triangle-down';
                        break;
                    case 'short_entry':
                        markerColor = '#d62728'; // Red
                        markerSymbol = 'triangle-down';
                        break;
                    case 'short_exit':
                        markerColor = '#ff7f0e'; // Orange
                        markerSymbol = 'triangle-up';
                        break;
                    default:
                        markerColor = '#7f7f7f'; // Gray
                        markerSymbol = 'circle';
                }
                
                // Add a marker annotation
                annotations.push({
                    x: timestamp,
                    y: price,
                    xref: 'x',
                    yref: 'y',
                    text: getSignalDisplayName(annotation.signal), // Use our helper function
                    showarrow: true,
                    arrowhead: 2,
                    arrowsize: 1,
                    arrowwidth: 2,
                    arrowcolor: markerColor,
                    ax: 0,
                    ay: -40,
                    bordercolor: markerColor,
                    borderwidth: 2,
                    borderpad: 4,
                    bgcolor: 'white',
                    opacity: 0.8,
                    visible: true,
                    textposition: 'top center'
                });
                
                // Add a shape for the point
                shapes.push({
                    type: 'circle',
                    xref: 'x',
                    yref: 'y',
                    x0: timestamp,
                    y0: price - 3,
                    x1: timestamp,
                    y1: price + 3,
                    fillcolor: markerColor,
                    line: {
                        color: markerColor
                    }
                });
                
            } catch (e) {
                console.error("Error creating annotation shape:", e, annotation);
            }
        });
        
        console.log(`Created ${shapes.length} annotation shapes and ${annotations.length} labels`);
        
        // Update the chart layout with these shapes
        if (window.Plotly) {
            // Note: Setting showlegend to false for all annotation markers
            Plotly.relayout('candlestick-chart', {
                shapes: shapes,
                annotations: annotations,
                showlegend: false
            });
        }
        
    } catch (error) {
        console.error("Error in updateChartAnnotations:", error);
    }
}

// Function to create manual annotation markers as DOM elements
function createManualAnnotationMarkers(annotations) {
    console.log('Creating manual annotation markers');
    
    // First, remove any existing manual markers
    document.querySelectorAll('.manual-annotation-marker').forEach(el => el.remove());
    
    // Find the chart container - try both chart types
    const chartContainer = document.getElementById('candlestick-chart') || document.getElementById('stockChart');
    if (!chartContainer) {
        console.error('No chart container found');
        return;
    }
    
    // Make sure the container has position relative
    chartContainer.style.position = 'relative';
    
    // Create overlay container for markers if it doesn't exist
    let markerContainer = document.getElementById('annotation-markers-container');
    if (!markerContainer) {
        markerContainer = document.createElement('div');
        markerContainer.id = 'annotation-markers-container';
        markerContainer.style.position = 'absolute';
        markerContainer.style.top = '0';
        markerContainer.style.left = '0';
        markerContainer.style.width = '100%';
        markerContainer.style.height = '100%';
        markerContainer.style.pointerEvents = 'none';
        markerContainer.style.zIndex = '1000';
        chartContainer.appendChild(markerContainer);
    } else {
        // Clear existing markers
        markerContainer.innerHTML = '';
    }
    
    // Process each annotation
    annotations.forEach((annotation, index) => {
        try {
            // Try to parse the timestamp
            const timestamp = new Date(annotation.timestamp || annotation.formatted_timestamp);
            
            // Skip invalid timestamps
            if (isNaN(timestamp.getTime())) {
                console.warn('Invalid timestamp for annotation:', annotation);
                return;
            }
            
            // Determine color and marker type based on signal
            let color, markerType;
            
            switch(annotation.signal) {
                case 'long_entry':
                    color = '#2ca02c';  // Green
                    markerType = 'triangle-up';
                    break;
                case 'long_exit':
                    color = '#1f77b4';  // Blue
                    markerType = 'triangle-down';
                    break;
                case 'short_entry':
                    color = '#d62728';  // Red
                    markerType = 'triangle-up';
                    break;
                case 'short_exit':
                    color = '#ff7f0e';  // Orange
                    markerType = 'triangle-down';
                    break;
                default:
                    color = '#7f7f7f';  // Gray
                    markerType = 'circle';
            }
            
            // Create marker element
            const marker = document.createElement('div');
            marker.className = 'manual-annotation-marker';
            marker.style.position = 'absolute';
            marker.style.zIndex = '1001';
            marker.style.pointerEvents = 'auto';
            marker.style.cursor = 'pointer';
            marker.title = `${annotation.signal} at ${annotation.formatted_timestamp || annotation.timestamp}`;
            
            // Position it based on the time (for demo purposes, distribute them evenly)
            // In a real implementation, you'd need to map the timestamp to x position
            marker.style.left = `${(index + 1) * (100 / (annotations.length + 1))}%`;
            marker.style.top = '10%';  // Near the top of the chart
            
            // Create the triangle or circle
            if (markerType === 'triangle-up') {
                marker.innerHTML = `
                    <div style="width: 0; height: 0; 
                         border-left: 10px solid transparent;
                         border-right: 10px solid transparent;
                         border-bottom: 20px solid ${color};"></div>
                `;
            } else if (markerType === 'triangle-down') {
                marker.innerHTML = `
                    <div style="width: 0; height: 0; 
                         border-left: 10px solid transparent;
                         border-right: 10px solid transparent;
                         border-top: 20px solid ${color};"></div>
                `;
            } else {
                marker.innerHTML = `
                    <div style="width: 20px; height: 20px; 
                         border-radius: 50%;
                         background-color: ${color};"></div>
                `;
            }
            
            // Add tooltip with annotation details
            marker.addEventListener('mouseover', () => {
                const tooltip = document.createElement('div');
                tooltip.className = 'annotation-tooltip';
                tooltip.style.position = 'absolute';
                tooltip.style.backgroundColor = 'white';
                tooltip.style.border = '1px solid #ccc';
                tooltip.style.padding = '8px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
                tooltip.style.zIndex = '1002';
                tooltip.style.left = marker.style.left;
                tooltip.style.top = 'calc(' + marker.style.top + ' + 25px)';
                tooltip.innerHTML = `
                    <div><strong>${annotation.signal}</strong></div>
                    <div>Time: ${annotation.formatted_timestamp || annotation.timestamp}</div>
                    <div>Price: ${annotation.price || 'N/A'}</div>
                    <div>Reason: ${annotation.reason || 'N/A'}</div>
                `;
                markerContainer.appendChild(tooltip);
                
                marker.addEventListener('mouseout', () => {
                    tooltip.remove();
                });
            });
            
            markerContainer.appendChild(marker);
            
        } catch (e) {
            console.error('Error creating marker for annotation:', e, annotation);
        }
    });
    
    console.log('Created manual markers for annotations');
}

// Add event listener for chart creation
document.addEventListener('plotly_afterplot', function() {
    if (typeof currentAnnotations !== 'undefined') {
        updateChartAnnotations(currentAnnotations);
    }
});

// Function to create annotation from selected point
function createAnnotationFromSelectedPoint(point, signal, reason = '') {
    if (!point || !point.timestamp) {
        console.error('Invalid point data for annotation:', point);
        showNotification('Invalid point data for annotation', 'error');
        return;
    }
    
    console.log('Creating annotation from point:', point);
    
    // Ensure timestamp is a proper date
    let timestamp;
    try {
        if (typeof point.timestamp === 'string') {
            timestamp = new Date(point.timestamp);
        } else if (point.timestamp instanceof Date) {
            timestamp = point.timestamp;
        } else {
            console.error('Invalid timestamp format:', point.timestamp);
            showNotification('Invalid timestamp format', 'error');
            return;
        }
        
        // Validate the timestamp
        if (isNaN(timestamp.getTime())) {
            console.error('Invalid timestamp value:', timestamp);
            showNotification('Invalid timestamp value', 'error');
            return;
        }
    } catch (e) {
        console.error('Error processing timestamp:', e, point.timestamp);
        showNotification('Error processing timestamp', 'error');
        return;
    }
    
    console.log('Parsed timestamp:', timestamp);
    
    // Create the annotation data
    const annotationData = {
        timestamp: timestamp.toISOString(),
        stock: point.symbol || currentStock, // Fallback to global currentStock if not in point
        signal: signal,
        price: point.price || point.close,
        reason: reason
    };
    
    console.log('Annotation data prepared:', annotationData);
    
    // Call the add annotation function
    addAnnotation(annotationData);
}

// Helper function to get the currently selected point
function getSelectedPoint() {
    // First try to get from window.clickedDataPoint (used by LightweightCharts)
    if (window.clickedDataPoint) {
        console.log('Getting selected point from window.clickedDataPoint:', window.clickedDataPoint);
        
        // Create a properly formatted point object
        return {
            timestamp: window.clickedDataPoint.timestamp,
            price: window.clickedDataPoint.price,
            symbol: currentStock,
            close: window.clickedDataPoint.price
        };
    }
    
    // Then try the selected-point-store (used by Plotly)
    const selectedPointElement = document.getElementById('selected-point-store');
    if (selectedPointElement && (selectedPointElement.innerText || selectedPointElement.textContent)) {
        try {
            console.log('Getting selected point from selected-point-store');
            return JSON.parse(selectedPointElement.innerText || selectedPointElement.textContent);
        } catch (e) {
            console.error('Error parsing selected point:', e);
            return null;
        }
    }
    
    console.warn('No selected point found');
    return null;
}

// Function to position annotation markers on the chart
function positionAnnotationMarkers() {
    // Check if we're using LightweightCharts
    if (window.chart && window.candlestickSeries && window.annotationMarkers) {
        window.annotationMarkers.forEach(marker => {
            try {
                // Convert the timestamp to chart coordinates
                const timePoint = marker.time;
                const pricePoint = marker.price;
                
                const coordinate = window.candlestickSeries.priceToCoordinate(pricePoint);
                const timeCoordinate = window.chart.timeScale().timeToCoordinate(timePoint);
                
                if (coordinate === null || timeCoordinate === null) {
                    // Point is outside visible range
                    marker.element.style.display = 'none';
                    return;
                }
                
                // Position the marker at the correct coordinates
                marker.element.style.display = 'block';
                marker.element.style.left = `${timeCoordinate}px`;
                marker.element.style.top = `${coordinate}px`;
            } catch (e) {
                console.error('Error positioning marker:', e);
            }
        });
    }
}

// Helper function to create triangle markers for LightweightCharts
function createChartMarker(annotation) {
    try {
        // Parse timestamp to get the time value for the chart
        const timestamp = new Date(annotation.timestamp || annotation.formatted_timestamp);
        const timeValue = timestamp.getTime() / 1000; // Convert to seconds for LightweightCharts
        
        // Get the price value
        const price = parseFloat(annotation.price);
        
        // Determine color and symbol based on signal type
        let color, shape, text;
        
        switch(annotation.signal) {
            case 'long_entry':
                color = '#2ca02c'; // Green
                shape = 'triangle-up';
                text = 'L-ENTRY';
                break;
            case 'long_exit':
                color = '#1f77b4'; // Blue
                shape = 'triangle-down';
                text = 'L-EXIT';
                break;
            case 'short_entry':
                color = '#d62728'; // Red
                shape = 'triangle-up'; 
                text = 'S-ENTRY';
                break;
            case 'short_exit':
                color = '#ff7f0e'; // Orange
                shape = 'triangle-down';
                text = 'S-EXIT';
                break;
            default:
                color = '#7f7f7f'; // Gray
                shape = 'circle';
                text = annotation.signal;
        }
        
        // Create the marker object for LightweightCharts
        return {
            time: timeValue,
            position: 'aboveBar',
            color: color,
            shape: shape,
            text: text,
            size: 2
        };
    } catch (e) {
        console.error('Error creating chart marker:', e, annotation);
        return null;
    }
}

// Add event listener for window resize to reposition annotation markers
window.addEventListener('resize', function() {
    if (window.chart) {
        setTimeout(positionAnnotationMarkers, 100); // Small delay to ensure chart has resized
    }
});

// Add event listeners for chart range changes to update marker positions
document.addEventListener('DOMContentLoaded', function() {
    // Check for chart initialization periodically
    const checkChart = setInterval(function() {
        if (window.chart) {
            // If chart exists, clear interval and setup listeners
            clearInterval(checkChart);
            
            console.log('Chart found, setting up range change listeners');
            
            // Subscribe to visible range changes
            window.chart.timeScale().subscribeVisibleTimeRangeChange(function() {
                setTimeout(positionAnnotationMarkers, 50);
            });
        }
    }, 500);
});

// Attach event listeners to annotation buttons
document.addEventListener('DOMContentLoaded', function() {
    // Long Buy button
    const longBuyBtn = document.getElementById('btn-long-entry');
    if (longBuyBtn) {
        longBuyBtn.addEventListener('click', function() {
            const selectedPoint = getSelectedPoint();
            if (selectedPoint) {
                createAnnotationFromSelectedPoint(selectedPoint, 'long_buy', 'Long entry signal');
            } else {
                showNotification('Please select a point on the chart first', 'warning');
            }
        });
    }
    
    // Long Exit button
    const longExitBtn = document.getElementById('btn-long-exit');
    if (longExitBtn) {
        longExitBtn.addEventListener('click', function() {
            const selectedPoint = getSelectedPoint();
            if (selectedPoint) {
                createAnnotationFromSelectedPoint(selectedPoint, 'long_exit', 'Long exit signal');
            } else {
                showNotification('Please select a point on the chart first', 'warning');
            }
        });
    }
    
    // Short Buy button
    const shortBuyBtn = document.getElementById('btn-short-entry');
    if (shortBuyBtn) {
        shortBuyBtn.addEventListener('click', function() {
            const selectedPoint = getSelectedPoint();
            if (selectedPoint) {
                createAnnotationFromSelectedPoint(selectedPoint, 'short_buy', 'Short entry signal');
            } else {
                showNotification('Please select a point on the chart first', 'warning');
            }
        });
    }
    
    // Short Exit button
    const shortExitBtn = document.getElementById('btn-short-exit');
    if (shortExitBtn) {
        shortExitBtn.addEventListener('click', function() {
            const selectedPoint = getSelectedPoint();
            if (selectedPoint) {
                createAnnotationFromSelectedPoint(selectedPoint, 'short_exit', 'Short exit signal');
            } else {
                showNotification('Please select a point on the chart first', 'warning');
            }
        });
    }
    
    // Delete Last button
    const deleteLastBtn = document.getElementById('delete-last-btn');
    if (deleteLastBtn) {
        deleteLastBtn.addEventListener('click', deleteLastAnnotation);
    }
});

// Helper function to get the currently selected point
function getSelectedPoint() {
    const selectedPointElement = document.getElementById('selected-point-store');
    if (!selectedPointElement) return null;
    
    try {
        return JSON.parse(selectedPointElement.innerText || selectedPointElement.textContent);
    } catch (e) {
        console.error('Error parsing selected point:', e);
        return null;
    }
}

// Function to draw annotations on the chart
function drawAnnotations(annotations) {
    console.log('Drawing annotations on chart');
    
    // If annotations aren't provided, use the global window.currentAnnotations
    const annotationsToUse = annotations || window.currentAnnotations || [];
    
    // Clear existing annotation markers
    document.querySelectorAll('.annotation-marker').forEach(el => el.remove());
    
    if (!annotationsToUse || annotationsToUse.length === 0) {
        console.log('No annotations to draw');
        return;
    }
    
    console.log(`Drawing ${annotationsToUse.length} annotations on chart`);
    
    // Check which chart library we're using
    const usingLightweightCharts = window.chart && window.candlestickSeries;
    
    if (usingLightweightCharts) {
        drawLightweightChartAnnotations(annotationsToUse);
    } else {
        // Fall back to manual marker creation if Plotly isn't available or ready
        createManualAnnotationMarkers(annotationsToUse);
    }
}

// Function to draw annotations on LightweightCharts
function drawLightweightChartAnnotations(annotations) {
    if (!window.chart || !window.candlestickSeries) {
        console.warn('LightweightCharts not available');
        return;
    }
    
    const chartContainer = document.getElementById('stockChart');
    if (!chartContainer) {
        console.warn('Chart container not found');
        return;
    }
    
    // Reset markers collection
    window.annotationMarkers = [];
    
    // Process each annotation
    annotations.forEach(function(annotation) {
        try {
            // Parse the timestamp and convert to seconds
            const timestamp = new Date(annotation.timestamp);
            const timestampSeconds = timestamp.getTime() / 1000;
            
            // Get the price
            const price = parseFloat(annotation.price);
            
            // Skip invalid values
            if (isNaN(timestampSeconds) || isNaN(price)) {
                console.warn('Invalid timestamp or price:', annotation);
                return;
            }
            
            // Determine color and marker type based on signal
            let color, markerType, markerHTML;
            
            switch(annotation.signal) {
                case 'long_entry':
                    color = '#2ca02c'; // Green
                    markerType = 'triangle-up';
                    markerHTML = '▲'; // Up triangle
                    break;
                case 'long_exit':
                    color = '#1f77b4'; // Blue
                    markerType = 'triangle-down';
                    markerHTML = '▼'; // Down triangle
                    break;
                case 'short_entry':
                    color = '#d62728'; // Red
                    markerType = 'triangle-down';
                    markerHTML = '▼'; // Down triangle
                    break;
                case 'short_exit':
                    color = '#ff7f0e'; // Orange
                    markerType = 'triangle-up';
                    markerHTML = '▲'; // Up triangle
                    break;
                default:
                    color = '#7f7f7f'; // Gray
                    markerType = 'circle';
                    markerHTML = '●'; // Circle
            }
            
            // Create marker element
            const markerDiv = document.createElement('div');
            markerDiv.className = 'annotation-marker';
            markerDiv.style.position = 'absolute';
            markerDiv.style.zIndex = '1000';
            markerDiv.style.pointerEvents = 'auto';
            markerDiv.style.cursor = 'pointer';
            markerDiv.style.fontSize = '24px';
            markerDiv.style.color = color;
            markerDiv.style.textShadow = '0px 0px 3px white';
            markerDiv.style.transform = 'translate(-50%, -50%)';
            markerDiv.innerHTML = markerHTML;
            markerDiv.title = `${annotation.signal} at ${price.toFixed(2)}`;
            
            // Add click handler to show details
            markerDiv.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent chart click
                showAnnotationDetails(annotation);
            });
            
            // Add label above marker
            const labelDiv = document.createElement('div');
            labelDiv.className = 'annotation-label';
            labelDiv.style.position = 'absolute';
            labelDiv.style.bottom = '100%';
            labelDiv.style.left = '50%';
            labelDiv.style.transform = 'translateX(-50%)';
            labelDiv.style.backgroundColor = 'rgba(255,255,255,0.8)';
            labelDiv.style.color = color;
            labelDiv.style.padding = '2px 4px';
            labelDiv.style.borderRadius = '3px';
            labelDiv.style.fontSize = '10px';
            labelDiv.style.fontWeight = 'bold';
            labelDiv.style.whiteSpace = 'nowrap';
            labelDiv.textContent = annotation.signal;
            markerDiv.appendChild(labelDiv);
            
            // Store marker data for repositioning
            window.annotationMarkers.push({
                element: markerDiv,
                time: timestampSeconds,
                price: price,
                annotation: annotation
            });
            
            // Add to chart container
            chartContainer.appendChild(markerDiv);
            
        } catch (error) {
            console.error("Error adding annotation marker:", error, annotation);
        }
    });
    
    // Position markers based on current chart state
    setTimeout(positionAnnotationMarkers, 0);
} 