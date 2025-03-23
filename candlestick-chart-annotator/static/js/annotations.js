// Connect to WebSocket server
const socket = io();

// Store current annotations
let currentAnnotations = [];

// Listen for annotation updates
socket.on('annotations_updated', function(data) {
    console.log('Received annotations update:', data);
    
    // Update global annotations
    window.annotations = data.annotations || [];
    
    // Filter for current stock and date
    if (currentStock && currentDate) {
        window.currentAnnotations = window.annotations.filter(function(annotation) {
            return annotation.stock === currentStock && 
                   annotation.timestamp.substring(0, 10) === currentDate;
        });
    } else {
        window.currentAnnotations = [];
    }
    
    // Update table
    updateAnnotationsTable(window.currentAnnotations);
    
    // Update chart
    if (typeof updateChartAnnotations === 'function') {
        updateChartAnnotations(window.currentAnnotations);
    }
    
    // If using LightweightCharts
    if (typeof drawAnnotations === 'function') {
        drawAnnotations();
    }
});

// Initial load of annotations
socket.on('annotations_data', function(data) {
    currentAnnotations = data.annotations;
    updateAnnotationsTable(currentAnnotations);
    updateAnnotationsOnChart();
});

// Request annotations on page load
document.addEventListener('DOMContentLoaded', function() {
    socket.emit('get_annotations');
});

// Update annotations table with consistent formatting and alignment
function updateAnnotationsTable(annotations) {
    console.log("Updating annotations table with:", annotations);
    
    // If no annotations provided, use current annotations
    if (!annotations) {
        annotations = currentAnnotations || [];
    }
    
    // Clear the table
    const tableBody = document.getElementById('annotations-table-body');
    if (!tableBody) {
        console.warn("Annotations table body not found");
        return;
    }
    
    tableBody.innerHTML = '';
    
    // If no annotations, show empty message
    if (!annotations || annotations.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="7" class="text-center">No annotations available</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // Sort annotations by timestamp
    const sortedAnnotations = [...annotations].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
    });
    
    // Add each annotation to the table
    sortedAnnotations.forEach((annotation, index) => {
        // Format timestamp
        let formattedTime = 'Unknown';
        try {
            if (annotation.formatted_timestamp) {
                formattedTime = annotation.formatted_timestamp;
            } else if (annotation.timestamp) {
                const timestamp = new Date(annotation.timestamp);
                if (!isNaN(timestamp.getTime())) {
                    formattedTime = formatTimestamp(timestamp);
                }
            }
        } catch (e) {
            console.error("Error formatting timestamp:", e);
        }
        
        // Format price
        let formattedPrice = 'N/A';
        try {
            const price = parseFloat(annotation.price);
            if (!isNaN(price)) {
                formattedPrice = price.toFixed(2);
            }
        } catch (e) {
            console.error("Error formatting price:", e);
        }
        
        // Determine badge class
        let badgeClass = '';
        switch(annotation.signal) {
            case 'long_entry':
                badgeClass = 'bg-success';
                break;
            case 'long_exit':
                badgeClass = 'bg-primary'; 
                break;
            case 'short_entry':
                badgeClass = 'bg-danger';
                break;
            case 'short_exit':
                badgeClass = 'bg-warning';
                break;
            default:
                badgeClass = 'bg-secondary';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${annotation.id || index + 1}</td>
            <td>${annotation.stock || 'N/A'}</td>
            <td>${formattedTime}</td>
            <td><span class="badge ${badgeClass}">${annotation.signal}</span></td>
            <td>₹${formattedPrice}</td>
            <td class="reason-cell">${annotation.reason || '-'}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-sm btn-outline-info view-ann-btn" data-id="${annotation.id}">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-ann-btn" data-id="${annotation.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners
    document.querySelectorAll('.view-ann-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const annotation = annotations.find(a => String(a.id) === String(id));
            if (annotation) {
                showAnnotationDetails(annotation);
            }
        });
    });
    
    document.querySelectorAll('.delete-ann-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            if (confirm('Are you sure you want to delete this annotation?')) {
                deleteAnnotation(id);
            }
        });
    });
}

// Function to update annotations on chart
function updateAnnotationsOnChart() {
    if (typeof updateChartAnnotations === 'function') {
        updateChartAnnotations(currentAnnotations);
    }
}

// Function to add new annotation
function addAnnotation(data) {
    console.log("Adding annotation:", data);
    
    // If timestamp is a Date object, convert to ISO string
    if (data.timestamp instanceof Date) {
        data.timestamp = data.timestamp.toISOString();
    }
    
    // Ensure all required fields are present
    if (!data.timestamp || !data.stock || !data.signal) {
        showNotification('Missing required annotation data', 'error');
        console.error('Missing required fields. Annotation data:', data);
        return;
    }
    
    fetch('/api/annotations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            showNotification('Annotation added successfully', 'success');
            
            // Close any open modals
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modalEl => {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            });
            
            // Remove modal backdrop if it exists
            const modalBackdrops = document.querySelectorAll('.modal-backdrop');
            modalBackdrops.forEach(backdrop => {
                backdrop.remove();
            });
            
            // Reset body classes that may have been added by Bootstrap
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            // Manually request annotations update
            setTimeout(() => {
                socket.emit('get_annotations');
            }, 500);
        }
    })
    .catch(error => {
        console.error('Error adding annotation:', error);
        showNotification('Error adding annotation: ' + error.message, 'error');
    });
}

/**
 * Function to completely fix scrolling issues
 * Add this function to your annotations.js file
 */
function fixScrollingIssues() {
    // 1. Close any open modals properly
    const openModals = document.querySelectorAll('.modal');
    openModals.forEach(modalEl => {
      try {
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
      } catch (e) {
        console.error('Error closing modal:', e);
      }
    });
  
    // 2. Remove all modal backdrops
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.parentNode.removeChild(backdrop);
    });
  
    // 3. Fix body classes and styles
    document.body.classList.remove('modal-open');
    document.body.removeAttribute('style'); // Remove all inline styles
    document.body.style.overflow = 'auto';  // Explicitly enable scrolling
  
    // 4. Check for any fixed position elements that might block scrolling
    document.querySelectorAll('[style*="position: fixed"]').forEach(el => {
      if (el.classList.contains('modal') || el.classList.contains('modal-backdrop')) {
        el.style.display = 'none';
      }
    });
  
    // 5. Ensure scroll events are properly handled
    window.scrollTo(window.scrollX, window.scrollY);
  }

// Function to delete annotation
function deleteAnnotation(id) {
    if (!id) {
        console.error("Invalid annotation ID");
        return;
    }
    
    console.log(`Deleting annotation with ID: ${id}`);
    
    fetch(`/api/annotations/${id}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Annotation deleted successfully:", data);
        
        // Remove from global annotations array
        if (window.annotations) {
            window.annotations = window.annotations.filter(a => a.id !== parseInt(id) && a.id !== id);
        }
        
        // Remove from current annotations array
        if (window.currentAnnotations) {
            window.currentAnnotations = window.currentAnnotations.filter(a => a.id !== parseInt(id) && a.id !== id);
        }
        
        // Force redraw of chart annotations
        if (typeof updateChartAnnotations === 'function') {
            updateChartAnnotations(window.currentAnnotations || []);
        }
        
        // If using LightweightCharts and drawAnnotations exists
        if (typeof drawAnnotations === 'function') {
            drawAnnotations();
        }
        
        // Update the table with remaining annotations
        updateAnnotationsTable(window.currentAnnotations || []);
        
        showNotification("Annotation deleted successfully", "success");
    })
    .catch(error => {
        console.error("Error deleting annotation:", error);
        showNotification(`Error deleting annotation: ${error.message}`, "error");
    });
}

// Function to delete last annotation
function deleteLastAnnotation() {
    fetch('/api/annotations/last', {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            showNotification('Last annotation deleted successfully', 'success');
        }
    })
    .catch(error => {
        showNotification('Error deleting annotation: ' + error, 'error');
    });
}

// Function to show notification
function showNotification(message, type) {
    const notificationArea = document.getElementById('notification-area');
    if (!notificationArea) return;
    
    notificationArea.textContent = message;
    
    // Set style based on type
    notificationArea.className = '';
    notificationArea.classList.add('notification', type);
    
    // Clear notification after 3 seconds
    setTimeout(() => {
        notificationArea.textContent = '';
        notificationArea.className = '';
    }, 3000);
} 