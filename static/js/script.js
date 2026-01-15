/**
 * BLOOMS BOT - Frontend JavaScript
 * Handles client-side interactions and validations
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('BLOOMS BOT initialized');
    
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        });
    }, 5000);
});

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value) {
            input.style.borderColor = 'var(--danger-color)';
            isValid = false;
        } else {
            input.style.borderColor = 'var(--border-color)';
        }
    });
    
    return isValid;
}

// Show loading state
function showLoading(buttonId, message = 'Processing...') {
    const button = document.getElementById(buttonId);
    if (button) {
        button.innerHTML = `<span>⏳ ${message}</span>`;
        button.disabled = true;
    }
}

// File size validation
function validateFileSize(input, maxSizeMB = 16) {
    if (input.files && input.files[0]) {
        const fileSize = input.files[0].size / 1024 / 1024; // in MB
        if (fileSize > maxSizeMB) {
            alert(`File size must be less than ${maxSizeMB}MB`);
            input.value = '';
            return false;
        }
    }
    return true;
}

// Confirm action
function confirmAction(message) {
    return confirm(message);
}

// Show success message
function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 500);
        }, 3000);
    }
}

// Show error message
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-error';
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 500);
        }, 5000);
    }
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Debounce function for input handlers
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export current page as JSON (for debugging)
function exportPageData() {
    const data = {
        url: window.location.href,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
    };
    
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'page_data.json';
    link.click();
}

// Print current page
function printPage() {
    window.print();
}

// Copy text to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccess('Copied to clipboard!');
        }).catch(err => {
            showError('Failed to copy');
        });
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showSuccess('Copied to clipboard!');
        } catch (err) {
            showError('Failed to copy');
        }
        document.body.removeChild(textarea);
    }
}

// Animate number counting
function animateNumber(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Animate elements on scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    elements.forEach(element => {
        if (isInViewport(element)) {
            element.classList.add('animated');
        }
    });
}

// Add scroll listener for animations
window.addEventListener('scroll', debounce(animateOnScroll, 100));

// Handle keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save (prevent default and show message)
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        showSuccess('Use the export buttons to save your paper');
    }
    
    // Escape to close modals (if any)
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => modal.style.display = 'none');
    }
});

// Performance monitoring (development only)
if (window.location.hostname === 'localhost') {
    window.addEventListener('load', function() {
        const perfData = window.performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        console.log(`Page load time: ${pageLoadTime}ms`);
    });
}

// Export utility functions for use in templates
window.bloomsBot = {
    validateForm,
    showLoading,
    validateFileSize,
    confirmAction,
    showSuccess,
    showError,
    formatNumber,
    copyToClipboard,
    printPage
};
