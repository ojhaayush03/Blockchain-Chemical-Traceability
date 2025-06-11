/**
 * Main Application Controller for Chemical Traceability System
 * Handles UI interactions and integrates with blockchain client
 */

// Import modules
import { initAuth, isAuthenticated, hasRole, ROLES } from './modules/auth.js';
import { initChemicalModule, getRegisterChemicalPage } from './modules/chemical.js';
import { initMovementTracking, renderMovementHistory } from './modules/movement.js';
import { showNotification, updatePageContent, showLoading, initTooltips, initPopovers } from './modules/ui.js';
// Using the global blockchainClient from blockchain.js in root directory

// Main app namespace
const ChemTrack = {
    // Current application state
    state: {
        currentUser: null,
        selectedRole: null,
        blockchainStatus: 'pending',
        notifications: [],
        currentChemical: null,
        movementHistory: [],
        dashboard: {
            activeTab: 'overview'
        },
        blockchainClient: null,
        // Navigation history
        navigation: {
            history: [],
            currentPage: null
        }
    },
    
    // Initialize the application
    init: async function() {
        console.log('Initializing Chemical Traceability System...');
        
        try {
            // Initialize UI components
            initTooltips();
            initPopovers();
            
            // Initialize authentication
            await initAuth();
            
            // Initialize blockchain client
            await this.initializeBlockchain();
            
            // Initialize modules
            this.initializeModules();
            
            // Set up splash screen
            this.setupSplashScreen();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Handle hash-based routing
            window.addEventListener('hashchange', () => {
                const path = window.location.hash.replace('#', '') || 'dashboard';
                this.loadPageContent(path);
            });
            
            // Load initial route
            const initialPath = window.location.hash.replace('#', '') || 'dashboard';
            this.loadPageContent(initialPath);
            
            console.log('Application initialized successfully');
        } catch (error) {
            console.error('Error initializing application:', error);
            this.showNotification('Failed to initialize application. Please refresh the page.', 'error');
        }
    },
    
    // Initialize blockchain client
    initializeBlockchain: async function() {
        try {
            // Use the global blockchainClient from the root blockchain.js file
            if (window.blockchainClient) {
                console.log('Using global blockchain client');
                this.state.blockchainClient = window.blockchainClient;
                
                // Check connection status
                const status = await window.blockchainClient.checkConnection();
                
                if (status.connected) {
                    console.log('Blockchain client initialized successfully');
                    this.state.blockchainStatus = 'connected';
                } else {
                    console.warn('Blockchain client is disconnected');
                    this.state.blockchainStatus = 'disconnected';
                }
            } else {
                console.error('Global blockchain client not found');
                this.state.blockchainStatus = 'error';
                this.showNotification('Failed to connect to blockchain. Some features may be limited.', 'warning');
            }
        } catch (error) {
            console.error('Error initializing blockchain client:', error);
            this.state.blockchainStatus = 'error';
            this.showNotification('Failed to connect to blockchain. Some features may be limited.', 'warning');
        }
    },
    
    // Initialize application modules
    initializeModules: function() {
        // Initialize chemical module
        initChemicalModule();
        
        // Initialize movement tracking
        initMovementTracking();
        
        // Add any other module initializations here
    },
    
    // Set up splash screen behavior
    setupSplashScreen: function() {
        const splashScreen = document.getElementById('splash-screen');
        const roleSelection = document.getElementById('role-selection');
        const SPLASH_DURATION = 2000; // 2 seconds
        
        if (!splashScreen || !roleSelection) {
            console.warn('Splash screen or role selection element not found');
            return;
        }
        
        // Show splash screen for specified duration, then transition to role selection
        setTimeout(() => {
            splashScreen.style.opacity = '0';
            setTimeout(() => {
                splashScreen.style.display = 'none';
                roleSelection.style.display = 'flex';
                // Dispatch custom event when splash screen is hidden
                document.dispatchEvent(new CustomEvent('splashHidden'));
            }, 500); // Fade out duration
        }, SPLASH_DURATION);
    },
    
    // Set up all event listeners
    setupQuickActions: function() {
        // Setup quick action buttons
        const quickActions = document.querySelectorAll('.quick-action');
        quickActions.forEach(action => {
            action.addEventListener('click', (e) => {
                const actionType = e.currentTarget.dataset.action;
                this.handleQuickAction(actionType);
            });
        });
        
        // Tab navigation links
        document.getElementById('show-signup')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchAuthTab('signup');
        });
        
        document.getElementById('show-login')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchAuthTab('login');
        });
        
        // Form submissions
        document.getElementById('login-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        document.getElementById('signup-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleSignup();
        });
    },

    // Add this inside the ChemTrack object
    
    // Setup chemical-related event listeners
    // Set up all event listeners for the application
    setupEventListeners: function() {
        console.log('Setting up application event listeners');
        
        // Setup role selection buttons event listeners
        const roleBtns = document.querySelectorAll('.select-role-btn');
        roleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const role = e.target.getAttribute('data-role');
                console.log(`Role button clicked: ${role}`);
                if (role) {
                    this.selectRole(role);
                }
            });
        });
        
        // Setup form event listeners
        document.getElementById('login-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        document.getElementById('signup-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleSignup();
        });
        
        // Setup role-specific event listeners
        this.setupChemicalEventListeners();
        this.setupMovementEventListeners();
        
        // Setup page events for initial page
        const initialPath = window.location.hash.replace('#', '') || 'dashboard';
        this.setupPageEvents(initialPath);
    },
    
    setupChemicalEventListeners: function() {
        // Chemical form submission is handled in the chemical module
        // This is a placeholder for any app-level chemical event listeners
    },
    
    // Setup movement-related event listeners
    setupMovementEventListeners: function() {
        // Movement form submission is handled in the movement module
        // This is a placeholder for any app-level movement event listeners
    },
    
    // Update content based on route
    updateContentForRoute: function(route) {
        // This method will be implemented to handle dynamic content loading
        // based on the current route
        console.log('Navigating to:', route);
        
        // Show loading state
        this.updatePageContent('<div class="loading-spinner">Loading...</div>');
        
        // Handle different routes
        if (route === 'dashboard') {
            // Show the dashboard container
            const dashboardContainer = document.getElementById('dashboard-container');
            if (dashboardContainer) {
                // Hide auth container if it's visible
                const authContainer = document.getElementById('auth-container');
                if (authContainer) {
                    authContainer.style.display = 'none';
                }
                
                // Show dashboard container
                dashboardContainer.style.display = 'block';
                
                setTimeout(() => {
                    this.buildDashboard();
                }, 100);
            } else {
                console.error('Dashboard container not found');
            }
        } else {
            // For other routes, could implement more sophisticated routing
            console.log('Route not specifically handled:', route);
        }
    },
    
    // Update page content with provided HTML
    updatePageContent: function(html) {
        const mainContent = document.getElementById('dashboard-content');
        if (mainContent) {
            mainContent.innerHTML = html;
        } else {
            console.error('Dashboard content element not found');
        }
    },

    // Get register chemical page content
getRegisterChemicalPage: function() {
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
                            <input type="number" id="chemical-quantity" class="form-control">
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
                            <label for="chemical-received">Received Date</label>
                            <input type="date" id="chemical-received" class="form-control">
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group col-md-6">
                            <label for="chemical-hazard">Hazard Class</label>
                            <select id="chemical-hazard" class="form-control">
                                <option value="">Select Hazard Class</option>
                                <option value="Flammable">Flammable</option>
                                <option value="Corrosive">Corrosive</option>
                                <option value="Toxic">Toxic</option>
                                <option value="Oxidizing">Oxidizing</option>
                                <option value="Explosive">Explosive</option>
                                <option value="Non-hazardous">Non-hazardous</option>
                            </select>
                        </div>
                        
                        <div class="form-group col-md-6">
                            <label for="chemical-cas">CAS Number</label>
                            <input type="text" id="chemical-cas" class="form-control">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-storage">Storage Conditions</label>
                        <input type="text" id="chemical-storage" class="form-control" placeholder="e.g., Keep refrigerated, Store in dark place">
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-batch">Batch Number</label>
                        <input type="text" id="chemical-batch" class="form-control">
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-location">Current Location*</label>
                        <input type="text" id="chemical-location" class="form-control" required placeholder="e.g., Lab 101, Warehouse A">
                    </div>
                    
                    <div class="form-group">
                        <label for="chemical-description">Description</label>
                        <textarea id="chemical-description" class="form-control" rows="3"></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" id="submit-chemical-btn" class="action-btn">
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
},

// Show notification to user
showNotification: function(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
    
    // Close button functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    });
    
    document.body.appendChild(notification);
    return notification;
},

// Handle chemical registration form submission
handleChemicalRegistration: async function() {
    const form = document.getElementById('register-chemical-form');
    const submitBtn = document.getElementById('submit-chemical-btn');
    const resultDiv = document.getElementById('register-result');
    
    if (!form || !submitBtn) return;
    
    // Disable form and show loading state
    const formElements = form.elements;
    for (let i = 0; i < formElements.length; i++) {
        formElements[i].disabled = true;
    }
    
    const originalBtnText = submitBtn.innerHTML;
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
        const resultElement = document.getElementById('register-result');
        if (resultElement) {
            resultElement.style.display = 'block';
            
            if (response.ok) {
                resultElement.className = 'alert alert-success';
                resultElement.innerHTML = `
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
                resultElement.className = 'alert alert-danger';
                resultElement.innerHTML = `
                    <h4><i class="fas fa-exclamation-triangle"></i> Registration Failed</h4>
                    <p>${result.message || 'Unknown error occurred'}</p>
                `;
            }
        }
    } catch (error) {
        console.error('Error registering chemical:', error);
        alert(error.message || 'An error occurred while registering the chemical');
    } finally {
        // Re-enable form and reset button state
        for (let i = 0; i < formElements.length; i++) {
            formElements[i].disabled = false;
        }
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Register Chemical';
    }
},

// Get track movement page content
getTrackMovementPage: function() {
    return `
        <div class="card" style="grid-column: span 3;">
            <div class="card-header">
                <h3 class="card-title">Track Chemical Movement</h3>
            </div>
            <div class="card-body">
                <form id="track-movement-form">
                    <div class="form-group">
                        <label for="movement-tag-id">RFID Tag ID*</label>
                        <div class="input-group">
                            <input type="text" id="movement-tag-id" class="form-control" required>
                            <div class="input-group-append">
                                <button type="button" id="scan-tag-btn" class="btn btn-secondary">
                                    <i class="fas fa-qrcode"></i> Scan
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="movement-location">New Location*</label>
                        <input type="text" id="movement-location" class="form-control" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="movement-moved-by">Moved By*</label>
                        <input type="text" id="movement-moved-by" class="form-control" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="movement-purpose">Purpose</label>
                        <select id="movement-purpose" class="form-control">
                            <option value="Transport">Transport</option>
                            <option value="Storage">Storage</option>
                            <option value="Use">Use</option>
                            <option value="Disposal">Disposal</option>
                            <option value="Return">Return</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="movement-status">Status</label>
                        <select id="movement-status" class="form-control">
                            <option value="In Transit">In Transit</option>
                            <option value="Delivered">Delivered</option>
                            <option value="Received">Received</option>
                            <option value="In Storage">In Storage</option>
                            <option value="In Use">In Use</option>
                            <option value="Disposed">Disposed</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="movement-remarks">Remarks</label>
                        <textarea id="movement-remarks" class="form-control" rows="3"></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" id="submit-movement-btn" class="action-btn">
                            <i class="fas fa-map-marker-alt"></i> Log Movement
                        </button>
                        <button type="reset" class="action-btn secondary">
                            <i class="fas fa-undo"></i> Reset Form
                        </button>
                    </div>
                </form>
                
                <div id="movement-result" class="mt-3" style="display: none;"></div>
            </div>
        </div>
    `;
},

// Handle movement tracking form submission
handleMovementTracking: function() {
    const submitBtn = document.getElementById('submit-movement-btn');
    if (!submitBtn) return;
    
    submitBtn.addEventListener('click', async () => {
        // Get form values
        const movementData = {
            tag_id: document.getElementById('movement-tag-id').value,
            location: document.getElementById('movement-location').value,
            moved_by: document.getElementById('movement-moved-by').value,
            purpose: document.getElementById('movement-purpose').value,
            status: document.getElementById('movement-status').value,
            remarks: document.getElementById('movement-remarks').value
        };
        
        // Basic validation
        if (!movementData.tag_id || !movementData.location || !movementData.moved_by) {
            alert('Please fill in all required fields (RFID Tag ID, New Location, and Moved By)');
            return;
        }
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging Movement...';
        
        try {
            // Call the blockchain client to log the movement
            const result = await blockchainClient.logEvent(movementData);
            
            // Display result
            const resultElement = document.getElementById('movement-result');
            if (resultElement) {
                resultElement.style.display = 'block';
                
                if (result.success) {
                    resultElement.className = 'alert alert-success';
                    let message = `
                        <h4><i class="fas fa-check-circle"></i> Movement Logged Successfully</h4>
                        <p>The chemical movement has been recorded.</p>
                    `;
                    
                    if (result.partialSuccess) {
                        message += `
                            <p><strong>Note:</strong> Movement was recorded in the local database, but blockchain verification failed.</p>
                            <p class="text-muted">This could be due to network issues or blockchain unavailability.</p>
                        `;
                    } else if (result.blockchainStatus) {
                        message += `
                            <p><strong>Blockchain status:</strong> Successfully verified and recorded on blockchain</p>
                        `;
                    }
                    
                    resultElement.innerHTML = message;
                    
                    // Reset the form
                    document.getElementById('track-movement-form').reset();
                } else {
                    resultElement.className = 'alert alert-danger';
                    resultElement.innerHTML = `
                        <h4><i class="fas fa-exclamation-triangle"></i> Movement Logging Failed</h4>
                        <p>${result.message || 'Unknown error occurred'}</p>
                    `;
                }
            }
        } catch (error) {
            console.error('Error logging movement:', error);
            alert('An error occurred while logging the movement');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-map-marker-alt"></i> Log Movement';
        }
    });
    
    // Set up scan button (simulation)
    const scanBtn = document.getElementById('scan-tag-btn');
    if (scanBtn) {
        scanBtn.addEventListener('click', () => {
            alert('RFID scanning functionality would be integrated with hardware here. For demo purposes, please enter the tag ID manually.');
        });
    }
},
    
    // Update blockchain connection status display
    updateBlockchainStatus: function() {
        if (typeof blockchainClient !== 'undefined') {
            blockchainClient.checkConnection()
                .then(status => {
                    console.log('Blockchain status:', status);
                })
                .catch(error => {
                    console.error('Error checking blockchain status:', error);
                });
        } else {
            console.warn('Blockchain client is not available');
            const statusElement = document.getElementById('blockchain-connection-status');
            if (statusElement) {
                statusElement.textContent = 'Blockchain client not initialized';
                statusElement.style.color = '#e67e22';
            }
        }
    },
    
    // Handle client-side navigation
    navigateTo: function(path, addToHistory = true) {
        // Add current page to navigation history if it exists and we should add to history
        if (addToHistory && this.state.navigation.currentPage) {
            this.state.navigation.history.push(this.state.navigation.currentPage);
        }
        
        // Update current page
        this.state.navigation.currentPage = path;
        
        // Remove 'active' class from all navigation links
        document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
        
        // Add 'active' class to the clicked link
        const activeLink = document.querySelector(`.nav-link[href="${path}"]`);
        if (activeLink) activeLink.classList.add('active');
        
        // Update page content based on route
        this.updateContentForRoute(path);
        
        // Prevent default browser navigation
        return false;
    },
    
    // Navigate back to previous page
    goBack: function() {
        if (this.state.navigation.history.length > 0) {
            // Get the last page from history
            const previousPage = this.state.navigation.history.pop();
            
            // Navigate to it without adding the current page to history (to avoid loops)
            this.navigateTo(previousPage, false);
            return true;
        } else {
            // Default to dashboard if no history
            this.navigateTo('/dashboard', false);
            return false;
        }
    },
    
    // Handle role selection
    selectRole: function(role) {
        console.log(`Role selected: ${role}`);
        this.state.selectedRole = role;
        
        // Hide role selection and show auth container
        document.getElementById('role-selection').style.display = 'none';
        document.getElementById('auth-container').style.display = 'block';
        
        // Update role info in auth sidebar
        this.updateAuthSidebarRole(role);
        
        // Set selected role in signup form if visible
        const signupRoleInput = document.getElementById('signup-role');
        if (signupRoleInput) {
            signupRoleInput.value = role.charAt(0).toUpperCase() + role.slice(1);
        }
    },
    
    // Update auth sidebar based on selected role
    updateAuthSidebarRole: function(role) {
        const roleInfo = document.getElementById('role-info');
        const authSidebar = document.getElementById('auth-sidebar');
        
        let roleData = {
            icon: '',
            title: '',
            description: '',
            color: ''
        };
        
        switch(role) {
            case 'admin':
                roleData.icon = '<i class="fas fa-crown"></i>';
                roleData.title = 'Administrator';
                roleData.description = 'Access full system controls, manage users, view audit logs, and oversee the entire chemical traceability network.';
                roleData.color = '#3498db';
                break;
            case 'manufacturer':
                roleData.icon = '<i class="fas fa-industry"></i>';
                roleData.title = 'Manufacturer';
                roleData.description = 'Register new chemicals, assign RFID tags, and initiate the supply chain with blockchain verification.';
                roleData.color = '#27ae60';
                break;
            case 'distributor':
                roleData.icon = '<i class="fas fa-truck"></i>';
                roleData.title = 'Distributor';
                roleData.description = 'Manage transportation logs, track chemical movement, and update blockchain records during transit.';
                roleData.color = '#f39c12';
                break;
            case 'customer':
                roleData.icon = '<i class="fas fa-flask"></i>';
                roleData.title = 'Customer';
                roleData.description = 'Receive and verify chemical deliveries, maintain compliance records, and manage inventory.';
                roleData.color = '#e74c3c';
                break;
        }
        
        if (authSidebar) {
            authSidebar.style.backgroundColor = roleData.color;
        }
        
        if (roleInfo) {
            roleInfo.innerHTML = `
                <div class="role-name">
                    <div class="role-name-icon">${roleData.icon}</div>
                    <h3>${roleData.title}</h3>
                </div>
                <div class="role-description">${roleData.description}</div>
            `;
        }
    },
    
    // Switch between login and signup tabs
    switchAuthTab: function(tabName) {
        // Update tab buttons
        document.querySelectorAll('.auth-tab').forEach(tab => {
            if (tab.getAttribute('data-tab') === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Update form visibility
        document.querySelectorAll('.auth-form').forEach(form => {
            if (form.id === `${tabName}-form`) {
                form.classList.add('active');
            } else {
                form.classList.remove('active');
            }
        });
    },
    
    // Handle login form submission
    handleLogin: function() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        if (!email || !password) {
            alert('Please enter both email and password');
            return;
        }
        
        // In a real app, you would call an API here
        console.log(`Login attempt with email: ${email}`);
        
        // For demo purposes, simulate successful login
        this.simulateSuccessfulAuth({
            name: email.split('@')[0],
            email: email,
            role: this.state.selectedRole
        });
    },
    
    // Handle signup form submission
    handleSignup: function() {
        const name = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm').value;
        
        if (!name || !email || !password || !confirmPassword) {
            alert('Please fill in all fields');
            return;
        }
        
        if (password !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }
        
        // In a real app, you would call an API here
        console.log(`Signup attempt with email: ${email}`);
        
        // For demo purposes, simulate successful signup
        this.simulateSuccessfulAuth({
            name: name,
            email: email,
            role: this.state.selectedRole
        });
    },
    
    // Keep this space intentionally empty to maintain line numbering
    // The legacyNavigateTo function has been removed in favor of the main navigateTo function
    // to maintain a single, consistent navigation method throughout the app
    
    
    // Simulate successful authentication (login/signup)
    async simulateSuccessfulAuth(userData) {
        try {
            // Update application state
            this.state.currentUser = userData;
            
            // Notify auth module if available
            if (window.AuthModule && typeof window.AuthModule.onAuthSuccess === 'function') {
                await window.AuthModule.onAuthSuccess(userData);
            }
            
            // Show welcome notification
            showNotification(`Welcome, ${userData.name || 'User'}!`, 'success');
            
            // Dispatch auth success event for other modules
            document.dispatchEvent(new CustomEvent('authSuccess', { detail: userData }));
            
            // Navigate to dashboard
            this.navigateTo('dashboard');
            
        } catch (error) {
            console.error('Error in auth success handler:', error);
            showNotification('Error initializing user session', 'error');
        }
    },
    
    // Build and show the appropriate dashboard based on user role
    buildDashboard: function() {
        const dashboardContainer = document.getElementById('dashboard-container');
        if (!dashboardContainer) return;
        
        const role = this.state.selectedRole;
        const user = this.state.currentUser;
        
        // Create main dashboard structure
        dashboardContainer.innerHTML = this.getDashboardHTML(role, user);
        dashboardContainer.style.display = 'block';
        
        // Set up dashboard event listeners
        this.setupDashboardEvents();
        
        // Check blockchain status again after dashboard is built
        this.updateDashboardBlockchainStatus();
    },
    
    // Generate dashboard HTML based on role
    getDashboardHTML: function(role, user) {
        const roleTitle = role.charAt(0).toUpperCase() + role.slice(1);
        
        // Common dashboard structure
        let html = `
            <div class="dashboard-sidebar" id="dashboard-sidebar">
                <div class="dashboard-logo">
                    <img src="./assets/rvlogo.jpg" alt="ChemTrack Logo">
                    <div class="dashboard-logo-text">
                        <h3>ChemTrack</h3>
                        <p>Chemical Traceability</p>
                    </div>
                </div>
                
                <ul class="sidebar-menu">
                    <li class="sidebar-item">
                        <a href="#overview" class="sidebar-link active" data-page="overview">
                            <span class="sidebar-icon"><i class="fas fa-tachometer-alt"></i></span>
                            Dashboard
                        </a>
                    </li>
                    
                    ${this.getRoleSpecificMenuItems(role)}
                    
                    <div class="sidebar-divider"></div>
                    
                    <li class="sidebar-item">
                        <a href="#blockchain" class="sidebar-link" data-page="blockchain">
                            <span class="sidebar-icon"><i class="fas fa-link"></i></span>
                            Blockchain Status
                        </a>
                    </li>
                    
                    <li class="sidebar-item">
                        <a href="#settings" class="sidebar-link" data-page="settings">
                            <span class="sidebar-icon"><i class="fas fa-cog"></i></span>
                            Settings
                        </a>
                    </li>
                </ul>
                
                <div class="sidebar-footer">
                    &copy; 2025 ChemTrack System
                </div>
            </div>
            
            <div class="dashboard-main">
                <div class="dashboard-header">
                    <div class="page-title">
                        <h1>Dashboard</h1>
                        <ul class="breadcrumb">
                            <li class="breadcrumb-item">ChemTrack</li>
                            <li class="breadcrumb-item">${roleTitle} Portal</li>
                        </ul>
                    </div>
                    
                    <div class="header-actions">
                        <div class="blockchain-status disconnected" id="header-blockchain-status">
                            <div class="blockchain-status-icon"></div>
                            <span>Checking blockchain...</span>
                        </div>
                        
                        <div class="user-dropdown" id="user-dropdown">
                            <button class="user-dropdown-toggle">
                                <div class="user-avatar">${user.name.charAt(0).toUpperCase()}</div>
                                <div class="user-info">
                                    <div class="user-name">${user.name}</div>
                                    <div class="user-role">${roleTitle}</div>
                                </div>
                                <i class="fas fa-chevron-down chevron-icon"></i>
                            </button>
                            
                            <div class="user-dropdown-menu">
                                <a href="#profile" class="dropdown-item">
                                    <i class="fas fa-user"></i> Profile
                                </a>
                                <a href="#settings" class="dropdown-item">
                                    <i class="fas fa-cog"></i> Settings
                                </a>
                                <div class="dropdown-divider"></div>
                                <a href="#logout" class="dropdown-item" id="logout-btn">
                                    <i class="fas fa-sign-out-alt"></i> Logout
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-content" id="dashboard-content">
                    <!-- Content will be loaded dynamically based on selected page -->
                    ${this.getDashboardContent(role)}
                </div>
            </div>
        `;
        
        return html;
    },
    
    // Get menu items specific to user role
    getRoleSpecificMenuItems: function(role) {
        switch(role) {
            case 'admin':
                return `
                    <li class="sidebar-item">
                        <a href="#users" class="sidebar-link" data-page="users">
                            <span class="sidebar-icon"><i class="fas fa-users"></i></span>
                            User Management
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#audit" class="sidebar-link" data-page="audit">
                            <span class="sidebar-icon"><i class="fas fa-clipboard-list"></i></span>
                            Audit Logs
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#chemicals" class="sidebar-link" data-page="chemicals">
                            <span class="sidebar-icon"><i class="fas fa-flask"></i></span>
                            All Chemicals
                        </a>
                    </li>
                `;
            case 'manufacturer':
                return `
                    <li class="sidebar-item">
                        <a href="#register" class="sidebar-link" data-page="register">
                            <span class="sidebar-icon"><i class="fas fa-plus-circle"></i></span>
                            Register Chemical
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#inventory" class="sidebar-link" data-page="inventory">
                            <span class="sidebar-icon"><i class="fas fa-boxes"></i></span>
                            Inventory
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#shipments" class="sidebar-link" data-page="shipments">
                            <span class="sidebar-icon"><i class="fas fa-truck-loading"></i></span>
                            Shipments
                        </a>
                    </li>
                `;
            case 'distributor':
                return `
                    <li class="sidebar-item">
                        <a href="#track" class="sidebar-link" data-page="track">
                            <span class="sidebar-icon"><i class="fas fa-map-marker-alt"></i></span>
                            Track Movement
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#scan" class="sidebar-link" data-page="scan">
                            <span class="sidebar-icon"><i class="fas fa-qrcode"></i></span>
                            Scan RFID
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#transfers" class="sidebar-link" data-page="transfers">
                            <span class="sidebar-icon"><i class="fas fa-exchange-alt"></i></span>
                            Transfers
                        </a>
                    </li>
                `;
            case 'customer':
                return `
                    <li class="sidebar-item">
                        <a href="#verify" class="sidebar-link" data-page="verify">
                            <span class="sidebar-icon"><i class="fas fa-check-circle"></i></span>
                            Verify Chemical
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#history" class="sidebar-link" data-page="history">
                            <span class="sidebar-icon"><i class="fas fa-history"></i></span>
                            Movement History
                        </a>
                    </li>
                    <li class="sidebar-item">
                        <a href="#inventory" class="sidebar-link" data-page="inventory">
                            <span class="sidebar-icon"><i class="fas fa-boxes"></i></span>
                            My Inventory
                        </a>
                    </li>
                `;
            default:
                return '';
        }
    },

    // Get initial dashboard content based on role
    getDashboardContent: function(role) {
        // Common dashboard overview with role-specific sections
        return `
            <div class="card" style="grid-column: span 2;">
                <div class="card-header">
                    <h3 class="card-title">Welcome to ChemTrack Dashboard</h3>
                </div>
                <div class="card-body">
                    <p>This blockchain-powered chemical traceability system helps manage and track chemicals throughout their lifecycle.</p>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Blockchain Status</h3>
                </div>
                <div class="card-body" id="blockchain-status-card">
                    <p><strong>Status:</strong> <span id="blockchain-connection-status">Checking...</span></p>
                    <p><strong>Last Check:</strong> <span id="blockchain-last-check">Just now</span></p>
                </div>
            </div>
            
            ${this.getRoleSpecificDashboardContent(role)}
            
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Quick Actions</h3>
                </div>
                <div class="card-body">
                    ${this.getQuickActionButtons(role)}
                </div>
            </div>
        `;
    },
    
    // Get role-specific dashboard content
    getRoleSpecificDashboardContent: function(role) {
        switch(role) {
            case 'admin':
                return `
                    <div class="card mb-4">
                        <div class="card-header">
                            <h3 class="card-title">System Overview</h3>
                        </div>
                        <div class="card-body">
                            <div class="stat-container">
                                <div class="stat-item">
                                    <h4>157</h4>
                                    <p>Chemicals Registered</p>
                                </div>
                                <div class="stat-item">
                                    <h4>42</h4>
                                    <p>Active Users</p>
                                </div>
                                <div class="stat-item">
                                    <h4>98%</h4>
                                    <p>Blockchain Verified</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mb-4">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h3 class="card-title">Database Management</h3>
                            <button type="button" id="backToDashboard" class="btn btn-sm btn-outline-secondary">
                                <i class="fas fa-arrow-left"></i> Back to Dashboard
                            </button>
                        </div>
                        <div class="card-body">
                            <ul class="nav nav-tabs" id="databaseTabs" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active" id="chemicals-tab" data-bs-toggle="tab" data-bs-target="#chemicals" type="button" role="tab" aria-controls="chemicals" aria-selected="true">
                                        Chemical Database
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="movements-tab" data-bs-toggle="tab" data-bs-target="#movements" type="button" role="tab" aria-controls="movements" aria-selected="false">
                                        Movement Logs
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="users-tab" data-bs-toggle="tab" data-bs-target="#users" type="button" role="tab" aria-controls="users" aria-selected="false">
                                        User Management
                                    </button>
                                </li>
                            </ul>
                            
                            <div class="tab-content pt-3" id="databaseTabsContent">
                                <!-- Chemicals Table Tab -->
                                <div class="tab-pane fade show active" id="chemicals" role="tabpanel" aria-labelledby="chemicals-tab">
                                    <div class="d-flex justify-content-between mb-3">
                                        <div class="input-group" style="max-width: 300px;">
                                            <input type="text" id="chemicalSearchInput" class="form-control" placeholder="Search chemicals...">
                                            <button class="btn btn-outline-secondary" type="button" id="chemicalSearchBtn">
                                                <i class="fas fa-search"></i>
                                            </button>
                                        </div>
                                        <div>
                                            <button class="btn btn-sm btn-outline-primary" id="refreshChemicalsBtn">
                                                <i class="fas fa-sync"></i> Refresh
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div class="table-responsive">
                                        <table class="table table-bordered table-hover" id="chemicalTable">
                                            <thead class="table-light">
                                                <tr>
                                                    <th>ID</th>
                                                    <th>Name</th>
                                                    <th>RFID Tag</th>
                                                    <th>Manufacturer</th>
                                                    <th>Quantity</th>
                                                    <th>Current Location</th>
                                                    <th>Expiry Date</th>
                                                    <th>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody id="chemicalTableBody">
                                                <!-- Chemical data will be loaded here dynamically -->
                                                <tr>
                                                    <td colspan="8" class="text-center">Loading chemical data...</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                
                                <!-- Movement Logs Tab -->
                                <div class="tab-pane fade" id="movements" role="tabpanel" aria-labelledby="movements-tab">
                                    <div class="d-flex justify-content-between mb-3">
                                        <div class="input-group" style="max-width: 300px;">
                                            <input type="text" id="movementSearchInput" class="form-control" placeholder="Search by tag ID...">
                                            <button class="btn btn-outline-secondary" type="button" id="movementSearchBtn">
                                                <i class="fas fa-search"></i>
                                            </button>
                                        </div>
                                        <div>
                                            <button class="btn btn-sm btn-outline-primary" id="refreshMovementsBtn">
                                                <i class="fas fa-sync"></i> Refresh
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div class="table-responsive">
                                        <table class="table table-bordered table-hover" id="movementTable">
                                            <thead class="table-light">
                                                <tr>
                                                    <th>ID</th>
                                                    <th>Tag ID</th>
                                                    <th>Location</th>
                                                    <th>Timestamp</th>
                                                    <th>Moved By</th>
                                                    <th>Purpose</th>
                                                    <th>Status</th>
                                                    <th>Blockchain Verified</th>
                                                </tr>
                                            </thead>
                                            <tbody id="movementTableBody">
                                                <!-- Movement data will be loaded here dynamically -->
                                                <tr>
                                                    <td colspan="8" class="text-center">Loading movement data...</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                
                                <!-- User Management Tab -->
                                <div class="tab-pane fade" id="users" role="tabpanel" aria-labelledby="users-tab">
                                    <div class="card">
                                        <div class="card-body">
                                            <h5 class="card-title">User Access Control</h5>
                                            <p>Manage user permissions and roles for the Chemical Traceability System.</p>
                                            <div class="table-responsive">
                                                <table class="table table-bordered table-hover" id="userTable">
                                                    <thead class="table-light">
                                                        <tr>
                                                            <th>ID</th>
                                                            <th>Username</th>
                                                            <th>Email</th>
                                                            <th>Role</th>
                                                            <th>Status</th>
                                                            <th>Actions</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody id="userTableBody">
                                                        <!-- User data will be loaded here dynamically -->
                                                        <tr>
                                                            <td colspan="6" class="text-center">Loading user data...</td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Blockchain Verification Status</h3>
                        </div>
                        <div class="card-body">
                            <div class="blockchain-status-container">
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <div class="card bg-light">
                                            <div class="card-body">
                                                <h5 class="card-title">Connection Status</h5>
                                                <div id="blockchainConnectionStatus">
                                                    <span class="badge bg-secondary">Checking...</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card bg-light">
                                            <div class="card-body">
                                                <h5 class="card-title">Verification Statistics</h5>
                                                <div id="blockchainVerificationStats">
                                                    <div class="d-flex justify-content-between">
                                                        <span>Chemicals Registered:</span>
                                                        <span id="registeredChemicalsCount">...</span>
                                                    </div>
                                                    <div class="d-flex justify-content-between">
                                                        <span>Movements Recorded:</span>
                                                        <span id="recordedMovementsCount">...</span>
                                                    </div>
                                                    <div class="d-flex justify-content-between">
                                                        <span>Verification Rate:</span>
                                                        <span id="verificationRate">...</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <button class="btn btn-primary" id="refreshBlockchainStatus">
                                    <i class="fas fa-sync"></i> Check Blockchain Status
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
            case 'manufacturer':
                return `
                    <div class="card mb-4">
                        <div class="card-header">
                            <h3 class="card-title">Manufacturing Stats</h3>
                        </div>
                        <div class="card-body">
                            <div class="stat-container">
                                <div class="stat-item">
                                    <h4>47</h4>
                                    <p>Chemicals Produced</p>
                                </div>
                                <div class="stat-item">
                                    <h4>12</h4>
                                    <p>Pending Shipments</p>
                                </div>
                                <div class="stat-item">
                                    <h4>100%</h4>
                                    <p>Compliance Rate</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h3 class="card-title">Register New Chemical</h3>
                            <button type="button" id="backToDashboard" class="btn btn-sm btn-outline-secondary">
                                <i class="fas fa-arrow-left"></i> Back to Dashboard
                            </button>
                        </div>
                        <div class="card-body">
                            <form id="registerChemicalForm">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="chemicalName" class="form-label">Chemical Name</label>
                                            <input type="text" class="form-control" id="chemicalName" name="name" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="rfidTag" class="form-label">RFID Tag</label>
                                            <input type="text" class="form-control" id="rfidTag" name="rfid_tag" required>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label for="manufacturer" class="form-label">Manufacturer</label>
                                            <input type="text" class="form-control" id="manufacturer" name="manufacturer" required>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label for="quantity" class="form-label">Quantity</label>
                                            <input type="number" step="0.01" class="form-control" id="quantity" name="quantity" required>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label for="unit" class="form-label">Unit</label>
                                            <select class="form-select" id="unit" name="unit" required>
                                                <option value="">Select Unit</option>
                                                <option value="kg">Kilogram (kg)</option>
                                                <option value="g">Gram (g)</option>
                                                <option value="L">Liter (L)</option>
                                                <option value="mL">Milliliter (mL)</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="expiryDate" class="form-label">Expiry Date</label>
                                            <input type="date" class="form-control" id="expiryDate" name="expiry_date">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="receivedDate" class="form-label">Received Date</label>
                                            <input type="date" class="form-control" id="receivedDate" name="received_date">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="batchNumber" class="form-label">Batch Number</label>
                                            <input type="text" class="form-control" id="batchNumber" name="batch_number">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="casNumber" class="form-label">CAS Number</label>
                                            <input type="text" class="form-control" id="casNumber" name="cas_number">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="hazardClass" class="form-label">Hazard Class</label>
                                            <select class="form-select" id="hazardClass" name="hazard_class">
                                                <option value="">Select Hazard Class</option>
                                                <option value="Class 1">Class 1 - Explosives</option>
                                                <option value="Class 2">Class 2 - Gases</option>
                                                <option value="Class 3">Class 3 - Flammable Liquids</option>
                                                <option value="Class 4">Class 4 - Flammable Solids</option>
                                                <option value="Class 5">Class 5 - Oxidizing Substances</option>
                                                <option value="Class 6">Class 6 - Toxic Substances</option>
                                                <option value="Class 7">Class 7 - Radioactive Materials</option>
                                                <option value="Class 8">Class 8 - Corrosive Substances</option>
                                                <option value="Class 9">Class 9 - Miscellaneous Dangerous Goods</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="storageCondition" class="form-label">Storage Condition</label>
                                            <input type="text" class="form-control" id="storageCondition" name="storage_condition">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="description" class="form-label">Description</label>
                                    <textarea class="form-control" id="description" name="description" rows="3"></textarea>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="initialLocation" class="form-label">Initial Location</label>
                                    <input type="text" class="form-control" id="initialLocation" name="current_location" value="Storage" required>
                                </div>
                                
                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                    <button type="submit" class="btn btn-primary">
                                        <i class="fas fa-plus-circle"></i> Register Chemical
                                    </button>
                                </div>
                                
                                <div id="registrationStatus" class="mt-3 d-none"></div>
                            </form>
                        </div>
                    </div>
                `;
                
            case 'distributor':
                return `
                    <div class="card mb-4">
                        <div class="card-header">
                            <h3 class="card-title">Distribution Stats</h3>
                        </div>
                        <div class="card-body">
                            <div class="stat-container">
                                <div class="stat-item">
                                    <h4>35</h4>
                                    <p>Active Shipments</p>
                                </div>
                                <div class="stat-item">
                                    <h4>8</h4>
                                    <p>Pending Transfers</p>
                                </div>
                                <div class="stat-item">
                                    <h4>156</h4>
                                    <p>Completed Transfers</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mb-4">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h3 class="card-title">Update Chemical Location</h3>
                            <button type="button" id="backToDashboard" class="btn btn-sm btn-outline-secondary">
                                <i class="fas fa-arrow-left"></i> Back to Dashboard
                            </button>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <form id="updateLocationForm">
                                        <div class="mb-3">
                                            <label for="rfidTagSearch" class="form-label">Chemical RFID Tag</label>
                                            <div class="input-group">
                                                <input type="text" class="form-control" id="rfidTagSearch" name="rfid_tag" required>
                                                <button class="btn btn-outline-primary" type="button" id="searchChemicalBtn">
                                                    <i class="fas fa-search"></i> Find
                                                </button>
                                            </div>
                                            <div class="form-text">Enter the RFID tag of the chemical to track</div>
                                        </div>
                                        
                                        <div id="chemicalDetailsContainer" class="mb-3 d-none">
                                            <div class="card bg-light">
                                                <div class="card-body">
                                                    <h5 id="chemicalName" class="mb-2">Chemical Name</h5>
                                                    <ul class="list-unstyled">
                                                        <li><strong>Manufacturer:</strong> <span id="chemicalManufacturer"></span></li>
                                                        <li><strong>Current Location:</strong> <span id="currentLocation"></span></li>
                                                        <li><strong>Last Updated:</strong> <span id="lastUpdated"></span></li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="newLocation" class="form-label">New Location</label>
                                            <input type="text" class="form-control" id="newLocation" name="location" required>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="purpose" class="form-label">Purpose</label>
                                            <select class="form-select" id="purpose" name="purpose" required>
                                                <option value="">Select Purpose</option>
                                                <option value="Shipping">Shipping</option>
                                                <option value="Storage">Storage Transfer</option>
                                                <option value="Processing">Processing</option>
                                                <option value="Testing">Quality Testing</option>
                                                <option value="Disposal">Disposal</option>
                                            </select>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="remarks" class="form-label">Remarks</label>
                                            <textarea class="form-control" id="remarks" name="remarks" rows="2"></textarea>
                                        </div>
                                        
                                        <div class="d-grid gap-2">
                                            <button type="submit" class="btn btn-primary" id="updateLocationBtn" disabled>
                                                <i class="fas fa-map-marker-alt"></i> Update Location
                                            </button>
                                        </div>
                                    </form>
                                </div>
                                
                                <div class="col-md-6">
                                    <div class="card h-100">
                                        <div class="card-header">
                                            <h5 class="card-title">Blockchain Verification</h5>
                                        </div>
                                        <div class="card-body">
                                            <div id="blockchainVerificationStatus" class="mb-3">
                                                <div class="alert alert-info">
                                                    <i class="fas fa-info-circle"></i> Search for a chemical to view its blockchain verification status.
                                                </div>
                                            </div>
                                            
                                            <div id="verificationDetails" class="d-none">
                                                <h6>Verification Details</h6>
                                                <div class="table-responsive">
                                                    <table class="table table-bordered table-sm">
                                                        <thead class="table-light">
                                                            <tr>
                                                                <th>Property</th>
                                                                <th>Status</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            <tr>
                                                                <td>Chain Integrity</td>
                                                                <td id="chainIntegrity"><span class="badge bg-secondary">Unknown</span></td>
                                                            </tr>
                                                            <tr>
                                                                <td>Last Verification</td>
                                                                <td id="lastVerification">-</td>
                                                            </tr>
                                                            <tr>
                                                                <td>Block Number</td>
                                                                <td id="blockNumber">-</td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card-footer">
                                            <button class="btn btn-outline-primary btn-sm" id="verifyBlockchainBtn" disabled>
                                                <i class="fas fa-shield-alt"></i> Verify on Blockchain
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Movement History</h3>
                        </div>
                        <div class="card-body">
                            <div id="movementHistoryContent">
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i> Search for a chemical above to view its movement history.
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
            case 'customer':
                return `
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Inventory Stats</h3>
                        </div>
                        <div class="card-body">
                            <div class="stat-container">
                                <div class="stat-item">
                                    <h4>23</h4>
                                    <p>Chemicals in Stock</p>
                                </div>
                                <div class="stat-item">
                                    <h4>5</h4>
                                    <p>Pending Deliveries</p>
                                </div>
                                <div class="stat-item">
                                    <h4>100%</h4>
                                    <p>Verified Chemicals</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
            default:
                return '';
        }
    },
    
    // Generate quick action buttons based on user role
    getQuickActionButtons: function(role) {
        switch(role) {
            case 'admin':
                return `
                    <button class="action-btn"><i class="fas fa-user-plus"></i> Add User</button>
                    <button class="action-btn"><i class="fas fa-search"></i> Chemical Lookup</button>
                    <button class="action-btn"><i class="fas fa-file-export"></i> Export Reports</button>
                `;
                
            case 'manufacturer':
                return `
                    <button class="action-btn" id="register-chemical-btn"><i class="fas fa-plus-circle"></i> Register New Chemical</button>
                    <button class="action-btn"><i class="fas fa-truck-loading"></i> Create Shipment</button>
                    <button class="action-btn"><i class="fas fa-print"></i> Print RFID Tags</button>
                `;
                
            case 'distributor':
                return `
                    <button class="action-btn" id="scan-rfid-btn"><i class="fas fa-qrcode"></i> Scan RFID Tag</button>
                    <button class="action-btn"><i class="fas fa-map-marker-alt"></i> Log Movement</button>
                    <button class="action-btn"><i class="fas fa-exchange-alt"></i> Transfer Ownership</button>
                `;
                
            case 'customer':
                return `
                    <button class="action-btn" id="verify-chemical-btn"><i class="fas fa-check-circle"></i> Verify Chemical</button>
                    <button class="action-btn"><i class="fas fa-history"></i> View History</button>
                    <button class="action-btn"><i class="fas fa-file-import"></i> Import Certificate</button>
                `;
                
            default:
                return '';
        }
    },
    
    // Set up dashboard event listeners
    setupDashboardEvents: function() {
        // Toggle user dropdown menu
        const userDropdown = document.getElementById('user-dropdown');
        if (userDropdown) {
            const dropdownToggle = userDropdown.querySelector('.user-dropdown-toggle');
            if (dropdownToggle) {
                dropdownToggle.addEventListener('click', function() {
                    userDropdown.classList.toggle('open');
                });
            }
            
            // Close dropdown when clicking elsewhere
            document.addEventListener('click', function(event) {
                if (!userDropdown.contains(event.target)) {
                    userDropdown.classList.remove('open');
                }
            });
        }
        
        // Set up back to dashboard buttons event listeners
        const backButtons = document.querySelectorAll('#backToDashboard');
        backButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.goBack();
            });
        });
        
        // Setup search chemical button events for distributor page
        const searchChemicalBtn = document.getElementById('searchChemicalBtn');
        if (searchChemicalBtn) {
            searchChemicalBtn.addEventListener('click', () => {
                this.findChemicalByRfid();
            });
        }
        
        // Setup verify blockchain button for distributor page
        const verifyBlockchainBtn = document.getElementById('verifyBlockchainBtn');
        if (verifyBlockchainBtn) {
            verifyBlockchainBtn.addEventListener('click', () => {
                this.verifyChemicalOnBlockchain();
            });
        }
        
        // Set up update location form submission
        const updateLocationForm = document.getElementById('updateLocationForm');
        if (updateLocationForm) {
            updateLocationForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updateChemicalLocation();
            });
        }
    },
    
    // Find chemical by RFID for distributor page
    findChemicalByRfid: function() {
        const rfidTag = document.getElementById('rfidTagSearch').value;
        if (!rfidTag) {
            this.showNotification('Please enter an RFID tag', 'warning');
            return;
        }
        
        // Show loading state
        document.getElementById('searchChemicalBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        
        // API call to get chemical details
        fetch(`${this.baseUrl}/api/chemicals/${rfidTag}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Chemical not found');
                }
                return response.json();
            })
            .then(data => {
                // Update UI with chemical details
                this.state.currentChemical = data;
                
                // Show chemical details
                document.getElementById('chemicalDetailsContainer').classList.remove('d-none');
                document.getElementById('chemicalName').textContent = data.name;
                document.getElementById('chemicalManufacturer').textContent = data.manufacturer;
                document.getElementById('currentLocation').textContent = data.location || 'Unknown';
                document.getElementById('lastUpdated').textContent = new Date(data.last_updated).toLocaleString();
                
                // Enable update button
                document.getElementById('updateLocationBtn').disabled = false;
                document.getElementById('verifyBlockchainBtn').disabled = false;
                
                // Load movement history
                this.loadMovementHistory(rfidTag);
                
                // Update verification status
                document.getElementById('blockchainVerificationStatus').innerHTML = `
                    <div class="alert alert-primary">
                        <i class="fas fa-info-circle"></i> Chemical ${data.name} (RFID: ${data.rfid_tag}) found. Verify on blockchain for traceability.
                    </div>
                `;
                
                // Reset button
                document.getElementById('searchChemicalBtn').innerHTML = '<i class="fas fa-search"></i> Find';
            })
            .catch(error => {
                document.getElementById('blockchainVerificationStatus').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle"></i> ${error.message}
                    </div>
                `;
                document.getElementById('searchChemicalBtn').innerHTML = '<i class="fas fa-search"></i> Find';
            });
    },
    
    // Load movement history for a chemical
    loadMovementHistory: function(rfidTag) {
        fetch(`${this.baseUrl}/api/movements/${rfidTag}`)
            .then(response => response.json())
            .then(data => {
                const movementHistoryContent = document.getElementById('movementHistoryContent');
                if (data.length === 0) {
                    movementHistoryContent.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> No movement history found for this chemical.
                        </div>
                    `;
                    return;
                }
                
                // Store in state
                this.state.movementHistory = data;
                
                // Create table
                let tableHTML = `
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>From</th>
                                    <th>To</th>
                                    <th>Purpose</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.forEach(movement => {
                    const date = new Date(movement.timestamp).toLocaleString();
                    const status = movement.verified ? 
                        '<span class="badge bg-success">Verified</span>' : 
                        '<span class="badge bg-warning text-dark">Pending</span>';
                    
                    tableHTML += `
                        <tr>
                            <td>${date}</td>
                            <td>${movement.from_location || 'N/A'}</td>
                            <td>${movement.to_location}</td>
                            <td>${movement.purpose}</td>
                            <td>${status}</td>
                        </tr>
                    `;
                });
                
                tableHTML += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                movementHistoryContent.innerHTML = tableHTML;
            })
            .catch(error => {
                console.error('Error loading movement history:', error);
                document.getElementById('movementHistoryContent').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle"></i> Error loading movement history.
                    </div>
                `;
            });
    },
    
    // Verify chemical on blockchain
    verifyChemicalOnBlockchain: function() {
        if (!this.state.currentChemical) {
            this.showNotification('Please search for a chemical first', 'warning');
            return;
        }
        
        const rfidTag = this.state.currentChemical.rfid_tag;
        const verifyBtn = document.getElementById('verifyBlockchainBtn');
        
        // Show loading state
        verifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
        verifyBtn.disabled = true;
        
        // Call blockchain verification endpoint
        fetch(`${this.baseUrl}/api/blockchain/verify/${rfidTag}`)
            .then(response => response.json())
            .then(data => {
                // Update verification UI
                document.getElementById('verificationDetails').classList.remove('d-none');
                
                // Update verification status
                if (data.verified) {
                    document.getElementById('chainIntegrity').innerHTML = 
                        '<span class="badge bg-success">Verified</span>';
                } else {
                    document.getElementById('chainIntegrity').innerHTML = 
                        '<span class="badge bg-danger">Failed</span>';
                }
                
                document.getElementById('lastVerification').textContent = new Date().toLocaleString();
                document.getElementById('blockNumber').textContent = data.block_number || '-';
                
                // Update button state
                verifyBtn.innerHTML = '<i class="fas fa-shield-alt"></i> Verify on Blockchain';
                verifyBtn.disabled = false;
                
                // Show notification
                this.showNotification('Blockchain verification complete', 'success');
            })
            .catch(error => {
                console.error('Error verifying on blockchain:', error);
                document.getElementById('blockchainVerificationStatus').innerHTML += `
                    <div class="alert alert-danger mt-3">
                        <i class="fas fa-exclamation-circle"></i> Error during blockchain verification.
                    </div>
                `;
                verifyBtn.innerHTML = '<i class="fas fa-shield-alt"></i> Verify on Blockchain';
                verifyBtn.disabled = false;
            });
    },
    
    // Update chemical location
    updateChemicalLocation: function() {
        if (!this.state.currentChemical) {
            this.showNotification('Please search for a chemical first', 'warning');
            return;
        }
        
        const form = document.getElementById('updateLocationForm');
        const rfidTag = this.state.currentChemical.rfid_tag;
        const newLocation = document.getElementById('newLocation').value;
        const purpose = document.getElementById('purpose').value;
        const remarks = document.getElementById('remarks').value;
        
        // Show loading state
        const submitButton = document.getElementById('updateLocationBtn');
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        submitButton.disabled = true;
        
        // Prepare data
        const movementData = {
            rfid_tag: rfidTag,
            from_location: this.state.currentChemical.location || 'Unknown',
            to_location: newLocation,
            purpose: purpose,
            remarks: remarks
        };
        
        // Send update to API
        fetch(`${this.baseUrl}/api/movements/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(movementData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update location');
                }
                return response.json();
            })
            .then(data => {
                // Update UI
                document.getElementById('currentLocation').textContent = newLocation;
                document.getElementById('lastUpdated').textContent = new Date().toLocaleString();
                
                // Reset form
                form.reset();
                
                // Update button state
                submitButton.innerHTML = '<i class="fas fa-map-marker-alt"></i> Update Location';
                submitButton.disabled = false;
                
                // Show notification
                this.showNotification('Location updated successfully', 'success');
                
                // Update movement history
                this.loadMovementHistory(rfidTag);
                
                // Update chemical state
                this.state.currentChemical.location = newLocation;
            })
            .catch(error => {
                console.error('Error updating location:', error);
                submitButton.innerHTML = '<i class="fas fa-map-marker-alt"></i> Update Location';
                submitButton.disabled = false;
                this.showNotification(error.message, 'error');
            });
    },
    
    // Set up quick action buttons and events
    setupQuickActions: function() {
        // Register chemical button (Manufacturer)
        const registerChemicalBtn = document.getElementById('register-chemical-btn');
        if (registerChemicalBtn) {
            registerChemicalBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('register');
            });
        }
        
        // Scan RFID button (Distributor)
        const scanRfidBtn = document.getElementById('scan-rfid-btn');
        if (scanRfidBtn) {
            scanRfidBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('scan');
            });
        }
        
        // Verify chemical button (Customer)
        const verifyChemicalBtn = document.getElementById('verify-chemical-btn');
        if (verifyChemicalBtn) {
            verifyChemicalBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('verify');
            });
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleLogout();
            });
        }
    },
    
    // Set up page-specific event listeners
    setupPageEvents: function(page) {
        console.log(`Setting up events for page: ${page}`);
        
        // Add event listener for chemical registration form if it exists
        const chemicalRegistrationForm = document.getElementById('registerChemicalForm');
        if (chemicalRegistrationForm) {
            console.log('Setting up chemical registration form event listener');
            chemicalRegistrationForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleChemicalRegistration();
            });
        }
        
        // Setup quick actions for all pages
        this.setupQuickActions();
        
        // Page-specific event setup
        switch (page) {
            case 'dashboard':
                // Setup dashboard-specific events
                break;
            case 'register':
                // Setup register chemical form events
                const registerForm = document.getElementById('register-chemical-form');
                if (registerForm) {
                    registerForm.addEventListener('submit', (e) => {
                        e.preventDefault();
                        this.handleChemicalRegistration();
                    });
                }
                break;
            case 'scan':
                // Setup scan form events
                break;
            case 'verify':
                // Setup verify form events
                break;
            default:
                console.log(`No specific events to setup for page: ${page}`);
        }
    },
    
    /**
     * Loads and displays content for a specific dashboard page
     * @param {string} page - The page identifier to load
     */
    loadPageContent: function(page) {
        // Get the content container
        const contentContainer = document.getElementById('dashboard-content');
        if (!contentContainer) {
            console.error('Content container not found');
            return;
        }
        
        // Update page title and breadcrumb
        const pageTitle = document.querySelector('.page-title');
        const breadcrumb = document.querySelector('.breadcrumb .current');
        let pageTitleText = this.getPageTitle(page);
        
        if (pageTitle) {
            pageTitle.textContent = pageTitleText;
        }
        
        if (breadcrumb) {
            breadcrumb.textContent = pageTitleText;
        }
        
        // Show loading state
        this.showLoadingState(contentContainer, page);
        
        try {
            // Try to load page content through modules
            const content = this.loadPageContentFromModules(page, pageTitleText);
            
            // Update the content container
            contentContainer.innerHTML = content;
            
            // Set up page-specific event listeners
            this.setupPageEvents(page);
            
        } catch (error) {
            console.error(`Error loading page ${page}:`, error);
            this.handlePageLoadError(error, contentContainer, page);
        }
    },
    
    /**
     * Gets the title for a page
     * @param {string} page - The page identifier
     * @returns {string} The formatted page title
     */
    getPageTitle: function(page) {
        const titles = {
            'overview': 'Dashboard',
            'blockchain': 'Blockchain Status',
            'register': 'Register Chemical',
            'track': 'Track Movement',
            'verify': 'Verify Chemical'
        };
        
        return titles[page] || (page.charAt(0).toUpperCase() + page.slice(1));
    },
    
    /**
     * Updates the breadcrumb navigation
     * @param {string} pageTitle - The current page title
     */
    updateBreadcrumb: function(pageTitle) {
        const breadcrumb = document.querySelector('.breadcrumb');
        if (!breadcrumb) return;
        
        const roleTitle = this.state.selectedRole 
            ? this.state.selectedRole.charAt(0).toUpperCase() + this.state.selectedRole.slice(1) 
            : 'User';
            
        breadcrumb.innerHTML = [
            '<li class="breadcrumb-item">ChemTrack</li>',
            `<li class="breadcrumb-item">${roleTitle} Portal</li>`,
            `<li class="breadcrumb-item">${pageTitle}</li>`
        ].join('');
    },
    
    /**
     * Shows a loading state in the content container
     * @param {HTMLElement} container - The container to show the loading state in
     * @param {string} page - The page being loaded
     */
    showLoadingState: function(container, page) {
        if (!container) return;
        
        container.innerHTML = [
            '<div class="d-flex justify-content-center align-items-center" style="height: 300px;">',
            '  <div class="spinner-border text-primary" role="status">',
            '    <span class="visually-hidden">Loading...</span>',
            '  </div>',
            `  <span class="ms-3">Loading ${page}...</span>`,
            '</div>'
        ].join('');
    },
    
    /**
     * Attempts to load page content from modules
     * @param {string} page - The page to load content for
     * @param {string} pageTitle - The title of the page
     * @returns {string} The HTML content for the page
     */
    loadPageContentFromModules: function(page, pageTitle) {
        // Dispatch event to allow modules to handle page loading
        const pageLoadEvent = new CustomEvent('loadDashboardPage', {
            detail: { 
                page: page, 
                content: '',
                handled: false
            },
            cancelable: true
        });
        
        // Dispatch the event and check if any module handled it
        const eventHandled = document.dispatchEvent(pageLoadEvent);
        
        if (eventHandled && pageLoadEvent.detail.handled) {
            return pageLoadEvent.detail.content;
        }
        
        // Fallback to default page content if no module handled it
        return this.getDefaultPageContent(page, pageTitle);
    },
    
    /**
     * Gets the default content for a page
     * @param {string} page - The page identifier
     * @param {string} pageTitle - The page title
     * @returns {string} The HTML content for the page
     */
    getDefaultPageContent: function(page, pageTitle) {
        const pageContent = {
            'overview': () => this.getDashboardContent(this.state.selectedRole),
            'dashboard': () => this.getDashboardContent(this.state.selectedRole),
            'blockchain': () => {
                const content = this.getBlockchainStatusPage();
                this.updateDashboardBlockchainStatus();
                return content;
            },
            'register': () => this.getRegisterChemicalPage(),
            'track': () => this.getTrackMovementPage()
        };
        
        if (pageContent[page]) {
            return pageContent[page]();
        }
        
        // Default content for unknown pages
        return [
            '<div class="card" style="grid-column: span 3;">',
            '  <div class="card-header">',
            `    <h3 class="card-title">${pageTitle || page}</h3>`,
            '  </div>',
            '  <div class="card-body">',
            `    <p>This ${page} functionality is under development.</p>`,
            '  </div>',
            '</div>'
        ].join('');
    },
    
    /**
     * Handles errors that occur during page loading
     * @param {Error} error - The error that occurred
     * @param {HTMLElement} container - The container to display the error in
     * @param {string} page - The page that was being loaded
     */
    handlePageLoadError: function(error, container, page) {
        console.error('Error loading page ' + page + ':', error);
        
        if (!container) {
            return;
        }
        
        container.innerHTML = [
            '<div class="alert alert-danger">',
            '  <h4>Error Loading Page</h4>',
            '  <p>There was an error loading the requested page. Please try again later.</p>',
            '  <pre class="small text-muted mt-2">' + (error.message || 'Unknown error') + '</pre>',
            '</div>'
        ].join('');
    },
    
    /**
     * Get blockchain status page content
     * @returns {string} HTML content for the blockchain status page
     */
    getBlockchainStatusPage: function() {
        return [
            '<div class="card" style="grid-column: span 3;">',
            '  <div class="card-header">',
            '    <h3 class="card-title">Blockchain Connection</h3>',
            '  </div>',
            '  <div class="card-body">',
            '    <p><strong>Connection Status:</strong> <span id="blockchain-detail-status">Checking...</span></p>',
            '    <p><strong>Provider:</strong> <span id="blockchain-provider">-</span></p>',
            '    <p><strong>Smart Contract:</strong> <span id="blockchain-contract">-</span></p>',
            '    <p><strong>Last Connection Check:</strong> <span id="blockchain-last-check-time">-</span></p>',
            '    <button class="action-btn" id="refresh-blockchain-btn">',
            '      <i class="fas fa-sync"></i> Check Connection',
            '    </button>',
            '  </div>',
            '</div>',
            '<div class="card" style="grid-column: span 3;">',
            '  <div class="card-header">',
            '    <h3 class="card-title">Blockchain Verification Statistics</h3>',
            '  </div>',
            '  <div class="card-body">',
            '    <div class="stat-container">',
            '      <div class="stat-item">',
            '        <h4>157</h4>',
            '        <p>Blockchain Records</p>',
            '      </div>',
            '      <div class="stat-item">',
            '        <h4>98%</h4>',
            '        <p>Verification Rate</p>',
            '      </div>',
            '      <div class="stat-item">',
            '        <h4>3</h4>',
            '        <p>Pending Transactions</p>',
            '      </div>',
            '    </div>',
            '  </div>',
            '</div>'
        ].join('\n');
    },
    
    /**
     * Update blockchain status in dashboard
     * @returns {void}
     */
    updateDashboardBlockchainStatus: function() {
        if (typeof blockchainClient === 'undefined') {
            console.warn('Blockchain client not available for status check');
            return;
        }
        
        var self = this;
        blockchainClient.checkConnection()
            .then(function(status) {
                console.log('Blockchain status updated:', status);
                
                // Update header status indicator
                var headerStatus = document.getElementById('header-blockchain-status');
                if (headerStatus) {
                    if (status.connected) {
                        headerStatus.className = 'blockchain-status connected';
                        headerStatus.innerHTML = [
                            '<div class="blockchain-status-icon"></div>',
                            '<span>Blockchain Connected</span>'
                        ].join('');
                    } else {
                        headerStatus.className = 'blockchain-status disconnected';
                        headerStatus.innerHTML = [
                            '<div class="blockchain-status-icon"></div>',
                            '<span>Blockchain Disconnected</span>'
                        ].join('');
                    }
                }
                
                // Update specific blockchain status elements if they exist
                var statusElements = [
                    'blockchain-connection-status',
                    'blockchain-status-value',
                    'blockchain-detail-status'
                ];
                
                statusElements.forEach(function(id) {
                    var element = document.getElementById(id);
                    if (element) {
                        element.textContent = status.connected ? 'Connected' : 'Disconnected';
                        element.style.color = status.connected ? '#27ae60' : '#e74c3c';
                    }
                });
                
                // Update provider information
                var providerElement = document.getElementById('blockchain-provider');
                if (providerElement && status.provider) {
                    providerElement.textContent = status.provider;
                }
                
                // Update contract address
                var contractElements = [
                    'blockchain-contract-address',
                    'blockchain-contract'
                ];
                
                contractElements.forEach(function(id) {
                    var element = document.getElementById(id);
                    if (element && status.contract_address) {
                        // Format contract address for display
                        var address = status.contract_address;
                        element.textContent = address.length > 12 ? 
                            address.substring(0, 6) + '...' + address.substring(address.length - 6) : 
                            address;
                    }
                });
                
                // Update last check time
                var timeElements = [
                    'blockchain-last-check',
                    'blockchain-last-check-time'
                ];
                
                timeElements.forEach(function(id) {
                    var element = document.getElementById(id);
                    if (element) {
                        element.textContent = new Date().toLocaleTimeString();
                    }
                });
            })
            .catch(function(error) {
                console.error('Error checking blockchain status:', error);
            });
    },
    
    /**
     * Handle user logout
     * @returns {void}
     */
    handleLogout: function() {
        // Reset user state
        this.state.currentUser = null;
        this.state.isAuthenticated = false;
        
        // Hide dashboard and show role selection
        document.getElementById('dashboard-container').style.display = 'none';
        document.getElementById('role-selection').style.display = 'flex';
        
        // Reset forms
        document.querySelectorAll('input').forEach(function(input) {
            input.value = '';
        });
    }
};

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ChemTrack.init();
});