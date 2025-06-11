/**
 * Authentication Module
 * Handles user authentication, session management, and role-based access control
 */

import { showNotification, showModal } from './ui.js';

// User roles
export const ROLES = {
    ADMIN: 'admin',
    MANUFACTURER: 'manufacturer',
    DISTRIBUTOR: 'distributor',
    RETAILER: 'retailer',
    CUSTOMER: 'customer'
};

// Current user session
let currentUser = null;

/**
 * Check if user is authenticated
 * @returns {boolean} True if user is authenticated
 */
export function isAuthenticated() {
    return currentUser !== null;
}

/**
 * Get current user
 * @returns {Object|null} Current user object or null if not authenticated
 */
export function getCurrentUser() {
    return currentUser;
}

/**
 * Check if current user has required role
 * @param {string|Array} requiredRole - Required role or array of roles
 * @returns {boolean} True if user has the required role
 */
export function hasRole(requiredRole) {
    if (!currentUser || !currentUser.role) return false;
    
    if (Array.isArray(requiredRole)) {
        return requiredRole.includes(currentUser.role);
    }
    
    return currentUser.role === requiredRole;
}

/**
 * Login user
 * @param {string} username - Username or email
 * @param {string} password - Password
 * @returns {Promise<Object>} Login result
 */
export async function login(username, password) {
    try {
        // Show loading state
        const loginButton = document.querySelector('#login-form button[type="submit"]');
        const originalButtonText = loginButton ? loginButton.innerHTML : '';
        
        if (loginButton) {
            loginButton.disabled = true;
            loginButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';
        }
        
        // In a real app, this would be an API call to your backend
        // For demo purposes, we'll simulate a successful login
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Login failed');
        }
        
        const userData = await response.json();
        
        // Store user data in session
        currentUser = {
            id: userData.id,
            username: userData.username,
            email: userData.email,
            role: userData.role,
            token: userData.token
        };
        
        // Store in session storage
        sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        // Show success message
        showNotification('Login successful!', 'success');
        
        // Return user data
        return { success: true, user: currentUser };
    } catch (error) {
        console.error('Login error:', error);
        showNotification(error.message || 'Login failed. Please try again.', 'error');
        return { success: false, error: error.message };
    } finally {
        // Reset button state
        const loginButton = document.querySelector('#login-form button[type="submit"]');
        if (loginButton) {
            loginButton.disabled = false;
            loginButton.innerHTML = originalButtonText || 'Sign In';
        }
    }
}

/**
 * Logout user
 */
export function logout() {
    // Clear session
    currentUser = null;
    sessionStorage.removeItem('currentUser');
    
    // Show the auth container and hide dashboard
    const authContainer = document.getElementById('auth-container');
    const dashboardContainer = document.getElementById('dashboard-container');
    const roleSelection = document.getElementById('role-selection');
    
    if (authContainer) authContainer.style.display = 'flex';
    if (dashboardContainer) dashboardContainer.style.display = 'none';
    if (roleSelection) roleSelection.style.display = 'none';
    
    // Switch to login tab
    const loginTab = document.querySelector('.auth-tab[data-tab="login"]');
    if (loginTab) loginTab.click();
}

/**
 * Initialize authentication
 * Checks for existing session on page load
 */
export function initAuth() {
    // Check for existing session
    const storedUser = sessionStorage.getItem('currentUser');
    if (storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
            console.log('User session restored:', currentUser);
        } catch (error) {
            console.error('Error parsing stored user:', error);
            sessionStorage.removeItem('currentUser');
        }
    }
    
    // Add event listener for logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
    
    // Protect routes based on authentication
    protectRoutes();
}

/**
 * Protect routes based on authentication and roles
 */
function protectRoutes() {
    const publicPaths = ['login', 'register', 'forgot-password'];
    const currentPath = window.location.hash.replace('#', '') || 'dashboard';
    
    // If user is not authenticated and trying to access protected route
    if (!isAuthenticated() && !publicPaths.includes(currentPath)) {
        // Store the intended URL to redirect after login
        sessionStorage.setItem('redirectAfterLogin', currentPath);
        
        // Show auth container and hide dashboard
        const authContainer = document.getElementById('auth-container');
        const dashboardContainer = document.getElementById('dashboard-container');
        const roleSelection = document.getElementById('role-selection');
        
        if (authContainer) authContainer.style.display = 'flex';
        if (dashboardContainer) dashboardContainer.style.display = 'none';
        if (roleSelection) roleSelection.style.display = 'none';
        
        // Switch to login tab
        const loginTab = document.querySelector('.auth-tab[data-tab="login"]');
        if (loginTab) loginTab.click();
        return;
    }
    
    // If user is authenticated and trying to access auth pages
    if (isAuthenticated() && publicPaths.includes(currentPath)) {
        // Redirect to dashboard or home
        const redirectTo = sessionStorage.getItem('redirectAfterLogin') || 'dashboard';
        sessionStorage.removeItem('redirectAfterLogin');
        
        // Update URL without reloading the page
        window.location.hash = redirectTo;
        
        // Show dashboard and hide auth container
        const authContainer = document.getElementById('auth-container');
        const dashboardContainer = document.getElementById('dashboard-container');
        const roleSelection = document.getElementById('role-selection');
        
        if (authContainer) authContainer.style.display = 'none';
        if (dashboardContainer) dashboardContainer.style.display = 'block';
        if (roleSelection) roleSelection.style.display = 'none';
    }
}

/**
 * Get authentication headers for API requests
 * @returns {Object} Headers with authorization token
 */
export function getAuthHeaders() {
    if (!isAuthenticated()) return {};
    
    return {
        'Authorization': `Bearer ${currentUser.token}`,
        'Content-Type': 'application/json'
    };
}

/**
 * Check if user can access a specific route
 * @param {string} route - The route to check
 * @returns {boolean} True if user can access the route
 */
export function canAccessRoute(route) {
    if (!isAuthenticated()) return false;
    
    // Define route permissions
    const routePermissions = {
        '/admin': [ROLES.ADMIN],
        '/manufacturer': [ROLES.ADMIN, ROLES.MANUFACTURER],
        '/distributor': [ROLES.ADMIN, ROLES.DISTRIBUTOR],
        '/retailer': [ROLES.ADMIN, ROLES.RETAILER],
        '/customer': [ROLES.ADMIN, ROLES.CUSTOMER]
    };
    
    // Check if route has specific permissions
    for (const [protectedRoute, allowedRoles] of Object.entries(routePermissions)) {
        if (route.startsWith(protectedRoute)) {
            return hasRole(allowedRoles);
        }
    }
    
    // Default to allowing access if no specific permissions are set
    return true;
}