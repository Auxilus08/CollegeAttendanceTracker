// Global utility functions and event handlers

document.addEventListener('DOMContentLoaded', function() {
  // Enable tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
  
  // Enable popovers
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
  
  // Handle confirmation dialogs
  const confirmButtons = document.querySelectorAll('[data-confirm]');
  confirmButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      if (!confirm(this.dataset.confirm)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });
  
  // Handle auto-dismissing alerts
  const autoAlerts = document.querySelectorAll('.alert-dismissible.auto-dismiss');
  autoAlerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
  
  // Select all checkboxes functionality
  const selectAllCheckboxes = document.querySelectorAll('[data-select-all]');
  selectAllCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      const targetSelector = this.dataset.selectAll;
      const targetCheckboxes = document.querySelectorAll(targetSelector);
      
      targetCheckboxes.forEach(targetBox => {
        targetBox.checked = this.checked;
      });
    });
  });
  
  // Make elements with data-href attribute clickable
  const clickableElements = document.querySelectorAll('[data-href]');
  clickableElements.forEach(element => {
    element.style.cursor = 'pointer';
    element.addEventListener('click', function() {
      window.location.href = this.dataset.href;
    });
  });
});

// Handle form elements that should trigger form submission when changed
document.addEventListener('change', function(e) {
  if (e.target.matches('[data-submit-on-change]')) {
    e.target.closest('form').submit();
  }
});

// Helper function to format dates
function formatDate(dateString) {
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString(undefined, options);
}

// Helper function to format times
function formatTime(timeString) {
  const options = { hour: '2-digit', minute: '2-digit' };
  return new Date(`1970-01-01T${timeString}`).toLocaleTimeString(undefined, options);
}

// Function to generate random colors for charts
function getRandomColor() {
  const letters = '0123456789ABCDEF';
  let color = '#';
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

// Function to get predefined colors for chart categories
function getCategoryColors() {
  return {
    present: '#28a745',   // Green
    absent: '#dc3545',    // Red
    late: '#ffc107',      // Yellow
    excused: '#17a2b8'    // Cyan
  };
}
