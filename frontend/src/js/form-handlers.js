/**
 * Form handling functionality
 */

/**
 * Sets up all form-related event handlers
 */
export function setupFormHandlers() {
  // Setup the API endpoint
  configureApiEndpoint();
  
  // Handle job description type toggle
  setupJobDescriptionTypeToggle();
  
  // Handle form submission
  setupFormValidation();
  
  // Handle copy button
  setupCopyButton();
}

/**
 * Configures the API endpoint for form submission
 */
function configureApiEndpoint() {
  const apiEndpoint = window.appConfig.apiBaseUrl;
  document.getElementById('cover_letter_form').setAttribute('hx-post', apiEndpoint);
  
  // Also set the hidden input field for the API endpoint
  document.getElementById('api_endpoint').value = apiEndpoint;
}

/**
 * Sets up the job description type toggle
 */
function setupJobDescriptionTypeToggle() {
  const radioButtons = document.querySelectorAll('input[name="job_desc_type"]');
  const textContainer = document.getElementById('job_desc_text_container');
  const imageContainer = document.getElementById('job_desc_image_container');

  // Initial state
  toggleDescriptionType(radioButtons);

  // Add event listeners
  radioButtons.forEach(radio => {
    radio.addEventListener('change', () => toggleDescriptionType(radioButtons));
  });
}

/**
 * Toggle between text and image job description
 * @param {NodeList} radioButtons - The radio button elements
 */
function toggleDescriptionType(radioButtons) {
  const textContainer = document.getElementById('job_desc_text_container');
  const imageContainer = document.getElementById('job_desc_image_container');
  
  if (document.querySelector('input[name="job_desc_type"]:checked').value === 'text') {
    textContainer.classList.remove('hidden');
    imageContainer.classList.add('hidden');
  } else {
    textContainer.classList.add('hidden');
    imageContainer.classList.remove('hidden');
  }
}

/**
 * Sets up form validation before submission
 */
function setupFormValidation() {
  const form = document.getElementById('cover_letter_form');
  
  form.addEventListener('htmx:beforeRequest', function(event) {
    // Get form data
    const formData = new FormData(form);
    
    // Validate form
    const validation = window.appUtils.validateForm(formData);
    
    if (!validation.isValid) {
      // Prevent form submission
      event.preventDefault();
      
      // Show error
      window.appUtils.showError(validation.errorMessage);
    }
  });
  
  // Handle success and errors
  form.addEventListener('htmx:responseError', function(event) {
    let errorMsg = 'Server error occurred. Please try again.';
    
    // Try to parse response as JSON for more specific error
    try {
      const response = JSON.parse(event.detail.xhr.responseText);
      if (response.error) {
        errorMsg = response.error;
      }
    } catch (e) {
      // If we can't parse JSON, use the generic error
    }
    
    window.appUtils.showError(errorMsg);
  });
  
  form.addEventListener('htmx:sendError', function() {
    window.appUtils.showError('Network error. Please check your internet connection and try again.');
  });
}

/**
 * Sets up the copy button functionality
 */
function setupCopyButton() {
  const copyButton = document.getElementById('copy_btn');
  
  if (!copyButton) {
    console.warn('Copy button element not found in the document');
    return;
  }
  
  copyButton.addEventListener('click', function() {
    const coverLetterContent = document.getElementById('cover_letter_editor');
    
    if (coverLetterContent && coverLetterContent.value.trim() !== '') {
      // Try to copy the text
      try {
        navigator.clipboard.writeText(coverLetterContent.value).then(() => {
          // Flash the button to show success
          this.classList.add('btn-success');
          setTimeout(() => {
            this.classList.remove('btn-success');
          }, 1000);
        }).catch(() => {
          window.appUtils.showError('Failed to copy to clipboard');
        });
      } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = coverLetterContent.value;
        textArea.style.position = 'fixed';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
          document.execCommand('copy');
          this.classList.add('btn-success');
          setTimeout(() => {
            this.classList.remove('btn-success');
          }, 1000);
        } catch (err) {
          window.appUtils.showError('Failed to copy to clipboard');
        }
        
        document.body.removeChild(textArea);
      }
    }
  });
} 