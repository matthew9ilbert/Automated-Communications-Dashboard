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

    // Check for time-based background images
    let backgroundImage = "url('/static/IMG_6138.jpeg')"; // Default fallback
    if (timeDecimal >= 2 && timeDecimal < 6) {
        backgroundImage = "url('/static/IMG_6161_early_morning.jpeg')"; // Early morning image (2-6 AM)
    } else if (timeDecimal >= 6 && timeDecimal < 10) {
        backgroundImage = "url('/static/IMG_6143.jpeg')"; // Morning image (6-10 AM)
    } else if (timeDecimal >= 10 && timeDecimal < 14) {
        backgroundImage = "url('/static/IMG_6237_midday.jpeg')"; // Midday image (10 AM-2 PM)
    } else if (timeDecimal >= 14 && timeDecimal < 18) {
        backgroundImage = "url('/static/IMG_6143_afternoon_correct.jpeg')"; // Afternoon image (2-6 PM)
    } else if (timeDecimal >= 18 && timeDecimal < 22) {
        backgroundImage = "url('/static/IMG_6161_evening.jpeg')"; // Evening image (6-10 PM)
    } else if (timeDecimal >= 22 || timeDecimal < 2) {
        backgroundImage = "url('/static/IMG_6161_late_night.jpeg')"; // Late night image (10 PM-2 AM)
    }
    root.style.setProperty('--bg-image', backgroundImage);

    if (timeDecimal >= sunrise && timeDecimal <= sunset) {
        // Daytime - show sun and bright background
        const sunProgress = (timeDecimal - sunrise) / (sunset - sunrise);
        const sunX = 20 + (sunProgress * 60); // Sun moves from 20% to 80% across sky
        const sunY = 10 + Math.sin(sunProgress * Math.PI) * -5; // Arc motion

        // Brightness varies throughout day
        let brightness = 1.8;
        let sunOpacity = 1;
        let bgOpacity = 0.9;

        if (timeDecimal < sunrise + 2) {
            // Dawn/morning
            brightness = 1.0 + (timeDecimal - sunrise) * 0.4;
            sunOpacity = 0.7 + (timeDecimal - sunrise) * 0.15;
            bgOpacity = 0.8;
        } else if (timeDecimal > sunset - 2) {
            // Evening/dusk
            brightness = 1.8 - (timeDecimal - (sunset - 2)) * 0.6;
            sunOpacity = 1 - (timeDecimal - (sunset - 2)) * 0.5;
            bgOpacity = 0.7;
        }

        root.style.setProperty('--sun-x', sunX + '%');
        root.style.setProperty('--sun-y', sunY + '%');
        root.style.setProperty('--sun-opacity', sunOpacity);
        root.style.setProperty('--bg-brightness', brightness);
        root.style.setProperty('--bg-opacity', bgOpacity);
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

    // Check for time-based background images
    let backgroundImage = "url('/static/IMG_6138.jpeg')"; // Default fallback
    if (timeDecimal >= 2 && timeDecimal < 6) {
        backgroundImage = "url('/static/IMG_6161_early_morning.jpeg')"; // Early morning image (2-6 AM)
    } else if (timeDecimal >= 6 && timeDecimal < 10) {
        backgroundImage = "url('/static/IMG_6143.jpeg')"; // Morning image (6-10 AM)
    } else if (timeDecimal >= 10 && timeDecimal < 14) {
        backgroundImage = "url('/static/IMG_6237_midday.jpeg')"; // Midday image (10 AM-2 PM)
    } else if (timeDecimal >= 14 && timeDecimal < 18) {
        backgroundImage = "url('/static/IMG_6143_afternoon_correct.jpeg')"; // Afternoon image (2-6 PM)
    } else if (timeDecimal >= 18 && timeDecimal < 22) {
        backgroundImage = "url('/static/IMG_6161_evening.jpeg')"; // Evening image (6-10 PM)
    } else if (timeDecimal >= 22 || timeDecimal < 2) {
        backgroundImage = "url('/static/IMG_6161_late_night.jpeg')"; // Late night image (10 PM-2 AM)
    }
    root.style.setProperty('--bg-image', backgroundImage);

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
    } else if (window.location.search.includes('test=midday')) {
        simulateTimeOfDay(12); // 12 PM midday
    } else if (window.location.search.includes('test=noon')) {
        simulateTimeOfDay(12); // Noon
    } else if (window.location.search.includes('test=afternoon')) {
        simulateTimeOfDay(15); // 3 PM afternoon
    } else if (window.location.search.includes('test=evening')) {
        simulateTimeOfDay(18); // 6 PM evening
    } else if (window.location.search.includes('test=night')) {
        simulateTimeOfDay(23); // 11 PM night
    } else if (window.location.search.includes('test=early')) {
        simulateTimeOfDay(4); // 4 AM early morning
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
async function refreshDashboard() {
    try {
        // Update timestamp
        updateLastRefreshTime();

        // Refresh statistics with real API call
        await refreshStatistics();

        // Refresh recent items
        refreshRecentItems();

        // Check for new notifications
        checkForNotifications();

        console.log('Dashboard refreshed at', new Date().toLocaleTimeString());
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        showNotification('Failed to refresh dashboard data', 'error');
    }
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
 * Refresh statistics counters with real API data
 */
async function refreshStatistics() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to get stats');
        }
        
        const stats = data.stats;
        
        // Update each statistic with animation
        const statMappings = {
            'total_tasks': '.card-body h2:eq(0)',
            'pending_tasks': '.card-body h2:eq(1)', 
            'high_priority_messages': '.card-body h2:eq(2)',
            'upcoming_events': '.card-body h2:eq(3)'
        };
        
        // Update statistics with better selectors
        updateStatistic('total_tasks', stats.total_tasks);
        updateStatistic('pending_tasks', stats.pending_tasks);
        updateStatistic('high_priority_messages', stats.high_priority_messages);
        updateStatistic('upcoming_events', stats.upcoming_events);
        
    } catch (error) {
        console.error('Error refreshing statistics:', error);
        // Fall back to current behavior if API fails
        fallbackStatisticsRefresh();
    }
}

/**
 * Update a specific statistic with animation
 */
function updateStatistic(statName, newValue) {
    const statCards = document.querySelectorAll('.card-body');
    let targetElement = null;
    
    // Find the correct card based on title text
    statCards.forEach(card => {
        const title = card.querySelector('.card-title');
        if (title) {
            const titleText = title.textContent.toLowerCase();
            if ((statName === 'total_tasks' && titleText.includes('total tasks')) ||
                (statName === 'pending_tasks' && titleText.includes('pending tasks')) ||
                (statName === 'high_priority_messages' && titleText.includes('high priority')) ||
                (statName === 'upcoming_events' && titleText.includes('upcoming events'))) {
                targetElement = card.querySelector('h2');
            }
        }
    });
    
    if (targetElement) {
        const currentValue = parseInt(targetElement.textContent) || 0;
        if (newValue !== currentValue) {
            animateCounter(targetElement, currentValue, newValue);
        }
    }
}

/**
 * Fallback statistics refresh (original behavior)
 */
function fallbackStatisticsRefresh() {
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
 * Setup form validation with enhanced feedback
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        // Add real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                // Clear validation state on input
                this.classList.remove('is-invalid', 'is-valid');
                const feedback = this.parentElement.querySelector('.invalid-feedback');
                if (feedback) {
                    feedback.style.display = 'none';
                }
            });
        });

        form.addEventListener('submit', function(event) {
            const isValid = validateForm(form);
            
            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();

                // Focus first invalid field
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                showNotification('Please correct the errors in the form', 'error');
            } else {
                // Add loading state to submit button
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
                    submitBtn.disabled = true;
                    
                    // Restore after delay if form doesn't redirect
                    setTimeout(() => {
                        if (submitBtn) {
                            submitBtn.innerHTML = originalText;
                            submitBtn.disabled = false;
                        }
                    }, 5000);
                }
            }

            form.classList.add('was-validated');
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let message = '';
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required';
    }
    
    // Email validation
    else if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid email address';
        }
    }
    
    // Phone validation
    else if (field.type === 'tel' && value) {
        const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid phone number';
        }
    }
    
    // Text length validation
    else if (field.type === 'text' && value) {
        if (field.minLength && value.length < field.minLength) {
            isValid = false;
            message = `Minimum ${field.minLength} characters required`;
        }
        else if (field.maxLength && value.length > field.maxLength) {
            isValid = false;
            message = `Maximum ${field.maxLength} characters allowed`;
        }
    }
    
    // Update field validation state
    updateFieldValidation(field, isValid, message);
    
    return isValid;
}

/**
 * Validate entire form
 */
function validateForm(form) {
    const fields = form.querySelectorAll('input, select, textarea');
    let isFormValid = true;
    
    fields.forEach(field => {
        const isFieldValid = validateField(field);
        if (!isFieldValid) {
            isFormValid = false;
        }
    });
    
    return isFormValid;
}

/**
 * Update field validation visual state
 */
function updateFieldValidation(field, isValid, message) {
    field.classList.remove('is-invalid', 'is-valid');
    
    // Remove existing feedback
    let feedback = field.parentElement.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
    
    if (!isValid) {
        field.classList.add('is-invalid');
        
        // Add error message
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        feedback.style.display = 'block';
        field.parentElement.appendChild(feedback);
    } else if (field.value.trim()) {
        field.classList.add('is-valid');
    }
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