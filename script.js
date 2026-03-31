// API Configuration
const API_BASE_URL = 'https://industrial-skills-2.preview.emergentagent.com/api';

// Get DOM elements
const form = document.getElementById('candidateForm');
const formContainer = document.getElementById('formContainer');
const welcomeContainer = document.getElementById('welcomeContainer');
const submitBtn = document.getElementById('submitBtn');

// Form submit handler
form.addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevents page refresh
    
    // Get form values
    const formData = {
        name: document.getElementById('name').value,
        surname: document.getElementById('surname').value,
        trade: document.getElementById('trade').value,
        year: parseInt(document.getElementById('year').value),
        dob: document.getElementById('dob').value
    };
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    try {
        // Send data to backend API
        const response = await fetch(`${API_BASE_URL}/candidates`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Registration successful:', result);
            
            // Hide the form
            formContainer.classList.add('hidden');
            
            // Show the welcome screen (stays until page refresh)
            welcomeContainer.classList.remove('hidden');
            
            // NO AUTO-RESET - User must manually refresh the page
            
        } else {
            throw new Error('Registration failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to submit registration. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit';
    }
});

// Optional: Function to get all candidates
async function getAllCandidates() {
    try {
        const response = await fetch(`${API_BASE_URL}/candidates`);
        const candidates = await response.json();
        console.log('All Candidates:', candidates);
        return candidates;
    } catch (error) {
        console.error('Error fetching candidates:', error);
    }
}

// Call this function in console to see all registered candidates
// getAllCandidates();