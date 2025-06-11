/**
 * UI Module
 * Handles all UI-related functionality including notifications and page transitions
 */

/**
 * Show a notification to the user
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, warning, info)
 * @returns {HTMLElement} The created notification element
 */
export function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Create notification content
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    const removeNotification = () => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    };
    
    setTimeout(removeNotification, 5000);
    
    // Close button functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', removeNotification);
    
    return notification;
}

/**
 * Toggle loading state for a button
 * @param {HTMLElement} button - The button element
 * @param {boolean} isLoading - Whether to show loading state
 * @param {string} [originalText] - The original button text to restore
 */
export function setButtonLoading(button, isLoading, originalText = null) {
    if (isLoading) {
        button.dataset.originalText = originalText || button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || originalText || '';
    }
}

/**
 * Show a modal dialog
 * @param {string} title - The modal title
 * @param {string} content - The modal content HTML
 * @param {Object} options - Modal options
 * @param {string} [options.confirmText='OK'] - Text for the confirm button
 * @param {string} [options.cancelText='Cancel'] - Text for the cancel button
 * @param {Function} [options.onConfirm] - Callback when confirm is clicked
 * @param {Function} [options.onCancel] - Callback when cancel is clicked
 */
export function showModal(title, content, options = {}) {
    // Create modal container
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    // Create modal content
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${title}</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" id="modal-cancel">${options.cancelText || 'Cancel'}</button>
                <button class="btn btn-primary" id="modal-confirm">${options.confirmText || 'OK'}</button>
            </div>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(modal);
    document.body.classList.add('modal-open');
    
    // Close modal function
    const closeModal = () => {
        modal.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(modal);
            document.body.classList.remove('modal-open');
        }, 300);
    };
    
    // Event listeners
    const closeBtn = modal.querySelector('.modal-close');
    const cancelBtn = modal.querySelector('#modal-cancel');
    const confirmBtn = modal.querySelector('#modal-confirm');
    
    closeBtn.addEventListener('click', () => {
        if (options.onCancel) options.onCancel();
        closeModal();
    });
    
    cancelBtn.addEventListener('click', () => {
        if (options.onCancel) options.onCancel();
        closeModal();
    });
    
    confirmBtn.addEventListener('click', () => {
        if (options.onConfirm) options.onConfirm();
        closeModal();
    });
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            if (options.onCancel) options.onCancel();
            closeModal();
        }
    });
    
    // Show modal with animation
    setTimeout(() => modal.classList.add('show'), 10);
    
    return modal;
}

/**
 * Update the page content
 * @param {string} content - The HTML content to set
 * @param {string} [containerId='app-content'] - The ID of the container to update
 */
export function updatePageContent(content, containerId = 'app-content') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = content;
    }
}

/**
 * Show a loading spinner
 * @param {string} [message='Loading...'] - The message to show with the spinner
 * @param {string} [containerId='app-content'] - The ID of the container to show the spinner in
 * @returns {HTMLElement} The loading element
 */
export function showLoading(message = 'Loading...', containerId = 'app-content') {
    const container = document.getElementById(containerId);
    if (!container) return null;
    
    const loadingElement = document.createElement('div');
    loadingElement.className = 'loading-container';
    loadingElement.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
        </div>
        <p class="mt-2">${message}</p>
    `;
    
    container.innerHTML = '';
    container.appendChild(loadingElement);
    
    return loadingElement;
}

/**
 * Initialize tooltips
 */
export function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize popovers
 */
export function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}