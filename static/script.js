// Modern Email Tool JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize modern animations and interactions
    initializeAnimations();
    initializeEmailValidation();
    initializeProgressBars();
    initializeTooltips();
});

// Animation Initialization
function initializeAnimations() {
    // Add fade-in animation to elements
    const cards = document.querySelectorAll('.modern-card, .feature-card, .stats-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });

    // Smooth scroll for navigation
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Email Validation Enhancement
function initializeEmailValidation() {
    // Real-time email validation feedback
    const emailInputs = document.querySelectorAll('input[type="email"], input[placeholder*="email"]');
    
    emailInputs.forEach(input => {
        input.addEventListener('input', function() {
            const email = this.value;
            const isValid = validateEmailFormat(email);
            
            // Visual feedback
            if (email.length > 0) {
                if (isValid) {
                    this.style.borderColor = '#48bb78';
                    this.style.boxShadow = '0 0 0 3px rgba(72, 187, 120, 0.1)';
                } else {
                    this.style.borderColor = '#f56565';
                    this.style.boxShadow = '0 0 0 3px rgba(245, 101, 101, 0.1)';
                }
            } else {
                this.style.borderColor = 'rgba(102, 126, 234, 0.2)';
                this.style.boxShadow = 'none';
            }
        });
    });
}

// Email Format Validation
function validateEmailFormat(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Progress Bar Animation
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.modern-progress-bar');
    
    const animateProgress = (bar, targetWidth) => {
        let currentWidth = 0;
        const increment = targetWidth / 50;
        
        const timer = setInterval(() => {
            currentWidth += increment;
            if (currentWidth >= targetWidth) {
                currentWidth = targetWidth;
                clearInterval(timer);
            }
            bar.style.width = currentWidth + '%';
        }, 20);
    };
    
    // Observe progress bars and animate when visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target.querySelector('.modern-progress-bar');
                const targetWidth = parseInt(bar.dataset.width) || 0;
                animateProgress(bar, targetWidth);
            }
        });
    });
    
    document.querySelectorAll('.modern-progress').forEach(progress => {
        observer.observe(progress);
    });
}

// Tooltip System
function initializeTooltips() {
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(45, 55, 72, 0.9);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        pointer-events: none;
        z-index: 1000;
        opacity: 0;
        transition: opacity 0.3s ease;
        backdrop-filter: blur(10px);
    `;
    document.body.appendChild(tooltip);
    
    // Add tooltips to elements with title attribute
    document.querySelectorAll('[title]').forEach(element => {
        const title = element.getAttribute('title');
        element.removeAttribute('title');
        
        element.addEventListener('mouseenter', function(e) {
            tooltip.textContent = title;
            tooltip.style.opacity = '1';
        });
        
        element.addEventListener('mousemove', function(e) {
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY - 30 + 'px';
        });
        
        element.addEventListener('mouseleave', function() {
            tooltip.style.opacity = '0';
        });
    });
}

// Email Counter Animation
function animateCounter(element, targetCount) {
    let currentCount = 0;
    const increment = Math.ceil(targetCount / 50);
    
    const timer = setInterval(() => {
        currentCount += increment;
        if (currentCount >= targetCount) {
            currentCount = targetCount;
            clearInterval(timer);
        }
        element.textContent = currentCount.toLocaleString();
    }, 30);
}

// Copy to Clipboard Functionality
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Berhasil disalin ke clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Berhasil disalin ke clipboard!', 'success');
    });
}

// Custom Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `custom-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
        </div>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        transform: translateX(400px);
        transition: transform 0.3s ease;
        border-left: 4px solid ${getNotificationColor(type)};
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

function getNotificationIcon(type) {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    return icons[type] || icons.info;
}

function getNotificationColor(type) {
    const colors = {
        success: '#48bb78',
        error: '#f56565',
        warning: '#ed8936',
        info: '#667eea'
    };
    return colors[type] || colors.info;
}

// Form Enhancement
function enhanceFormSubmission() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="loading-spinner"></span> Memproses...';
                submitButton.disabled = true;
            }
        });
    });
}

// Email List Enhancement
function enhanceEmailList() {
    const emailItems = document.querySelectorAll('.email-item');
    emailItems.forEach(item => {
        item.addEventListener('click', function() {
            const email = this.textContent.trim();
            copyToClipboard(email);
        });
    });
}

// Dark Mode Toggle (for future enhancement)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Initialize dark mode from localStorage
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// Export functions for use in Streamlit
window.EmailToolJS = {
    copyToClipboard,
    showNotification,
    animateCounter,
    validateEmailFormat
};