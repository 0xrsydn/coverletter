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
  // Use a relative URL to hide the actual API domain
  const apiEndpoint = '/api/generate_cover_letter';
  
  // Set the hx-post attribute to the API endpoint
  document.getElementById('cover_letter_form').setAttribute('hx-post', apiEndpoint);
  
  // Log to confirm it's being set correctly
  console.log('API endpoint set to:', apiEndpoint);
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
  const textInput = document.getElementById('job_desc_text');
  const imageInput = document.getElementById('job_desc_image');
  
  if (document.querySelector('input[name="job_desc_type"]:checked').value === 'text') {
    // Show text container, hide image container
    textContainer.classList.remove('hidden');
    imageContainer.classList.add('hidden');
    
    // Update required attributes
    textInput.setAttribute('required', '');
    imageInput.removeAttribute('required');
  } else {
    // Show image container, hide text container
    textContainer.classList.add('hidden');
    imageContainer.classList.remove('hidden');
    
    // Update required attributes
    textInput.removeAttribute('required');
    imageInput.setAttribute('required', '');
  }
}

/**
 * Sets up form validation before submission
 */
function setupFormValidation() {
  const form = document.getElementById('cover_letter_form');
  const generateButton = document.getElementById('generate_btn');
  
  // Prevent default form submission and handle it manually
  form.addEventListener('submit', function(event) {
    event.preventDefault();
    
    // Show loading indicator
    document.getElementById('cover_letter_loading').classList.remove('hidden');
    
    // Set button to loading state
    generateButton.classList.add('loading');
    generateButton.disabled = true;
    
    // Get form data
    const formData = new FormData(form);
    
    // Handle job description type - ensure only one type is sent
    const jobDescType = document.querySelector('input[name="job_desc_type"]:checked').value;
    
    if (jobDescType === 'text') {
      // Text mode - ensure job_desc_image is empty
      formData.delete('job_desc_image');
      // Make sure job_desc_text is not empty
      if (!formData.get('job_desc_text') || formData.get('job_desc_text').trim() === '') {
        window.appUtils.showError('Please enter a job description text');
        // Reset button state
        generateButton.classList.remove('loading');
        generateButton.disabled = false;
        // Hide loading indicator
        document.getElementById('cover_letter_loading').classList.add('hidden');
        return;
      }
    } else {
      // Image mode - ensure job_desc_text is empty
      formData.set('job_desc_text', '');
      
      // Make sure job_desc_image is not empty
      if (!formData.get('job_desc_image') || formData.get('job_desc_image').size === 0) {
        window.appUtils.showError('Please upload a job description image');
        // Reset button state
        generateButton.classList.remove('loading');
        generateButton.disabled = false;
        // Hide loading indicator
        document.getElementById('cover_letter_loading').classList.add('hidden');
        return;
      }
    }
    
    // Validate form
    const validation = window.appUtils.validateForm(formData);
    
    if (!validation.isValid) {
      // Show error
      window.appUtils.showError(validation.errorMessage);
      // Hide loading indicator
      document.getElementById('cover_letter_loading').classList.add('hidden');
      // Reset button state
      generateButton.classList.remove('loading');
      generateButton.disabled = false;
      return;
    }
    
    // Use a relative URL to hide the actual API domain
    const apiEndpoint = '/api/generate_cover_letter';
    
    // Submit form data directly using fetch
    fetch(apiEndpoint, {
      method: 'POST',
      body: formData,
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok: ' + response.status);
      }
      return response.text();
    })
    .then(data => {
      // Update the editor with the generated cover letter
      document.getElementById('cover_letter_editor').value = data;
    })
    .catch(error => {
      window.appUtils.showError('Network error: ' + error.message);
    })
    .finally(() => {
      // Hide loading indicator
      document.getElementById('cover_letter_loading').classList.add('hidden');
      // Reset button state
      generateButton.classList.remove('loading');
      generateButton.disabled = false;
    });
  });
  
  // We'll keep these event listeners for any HTMX fallback but they likely won't be used now
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