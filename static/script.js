// --- DOM Element References ---
const csvFileInput = document.getElementById('csv-file');
const fileNameSpan = document.getElementById('file-name');
const promptInput = document.getElementById('prompt-input');
const generateStepsBtn = document.getElementById('generate-steps-btn');
const stepsContainer = document.getElementById('steps-container');
const applyCleaningBtn = document.getElementById('apply-cleaning-btn');
const dataPreview = document.getElementById('data-preview');
const messageArea = document.getElementById('message-area');

let uploadedFile = null;

// --- Event Listeners ---
csvFileInput.addEventListener('change', handleFileUpload);
generateStepsBtn.addEventListener('click', handleGenerateSteps);
applyCleaningBtn.addEventListener('click', handleApplyCleaning);

// --- Functions ---
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file && file.type === "text/csv") {
        uploadedFile = file;
        fileNameSpan.textContent = file.name;
        generateStepsBtn.disabled = false;
        
        // Upload the file immediately to the backend
        const formData = new FormData();
        formData.append('file', uploadedFile);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                showMessage(`File '${data.filename}' uploaded successfully. Original data has ${data.rows} rows.`, 'success');
                displayDataPreview(data.preview);
            } else {
                showMessage(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred during file upload.', 'error');
        });

    } else {
        showMessage('Please select a valid .csv file.', 'error');
        fileNameSpan.textContent = 'No file selected';
        generateStepsBtn.disabled = true;
        uploadedFile = null;
    }
}

async function handleGenerateSteps() {
    if (!uploadedFile || !promptInput.value) {
        showMessage('Please upload a file and describe your goal first.', 'error');
        return;
    }
    
    generateStepsBtn.disabled = true;
    generateStepsBtn.textContent = 'Generating...';

    try {
        const response = await fetch('/generate_steps', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: promptInput.value })
        });
        const data = await response.json();

        if (data.steps) {
            renderSteps(data.steps);
            applyCleaningBtn.disabled = false;
            showMessage('AI has generated cleaning steps. You can now edit, reorder, or delete them.', 'success');
        } else {
            showMessage(data.error || 'Could not generate steps.', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('An error occurred while generating steps.', 'error');
    } finally {
        generateStepsBtn.disabled = false;
        generateStepsBtn.textContent = 'Generate Cleaning Steps';
    }
}

async function handleApplyCleaning() {
    const stepElements = document.querySelectorAll('.step-item input[type="text"]');
    const steps = Array.from(stepElements).map(input => input.value);
    
    if (steps.length === 0) {
        showMessage('No cleaning steps to apply.', 'error');
        return;
    }

    applyCleaningBtn.disabled = true;
    applyCleaningBtn.textContent = 'Cleaning...';

    try {
        const response = await fetch('/apply_cleaning', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ steps: steps })
        });
        const data = await response.json();

        if (data.success) {
            showMessage(data.message, 'success');
            displayDataPreview(data.preview);
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('An error occurred while applying cleaning steps.', 'error');
    } finally {
        applyCleaningBtn.disabled = false;
        applyCleaningBtn.textContent = 'Apply Cleaning & Show Preview';
    }
}

function renderSteps(steps) {
    stepsContainer.innerHTML = ''; // Clear existing steps
    steps.forEach((stepText, index) => {
        const stepItem = document.createElement('div');
        stepItem.className = 'step-item';
        stepItem.draggable = true;
        stepItem.innerHTML = `
            <span class="drag-handle">☰</span>
            <input type="text" value="${escapeHtml(stepText)}">
            <div class="step-actions">
                <button class="delete-btn" title="Delete Step">✖</button>
            </div>
        `;
        stepsContainer.appendChild(stepItem);
        
        // Add event listener for the delete button
        stepItem.querySelector('.delete-btn').addEventListener('click', () => {
            stepItem.remove();
            if (stepsContainer.children.length === 0) {
                applyCleaningBtn.disabled = true;
                stepsContainer.innerHTML = '<p>No steps defined. Generate new ones.</p>';
            }
        });
    });

    // Add drag and drop functionality
    let draggedItem = null;
    stepsContainer.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('step-item')) {
            draggedItem = e.target;
            setTimeout(() => {
                if(draggedItem) draggedItem.style.opacity = '0.5';
            }, 0);
        }
    });
    stepsContainer.addEventListener('dragend', (e) => {
        setTimeout(() => {
            if (draggedItem) {
                draggedItem.style.opacity = '1';
                draggedItem = null;
            }
        }, 0);
    });
    stepsContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        const afterElement = getDragAfterElement(stepsContainer, e.clientY);
        if (draggedItem) {
            if (afterElement == null) {
                stepsContainer.appendChild(draggedItem);
            } else {
                stepsContainer.insertBefore(draggedItem, afterElement);
            }
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.step-item:not(.dragging)')];
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function displayDataPreview(data) {
    if (!data || data.length === 0) {
        dataPreview.innerHTML = '<p>No data to display.</p>';
        return;
    }
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');
    
    // Headers
    const headerRow = document.createElement('tr');
    Object.keys(data[0]).forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    
    // Body
    data.forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    
    table.appendChild(thead);
    table.appendChild(tbody);
    
    dataPreview.innerHTML = '';
    dataPreview.appendChild(table);
}

function showMessage(text, type) {
    messageArea.innerHTML = `<div class="message ${type}">${escapeHtml(text)}</div>`;
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
