/**
 * Movement Module
 * Handles tracking and recording of chemical movements
 */

import { showNotification, setButtonLoading } from './ui.js';
import { getAuthHeaders } from './auth.js';

/**
 * Record a movement event for a chemical
 * @param {string} rfidTag - The RFID tag of the chemical
 * @param {string} location - The new location
 * @param {string} movedBy - The ID of the user who moved the chemical
 * @param {string} [purpose] - The purpose of the movement
 * @param {string} [status] - The status of the movement
 * @returns {Promise<Object>} The result of the movement recording
 */
export async function recordMovement(rfidTag, location, movedBy, purpose = '', status = 'in_transit') {
    try {
        const response = await fetch('/log-event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                rfid_tag: rfidTag,
                location: location,
                moved_by: movedBy,
                purpose: purpose,
                status: status,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to record movement');
        }

        const result = await response.json();
        showNotification('Movement recorded successfully', 'success');
        return { success: true, data: result };
    } catch (error) {
        console.error('Error recording movement:', error);
        showNotification(error.message || 'Failed to record movement', 'error');
        return { success: false, error: error.message };
    }
}

/**
 * Get movement history for a chemical
 * @param {string} rfidTag - The RFID tag of the chemical
 * @returns {Promise<Array>} Array of movement events
 */
export async function getMovementHistory(rfidTag) {
    try {
        const response = await fetch(`/chemical-history/${rfidTag}`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to fetch movement history');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching movement history:', error);
        showNotification('Failed to load movement history', 'error');
        return [];
    }
}

/**
 * Handle movement form submission
 * @param {Event} event - The form submission event
 */
export async function handleMovementFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
    
    try {
        // Set loading state
        setButtonLoading(submitBtn, true, originalBtnText);
        
        // Get form data
        const formData = new FormData(form);
        const movementData = {
            rfid_tag: formData.get('rfid_tag'),
            location: formData.get('location'),
            purpose: formData.get('purpose') || '',
            status: formData.get('status') || 'in_transit'
        };
        
        // Validate required fields
        if (!movementData.rfid_tag || !movementData.location) {
            throw new Error('RFID tag and location are required');
        }
        
        // Record movement
        const result = await recordMovement(
            movementData.rfid_tag,
            movementData.location,
            getCurrentUser()?.id || 'system',
            movementData.purpose,
            movementData.status
        );
        
        if (result.success) {
            // Reset form on success
            form.reset();
        }
    } catch (error) {
        console.error('Movement form error:', error);
        showNotification(error.message || 'Failed to process movement', 'error');
    } finally {
        // Reset button state
        setButtonLoading(submitBtn, false, originalBtnText);
    }
}

/**
 * Initialize movement tracking
 */
export function initMovementTracking() {
    const movementForm = document.getElementById('movement-form');
    if (movementForm) {
        movementForm.addEventListener('submit', handleMovementFormSubmit);
    }
    
    // Initialize any movement-related UI components
    initMovementUI();
}

/**
 * Initialize movement-related UI components
 */
function initMovementUI() {
    // Add any UI initialization code here
    // For example, date pickers, location autocomplete, etc.
    
    // Example: Initialize date picker for movement date
    const dateInput = document.getElementById('movement-date');
    if (dateInput && !dateInput.value) {
        dateInput.valueAsDate = new Date();
    }
    
    // Example: Initialize location autocomplete
    initLocationAutocomplete();
}

/**
 * Initialize location autocomplete
 */
function initLocationAutocomplete() {
    const locationInput = document.getElementById('location');
    if (!locationInput) return;
    
    // This is a placeholder for actual location autocomplete implementation
    // In a real app, you would integrate with a geocoding service like Google Maps
    
    // Example of how you might implement this:
    // const autocomplete = new google.maps.places.Autocomplete(locationInput, {
    //     types: ['establishment', 'geocode']
    // });
    
    // For now, we'll just log a message
    console.log('Location autocomplete would be initialized here');
}

/**
 * Render movement history for a chemical
 * @param {string} rfidTag - The RFID tag of the chemical
 * @param {HTMLElement} container - The container to render the history in
 */
export async function renderMovementHistory(rfidTag, container) {
    if (!container) return;
    
    try {
        // Show loading state
        container.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> Loading history...</div>';
        
        // Fetch movement history
        const history = await getMovementHistory(rfidTag);
        
        if (history.length === 0) {
            container.innerHTML = '<div class="text-muted text-center py-4">No movement history found</div>';
            return;
        }
        
        // Render history
        container.innerHTML = `
            <div class="timeline">
                ${history.map(event => `
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <p class="mb-1">
                                <strong>${formatDate(event.timestamp)}</strong> - 
                                Moved to ${event.location}
                            </p>
                            ${event.purpose ? `<p class="text-muted small mb-0">Purpose: ${event.purpose}</p>` : ''}
                            ${event.status ? `<span class="badge badge-${getStatusBadgeClass(event.status)}">${formatStatus(event.status)}</span>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Error rendering movement history:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                Failed to load movement history. Please try again later.
            </div>
        `;
    }
}

/**
 * Format a date string for display
 * @param {string} dateString - The date string to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

/**
 * Format a status string for display
 * @param {string} status - The status to format
 * @returns {string} Formatted status
 */
function formatStatus(status) {
    return status
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Get the Bootstrap badge class for a status
 * @param {string} status - The status
 * @returns {string} Bootstrap badge class
 */
function getStatusBadgeClass(status) {
    const statusClasses = {
        'in_transit': 'info',
        'delivered': 'success',
        'returned': 'warning',
        'damaged': 'danger',
        'lost': 'dark'
    };
    
    return statusClasses[status] || 'secondary';
}