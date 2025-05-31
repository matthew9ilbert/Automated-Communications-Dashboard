/**
 * EVS Manager Dashboard JavaScript
 * Handles client-side functionality for the dashboard
 */

// Global configuration
const DASHBOARD_CONFIG = {
    refreshInterval: 5 * 60 * 1000, // 5 minutes
    notificationDuration: 5000, // 5 seconds
    animationDuration: 300,
    maxRecentItems: 10
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    startAutoRefresh();
    checkForNotifications();
});

/**
 * Test function to simulate different times of day
 */
function simulateTimeOfDay(testHour) {
    const now = new Date();
    const timeDecimal = testHour !== undefined ? testHour : now.getHours() + now.getMinutes() / 60;
    
    // Seattle coordinates for sun calculations (approximate)
    const latitude = 47.6062;
    const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000);
    
    // Calculate sunrise and sunset times (simplified)
    const solarNoon = 12;
    const declination = 23.45 * Math.sin((360 * (284 + dayOfYear) / 365) * Math.PI / 180);
    const hourAngle = Math.acos(-Math.tan(latitude * Math.PI / 180) * Math.tan(declination * Math.PI / 180));
    const sunrise = solarNoon - (hourAngle * 12 / Math.PI);
    const sunset = solarNoon + (hourAngle * 12 / Math.PI);
    
    const root = document.documentElement;
    
    if (timeDecimal >= sunrise && timeDecimal <= sunset) {
        // Daytime - show sun and bright background
        const sunProgress = (timeDecimal - sunrise) / (sunset - sunrise);
        const sunX = 20 + (sunProgress * 60); // Sun moves from 20% to 80% across sky
        const sunY = 10 + Math.sin(sunProgress * Math.PI) * -5; // Arc motion
        
        // Brightness varies throughout day
        let brightness = 1.4;
        let sunOpacity = 1;
        
        if (timeDecimal < sunrise + 2) {
            // Dawn/morning
            brightness = 0.9 + (timeDecimal - sunrise) * 0.25;
            sunOpacity = 0.6 + (timeDecimal - sunrise) * 0.2;
        } else if (timeDecimal > sunset - 2) {
            // Evening/dusk
            brightness = 1.4 - (timeDecimal - (sunset - 2)) * 0.5;
            sunOpacity = 1 - (timeDecimal - (sunset - 2)) * 0.4;
        }
        
        root.style.setProperty('--sun-x', sunX + '%');
        root.style.setProperty('--sun-y', sunY + '%');
        root.style.setProperty('--sun-opacity', sunOpacity);
        root.style.setProperty('--bg-brightness', brightness);
        root.style.setProperty('--bg-opacity', '0.8');
        root.style.setProperty('--bg-hue', '0deg');
        
        console.log(`Daytime mode: ${timeDecimal.toFixed(1)}h, Sun at ${sunX.toFixed(1)}%, ${sunY.toFixed(1)}%, Brightness: ${brightness.toFixed(1)}`);
    } else {
        // Nighttime - hide sun, darker background
        root.style.setProperty('--sun-opacity', '0');
        root.style.setProperty('--bg-brightness', '0.6');
        root.style.setProperty('--bg-opacity', '0.6');
        root.style.setProperty('--bg-hue', '15deg'); // Slight warm tint for night
        
        console.log(`Night mode: ${timeDecimal.toFixed(1)}h, No sun, Dark background`);
    }
}

/**
 * Dynamic background controller based on time of day
 */
function updateDynamicBackground() {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const timeDecimal = hour + minute / 60;
    
    // Seattle coordinates for sun calculations (approximate)
    const latitude = 47.6062;
    const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000);
    
    // Calculate sunrise and sunset times (simplified)
    const solarNoon = 12;
    const declination = 23.45 * Math.sin((360 * (284 + dayOfYear) / 365) * Math.PI / 180);
    const hourAngle = Math.acos(-Math.tan(latitude * Math.PI / 180) * Math.tan(declination * Math.PI / 180));
    const sunrise = solarNoon - (hourAngle * 12 / Math.PI);
    const sunset = solarNoon + (hourAngle * 12 / Math.PI);
    
    const root = document.documentElement;
    
    if (timeDecimal >= sunrise && timeDecimal <= sunset) {
        // Daytime - show sun and bright background
        const sunProgress = (timeDecimal - sunrise) / (sunset - sunrise);
        const sunX = 20 + (sunProgress * 60); // Sun moves from 20% to 80% across sky
        const sunY = 20 + Math.sin(sunProgress * Math.PI) * -10; // Arc motion
        
        // Brightness varies throughout day
        let brightness = 1.2;
        if (timeDecimal < sunrise + 1) {
            brightness = 0.8 + (timeDecimal - sunrise) * 0.4; // Dawn
        } else if (timeDecimal > sunset - 1) {
            brightness = 1.2 - (timeDecimal - (sunset - 1)) * 0.4; // Dusk
        }
        
        root.style.setProperty('--sun-x', sunX + '%');
        root.style.setProperty('--sun-y', sunY + '%');
        root.style.setProperty('--sun-opacity', '1');
        root.style.setProperty('--bg-brightness', brightness);
        root.style.setProperty('--bg-opacity', '0.7');
        root.style.setProperty('--bg-hue', '0deg');
    } else {
        // Nighttime - hide sun, darker background
        root.style.setProperty('--sun-opacity', '0');
        root.style.setProperty('--bg-brightness', '0.6');
        root.style.setProperty('--bg-opacity', '0.6');
        root.style.setProperty('--bg-hue', '20deg'); // Slight warm tint for night
    }
}

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Set up form validation
    setupFormValidation();
    
    // Initialize data tables if present
    initializeDataTables();
    
    // Set up real-time updates
    setupWebSocket();
    
    // Initialize dynamic background
    updateDynamicBackground();
    
    // Update background every 5 minutes
    setInterval(updateDynamicBackground, 300000);
    
    // Add test controls for time simulation (temporary)
    if (window.location.search.includes('test=morning')) {
        simulateTimeOfDay(7); // 7 AM morning
    } else if (window.location.search.includes('test=noon')) {
        simulateTimeOfDay(12); // Noon
    } else if (window.location.search.includes('test=evening')) {
        simulateTimeOfDay(18); // 6 PM evening
    } else if (window.location.search.includes('test=night')) {
        simulateTimeOfDay(23); // 11 PM night
    }
    
    console.log('Dashboard initialized successfully');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Handle form submissions
    document.addEventListener('submit', handleFormSubmission);
    
    // Handle dropdown changes
    document.addEventListener('change', handleDropdownChanges);
    
    // Handle button clicks
    document.addEventListener('click', handleButtonClicks);
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Handle window resize
    window.addEventListener('resize', handleWindowResize);
    
    // Handle visibility change for auto-refresh
    document.addEventListener('visibilitychange', handleVisibilityChange);
}

/**
 * Handle form submissions
 */
function handleFormSubmission(event) {
    const form = event.target.closest('form');
    if (!form) return;
    
    // Add loading state
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
        submitButton.disabled = true;
        
        // Restore button state after a delay (in case of redirect)
        setTimeout(() => {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }, 3000);
    }
}

/**
 * Handle dropdown changes for real-time updates
 */
function handleDropdownChanges(event) {
    const element = event.target;
    
    // Handle status changes
    if (element.name === 'status' && element.closest('form')) {
        const form = element.closest('form');
        if (form.querySelector('input[name="task_id"]')) {
            // Auto-submit task status changes
            setTimeout(() => form.submit(), 100);
        }
    }
    
    // Handle filter changes
    if (element.id && element.id.includes('Filter')) {
        applyFilters();
    }
}

/**
 * Handle button clicks
 */
function handleButtonClicks(event) {
    const button = event.target.closest('button');
    if (!button) return;
    
    // Handle quick action buttons
    if (button.dataset.action) {
        event.preventDefault();
        handleQuickAction(button.dataset.action, button.dataset);
    }
    
    // Handle confirmation buttons
    if (button.dataset.confirm) {
        event.preventDefault();
        showConfirmDialog(button.dataset.confirm, () => {
            // Execute the original action
            if (button.onclick) {
                button.onclick();
            } else if (button.href) {
                window.location.href = button.href;
            }
        });
    }
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(event) {
    // Only handle shortcuts when not in input fields
    if (event.target.tagName.toLowerCase() === 'input' || 
        event.target.tagName.toLowerCase() === 'textarea') {
        return;
    }
    
    // Ctrl/Cmd + key combinations
    if (event.ctrlKey || event.metaKey) {
        switch(event.key.toLowerCase()) {
            case 'n':
                event.preventDefault();
                openCreateModal();
                break;
            case 'r':
                event.preventDefault();
                refreshDashboard();
                break;
            case 'f':
                event.preventDefault();
                focusSearchField();
                break;
        }
    }
    
    // Escape key
    if (event.key === 'Escape') {
        closeAllModals();
    }
}

/**
 * Handle window resize
 */
function handleWindowResize() {
    // Adjust table responsiveness
    adjustTableLayout();
    
    // Recalculate chart sizes if present
    if (window.Chart && Chart.instances && Chart.instances.length > 0) {
        Object.values(Chart.instances).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }
}

/**
 * Handle visibility change for auto-refresh
 */
function handleVisibilityChange() {
    if (document.hidden) {
        // Page is hidden, pause auto-refresh
        clearInterval(window.dashboardRefreshInterval);
    } else {
        // Page is visible, resume auto-refresh
        startAutoRefresh();
        // Refresh immediately when returning to page
        refreshDashboard();
    }
}

/**
 * Start auto-refresh functionality
 */
function startAutoRefresh() {
    // Clear existing interval
    if (window.dashboardRefreshInterval) {
        clearInterval(window.dashboardRefreshInterval);
    }
    
    // Set up new interval
    window.dashboardRefreshInterval = setInterval(() => {
        refreshDashboard();
    }, DASHBOARD_CONFIG.refreshInterval);
    
    console.log('Auto-refresh started');
}

/**
 * Refresh dashboard data
 */
function refreshDashboard() {
    // Update timestamp
    updateLastRefreshTime();
    
    // Refresh statistics
    refreshStatistics();
    
    // Refresh recent items
    refreshRecentItems();
    
    // Check for new notifications
    checkForNotifications();
    
    console.log('Dashboard refreshed at', new Date().toLocaleTimeString());
}

/**
 * Update last refresh time display
 */
function updateLastRefreshTime() {
    const timeElements = document.querySelectorAll('#lastUpdated, .last-updated');
    const now = new Date();
    const timeString = now.toLocaleString();
    
    timeElements.forEach(element => {
        element.textContent = timeString;
    });
}

/**
 * Refresh statistics counters
 */
function refreshStatistics() {
    // In a full implementation, this would make AJAX calls to get updated stats
    // For now, we'll simulate random updates
    const statElements = document.querySelectorAll('.card-body h2');
    
    statElements.forEach(element => {
        const currentValue = parseInt(element.textContent) || 0;
        // Simulate small random changes
        const change = Math.floor(Math.random() * 3) - 1; // -1, 0, or 1
        const newValue = Math.max(0, currentValue + change);
        
        if (newValue !== currentValue) {
            animateCounter(element, currentValue, newValue);
        }
    });
}

/**
 * Animate counter changes
 */
function animateCounter(element, from, to) {
    const duration = 1000;
    const start = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.round(from + (to - from) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

/**
 * Refresh recent items lists
 */
function refreshRecentItems() {
    // In a full implementation, this would fetch updated data
    // For now, we'll just add visual feedback
    const recentLists = document.querySelectorAll('.recent-items, .pending-items');
    
    recentLists.forEach(list => {
        list.classList.add('refreshing');
        setTimeout(() => {
            list.classList.remove('refreshing');
        }, 500);
    });
}

/**
 * Check for new notifications
 */
function checkForNotifications() {
    // In a full implementation, this would check for new alerts
    // Only update badge if there are actual unread notifications
    const unreadMessages = document.querySelectorAll('.message-item.unread, .task-item.urgent').length;
    
    updateNotificationBadge(unreadMessages);
}

/**
 * Update notification badge
 */
function updateNotificationBadge(count) {
    let badge = document.querySelector('.notification-badge');
    
    if (!badge && count > 0) {
        badge = document.createElement('span');
        badge.className = 'notification-badge';
        const navIcon = document.querySelector('.navbar-brand i');
        if (navIcon) {
            navIcon.parentElement.style.position = 'relative';
            navIcon.parentElement.appendChild(badge);
        }
    }
    
    if (badge) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form[data-validate="true"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
}

/**
 * Initialize data tables
 */
function initializeDataTables() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        // Add sorting functionality
        setupTableSorting(table);
        
        // Add search functionality
        setupTableSearch(table);
        
        // Add row selection
        setupRowSelection(table);
    });
}

/**
 * Setup table sorting
 */
function setupTableSorting(table) {
    const headers = table.querySelectorAll('th[data-sortable="true"]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            sortTable(table, header);
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, header) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentElement.children).indexOf(header);
    const isAscending = header.dataset.sortDir !== 'asc';
    
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        if (isAscending) {
            return aValue.localeCompare(bValue, undefined, {numeric: true});
        } else {
            return bValue.localeCompare(aValue, undefined, {numeric: true});
        }
    });
    
    // Update DOM
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort direction
    header.dataset.sortDir = isAscending ? 'asc' : 'desc';
    
    // Update sort indicators
    const allHeaders = table.querySelectorAll('th[data-sortable="true"]');
    allHeaders.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
}

/**
 * Setup table search
 */
function setupTableSearch(table) {
    const searchInput = table.parentElement.querySelector('.table-search');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        filterTable(table, this.value);
    });
}

/**
 * Filter table rows
 */
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

/**
 * Setup row selection
 */
function setupRowSelection(table) {
    const selectAllCheckbox = table.querySelector('th input[type="checkbox"]');
    const rowCheckboxes = table.querySelectorAll('tbody input[type="checkbox"]');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButtons();
        });
    }
    
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkActionButtons();
            
            // Update select all checkbox state
            if (selectAllCheckbox) {
                const checkedCount = table.querySelectorAll('tbody input[type="checkbox"]:checked').length;
                selectAllCheckbox.checked = checkedCount === rowCheckboxes.length;
                selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < rowCheckboxes.length;
            }
        });
    });
}

/**
 * Update bulk action buttons
 */
function updateBulkActionButtons() {
    const selectedCount = document.querySelectorAll('tbody input[type="checkbox"]:checked').length;
    const bulkButtons = document.querySelectorAll('.bulk-action-btn');
    
    bulkButtons.forEach(button => {
        button.disabled = selectedCount === 0;
        const countSpan = button.querySelector('.selection-count');
        if (countSpan) {
            countSpan.textContent = selectedCount;
        }
    });
}

/**
 * Setup WebSocket for real-time updates
 */
function setupWebSocket() {
    // In a full implementation, this would establish WebSocket connection
    // For now, we'll simulate with periodic checks
    console.log('WebSocket simulation started');
}

/**
 * Handle quick actions
 */
function handleQuickAction(action, data) {
    switch(action) {
        case 'mark-processed':
            markAsProcessed(data.id);
            break;
        case 'assign-staff':
            openStaffAssignmentModal(data.id);
            break;
        case 'create-task':
            openTaskCreationModal(data);
            break;
        case 'add-to-calendar':
            openCalendarModal(data);
            break;
        default:
            console.warn('Unknown quick action:', action);
    }
}

/**
 * Show confirmation dialog
 */
function showConfirmDialog(message, onConfirm, onCancel = null) {
    if (confirm(message)) {
        onConfirm();
    } else if (onCancel) {
        onCancel();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', duration = DASHBOARD_CONFIG.notificationDuration) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    
    // Create message text node to prevent XSS
    const messageText = document.createTextNode(message);
    notification.appendChild(messageText);
    
    // Create close button
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close';
    closeButton.setAttribute('data-bs-dismiss', 'alert');
    notification.appendChild(closeButton);
    
    // Add to page
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    // Auto-dismiss
    setTimeout(() => {
        notification.remove();
    }, duration);
}

/**
 * Open create modal
 */
function openCreateModal() {
    const createButtons = document.querySelectorAll('[data-bs-toggle="modal"][data-bs-target*="create"]');
    if (createButtons.length > 0) {
        createButtons[0].click();
    }
}

/**
 * Focus search field
 */
function focusSearchField() {
    const searchFields = document.querySelectorAll('input[type="search"], .table-search, #search');
    if (searchFields.length > 0) {
        searchFields[0].focus();
    }
}

/**
 * Close all modals
 */
function closeAllModals() {
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
}

/**
 * Adjust table layout for mobile
 */
function adjustTableLayout() {
    const tables = document.querySelectorAll('.table-responsive');
    const isMobile = window.innerWidth < 768;
    
    tables.forEach(table => {
        if (isMobile) {
            table.classList.add('table-mobile');
        } else {
            table.classList.remove('table-mobile');
        }
    });
}

/**
 * Apply filters
 */
function applyFilters() {
    // Get all filter elements
    const filters = document.querySelectorAll('[id$="Filter"]');
    const filterValues = {};
    
    filters.forEach(filter => {
        filterValues[filter.id] = filter.value;
    });
    
    // Apply filters to relevant elements
    const filterable = document.querySelectorAll('[data-filterable="true"]');
    
    filterable.forEach(element => {
        let show = true;
        
        Object.entries(filterValues).forEach(([filterId, value]) => {
            if (value && element.dataset[filterId.replace('Filter', '')]) {
                if (element.dataset[filterId.replace('Filter', '')] !== value) {
                    show = false;
                }
            }
        });
        
        element.style.display = show ? '' : 'none';
    });
}

/**
 * Mark item as processed
 */
function markAsProcessed(id) {
    // In a full implementation, this would make an API call
    showNotification(`Item ${id} marked as processed`, 'success');
}

/**
 * Open staff assignment modal
 */
function openStaffAssignmentModal(id) {
    const modal = document.querySelector('#assignmentModal');
    if (modal) {
        new bootstrap.Modal(modal).show();
    }
}

/**
 * Open task creation modal
 */
function openTaskCreationModal(data) {
    const modal = document.querySelector('#createTaskModal');
    if (modal) {
        // Pre-fill form if data provided
        if (data.title) {
            const titleInput = modal.querySelector('#title');
            if (titleInput) titleInput.value = data.title;
        }
        
        new bootstrap.Modal(modal).show();
    }
}

/**
 * Open calendar modal
 */
function openCalendarModal(data) {
    const modal = document.querySelector('#createEventModal');
    if (modal) {
        new bootstrap.Modal(modal).show();
    }
}

/**
 * Initialize charts if Chart.js is available
 */
function initializeCharts() {
    if (typeof Chart === 'undefined') return;
    
    // Example priority distribution chart
    const priorityChart = document.getElementById('priorityChart');
    if (priorityChart) {
        new Chart(priorityChart, {
            type: 'doughnut',
            data: {
                labels: ['High', 'Medium', 'Low'],
                datasets: [{
                    data: [12, 19, 8],
                    backgroundColor: [
                        'var(--bs-danger)',
                        'var(--bs-warning)',
                        'var(--bs-secondary)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

// Export functions for global use
window.EVSManager = {
    refreshDashboard,
    showNotification,
    markAsProcessed,
    openStaffAssignmentModal,
    openTaskCreationModal,
    openCalendarModal,
    showConfirmDialog
};

// Initialize charts when Chart.js loads
if (typeof Chart !== 'undefined') {
    initializeCharts();
} else {
    // Wait for Chart.js to load
    document.addEventListener('chartjs-loaded', initializeCharts);
}

console.log('EVS Manager Dashboard JavaScript loaded successfully');
