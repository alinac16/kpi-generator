document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const fileInput = document.getElementById('csv-file-input');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadCard = document.getElementById('upload-card');
    const uploadArea = document.querySelector('.upload-area');
    const loadingIndicator = document.getElementById('loading-indicator');
    const analysisContainer = document.getElementById('analysis-container');
    const analysisOutput = document.getElementById('analysis-output');
    const resetButton = document.getElementById('reset-button');
    const errorBox = document.getElementById('error-box');
    const errorMessage = document.getElementById('error-message');

    // --- Event Listeners ---

    // Handle file selection via button
    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            handleFile(file);
        }
    });

    // Handle drag and drop events
    uploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', (event) => {
        event.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    uploadArea.addEventListener('drop', (event) => {
        event.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = event.dataTransfer.files[0];
        if (file) {
            handleFile(file);
        }
    });

    // Handle reset button click
    resetButton.addEventListener('click', resetUI);

    // --- UI Update Functions ---

    function resetUI() {
        fileInput.value = ''; // Clear the file input
        fileNameDisplay.textContent = 'CSV up to 10MB';
        uploadCard.classList.remove('hidden');
        analysisContainer.classList.add('hidden');
        loadingIndicator.classList.add('hidden');
        errorBox.classList.add('hidden');
    }

    function showLoading() {
        uploadCard.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');
        errorBox.classList.add('hidden');
        analysisContainer.classList.add('hidden');
    }

    function showResults(markdownContent) {
        analysisOutput.innerHTML = marked.parse(markdownContent);
        loadingIndicator.classList.add('hidden');
        analysisContainer.classList.remove('hidden');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorBox.classList.remove('hidden');
        loadingIndicator.classList.add('hidden');
        // Show the reset button so user can try again
        resetButton.parentElement.classList.remove('hidden'); 
    }

    // --- Core Logic ---

    function handleFile(file) {
        // Validate file type and size
        if (!file.type.match('text/csv') && !file.name.endsWith('.csv')) {
            showError('Please upload a valid CSV file.');
            resetUI();
            return;
        }
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            showError('File is too large. Please upload a file smaller than 10MB.');
            resetUI();
            return;
        }

        fileNameDisplay.textContent = file.name;
        showLoading();

        // Use FormData to send the file to the backend
        const formData = new FormData();
        formData.append('file', file);

        // Fetch request to the Python backend
        fetch('/analyze', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                // If response is not ok, parse the JSON to get the error message
                return response.json().then(err => { throw new Error(err.error || 'An unknown error occurred.') });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                // Handle application-specific errors from the backend
                throw new Error(data.error);
            }
            showResults(data.analysis);
        })
        .catch(error => {
            console.error("Error:", error);
            showError(error.message);
        });
    }
});
