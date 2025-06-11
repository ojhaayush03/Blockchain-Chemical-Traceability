/**
 * Chemical Module
 * Handles all chemical-related functionality including registration and management
 */

import { showNotification } from './ui.js';

/**
 * Handle chemical registration form submission
 * @param {Event} event - The form submission event
 */
export async function handleChemicalRegistration(event) {
    event.preventDefault();
    
    const form = document.getElementById('register-chemical-form');
    const submitBtn = document.getElementById('submit-chemical-btn');
    const resultDiv = document.getElementById('register-result');
    
    if (!form || !submitBtn) return;
    
    // Disable form and show loading state
    const formElements = form.elements;
    for (let i = 0; i < formElements.length; i++) {
        formElements[i].disabled = true;
    }
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
    
    try {
        // Get form values with validation
        const name = document.getElementById('chemical-name').value.trim();
        const rfidTag = document.getElementById('chemical-rfid').value.trim();
        const manufacturer = document.getElementById('chemical-manufacturer').value.trim();
        const location = document.getElementById('chemical-location').value.trim();
        
        // Basic validation
        if (!name || !rfidTag || !manufacturer || !location) {
            throw new Error('Please fill in all required fields');
        }
        
        // Prepare chemical data
        const chemicalData = {
            name: name,
            rfid_tag: rfidTag,
            manufacturer: manufacturer,
            current_location: location,
            quantity: document.getElementById('chemical-quantity').value ? 
                    parseFloat(document.getElementById('chemical-quantity').value) : null,
            unit: document.getElementById('chemical-unit').value,
            expiry_date: document.getElementById('chemical-expiry').value || null,
            storage_condition: document.getElementById('chemical-storage').value || null,
            hazard_class: document.getElementById('chemical-hazard').value || null,
            cas_number: document.getElementById('chemical-cas').value.trim() || null,
            batch_number: document.getElementById('chemical-batch').value.trim() || null,
            description: document.getElementById('chemical-description').value.trim() || null
        };
        
        // Make API call to register the chemical
        const response = await fetch('/register-chemical', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(chemicalData)
        });
        
        const result = await response.json();
        
        // Display result
        if (resultDiv) {
            resultDiv.style.display = 'block';
            
            if (response.ok) {
                resultDiv.className = 'alert alert-success';
                resultDiv.innerHTML = `
                    <h4><i class="fas fa-check-circle"></i> Chemical Registered Successfully</h4>
                    <p>The chemical has been registered in the database.</p>
                    ${result.blockchain ? 
                        '<p><strong>Blockchain status:</strong> Verified and recorded on blockchain</p>' :
                        '<p><strong>Blockchain status:</strong> Recorded in local database only</p>'
                    }
                `;
                // Reset the form
                form.reset();
            } else {
                throw new Error(result.message || 'Failed to register chemical');
            }
        }
    } catch (error) {
        console.error('Error registering chemical:', error);
        showNotification(error.message || 'An error occurred while registering the chemical', 'error');
    } finally {
        // Re-enable form and reset button state
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = false;
        }
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Register Chemical';
    }
}

/**
 * Initialize chemical-related event listeners
 */
export function initChemicalModule() {
    const registerForm = document.getElementById('register-chemical-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleChemicalRegistration);
    }
}

/**
 * Get the HTML for the register chemical page
 * @returns {string} HTML content for the register chemical page
 */
export function getRegisterChemicalPage() {
    return `
        <div class="card" style="grid-column: span 3;">
            <div class="card-header">
                <h3 class="card-title">Register New Chemical</h3>
            </div>
            <div class="card-body">
                <form id="register-chemical-form">
                    <div class="form-group">
                        <label for="chemical-name">Chemical Name*</label>
                        <input type="text" id="chemical-name" class="form-control" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-rfid">RFID Tag ID*</label>
                        <input type="text" id="chemical-rfid" class="form-control" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-manufacturer">Manufacturer*</label>
                        <input type="text" id="chemical-manufacturer" class="form-control" required>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group col-md-6">
                            <label for="chemical-quantity">Quantity</label>
                            <input type="number" id="chemical-quantity" class="form-control" step="0.01">
                        </div>
                        
                        <div class="form-group col-md-6">
                            <label for="chemical-unit">Unit</label>
                            <select id="chemical-unit" class="form-control">
                                <option value="L">Liters (L)</option>
                                <option value="mL">Milliliters (mL)</option>
                                <option value="kg">Kilograms (kg)</option>
                                <option value="g">Grams (g)</option>
                                <option value="mg">Milligrams (mg)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group col-md-6">
                            <label for="chemical-expiry">Expiry Date</label>
                            <input type="date" id="chemical-expiry" class="form-control">
                        </div>
                        
                        <div class="form-group col-md-6">
                            <label for="chemical-storage">Storage Condition</label>
                            <select id="chemical-storage" class="form-control">
                                <option value="">Select storage condition</option>
                                <option value="room_temp">Room Temperature</option>
                                <option value="refrigerated">Refrigerated (2-8°C)</option>
                                <option value="frozen">Frozen (-20°C)</option>
                                <option value="deep_freeze">Deep Freeze (-80°C)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-location">Current Location*</label>
                        <input type="text" id="chemical-location" class="form-control" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-description">Description</label>
                        <textarea id="chemical-description" class="form-control" rows="3"></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="submit" id="submit-chemical-btn" class="action-btn">
                            <i class="fas fa-save"></i> Register Chemical
                        </button>
                        <button type="reset" class="action-btn secondary">
                            <i class="fas fa-undo"></i> Reset Form
                        </button>
                    </div>
                </form>
                
                <div id="register-result" class="mt-3" style="display: none;"></div>
            </div>
        </div>
    `;
}