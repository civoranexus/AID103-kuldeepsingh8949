// ===== BASIC CROPGUARD AI FRONTEND =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initializeDragDrop();
    initializeFileInput();
    initializeSmoothScrolling();
}

// ===== DRAG & DROP FUNCTIONALITY =====
function initializeDragDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (!uploadArea || !fileInput) return;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        uploadArea.classList.add('dragover');
    }

    function unhighlight() {
        uploadArea.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            handleFile(files[0]);
        }
    }
}

// ===== FILE INPUT HANDLING =====
function initializeFileInput() {
    const fileInput = document.getElementById('fileInput');

    if (!fileInput) return;

    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            // Hide results when new file is selected
            const resultsSection = document.getElementById('results');
            if (resultsSection) {
                resultsSection.style.display = 'none';
            }

            handleFile(e.target.files[0]);
        }
    });
}

function handleFile(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file (JPG, PNG, JPEG, GIF)');
        return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB');
        return;
    }

    // Show preview
    showImagePreview(file);
}

function showImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewImage = document.getElementById('previewImage');
        const previewSection = document.getElementById('previewSection');
        const uploadArea = document.getElementById('uploadArea');
        const analyzeBtn = document.getElementById('analyzeBtn');

        if (previewImage && previewSection && uploadArea) {
            previewImage.src = e.target.result;

            // Hide upload area and show preview
            uploadArea.style.display = 'none';
            previewSection.style.display = 'block';

            // Show analyze button
            if (analyzeBtn) {
                analyzeBtn.style.display = 'block';
            }

            // Store file for later use
            window.selectedFile = file;
        }
    };
    reader.readAsDataURL(file);
}

// ===== IMAGE ANALYSIS =====
function analyzeImage() {
    if (!window.selectedFile) {
        showError('Please select an image first');
        return;
    }

    // Disable analyze button
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    }

    // Show loading modal
    showLoadingModal();

    // Create FormData - pass filename explicitly for Safari/compatibility
    const formData = new FormData();
    const file = window.selectedFile;
    const fileName = file.name && file.name.trim() ? file.name : 'image.jpg';
    formData.append('file', file, fileName);

    // Set timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    // Send request
    fetch('/predict', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId);
            const contentType = response.headers.get('content-type') || '';
            if (!response.ok) {
                if (contentType.includes('application/json')) {
                    return response.json().then(data => {
                        throw new Error(data.error || `Server error: ${response.status}`);
                    });
                }
                throw new Error(`Server error: ${response.status}`);
            }
            if (!contentType.includes('application/json')) {
                throw new Error('Invalid response from server. Please try again.');
            }
            return response.json();
        })
        .then(data => {
            hideLoadingModal();

            // Re-enable analyze button
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Disease';
            }

            if (data && data.success) {
                showResults(data);
            } else {
                const errMsg = (data && data.error) ? data.error : 'An error occurred during analysis.';
                console.error('[CropGuard] Prediction failed:', data);
                showError(errMsg);
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            hideLoadingModal();

            // Re-enable analyze button
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Disease';
            }

            if (error.name === 'AbortError') {
                showError('Request timed out. Please try again.');
            } else if (error.message) {
                showError(error.message);
            } else {
                showError('Network error. Please check your connection and try again.');
            }
            console.error('Error:', error);
        });
}

// ===== RESULTS DISPLAY =====
function showResults(data) {
    // Update result image
    const resultImage = document.getElementById('resultImage');
    const previewImage = document.getElementById('previewImage');

    if (resultImage) {
        if (data.image_path) {
            resultImage.src = data.image_path;
        } else if (previewImage && previewImage.src) {
            resultImage.src = previewImage.src;
        }
    }

    // Update prediction title
    const predictionTitle = document.getElementById('predictionTitle');
    if (predictionTitle) {
        predictionTitle.textContent = data.prediction || 'Unknown';
    }

    // Update confidence bar
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceText = document.getElementById('confidenceText');
    if (confidenceFill && confidenceText) {
        const confidencePercent = Math.round((data.confidence || 0) * 100);
        confidenceFill.style.width = confidencePercent + '%';
        confidenceText.textContent = confidencePercent + '%';
    }

    // Update top predictions
    const predictionList = document.getElementById('predictionList');
    if (predictionList) {
        predictionList.innerHTML = '';

        if (data.top_3_predictions && Array.isArray(data.top_3_predictions)) {
            data.top_3_predictions.forEach(prediction => {
                const predictionItem = document.createElement('div');
                predictionItem.className = 'prediction-item';

                predictionItem.innerHTML = `
                    <span class="prediction-name">${prediction.class || 'Unknown'}</span>
                    <span class="prediction-confidence">${Math.round((prediction.confidence || 0) * 100)}%</span>
                `;

                predictionList.appendChild(predictionItem);
            });
        }
    }

    // Show results section
    const resultsSection = document.getElementById('results');
    if (resultsSection) {
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({
            behavior: 'smooth'
        });
    }
}

// ===== UTILITY FUNCTIONS =====
function removeImage() {
    const previewSection = document.getElementById('previewSection');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('results');

    // Hide preview and show upload area
    if (previewSection) previewSection.style.display = 'none';
    if (uploadArea) uploadArea.style.display = 'block';

    // Clear file input
    if (fileInput) fileInput.value = '';
    window.selectedFile = null;

    // Hide results
    if (resultsSection) resultsSection.style.display = 'none';

    // Reset button
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Disease';
        analyzeBtn.style.display = 'none';
    }
}

function resetUpload() {
    removeImage();

    // Show upload section
    const uploadSection = document.getElementById('upload');
    if (uploadSection) {
        uploadSection.scrollIntoView({
            behavior: 'smooth'
        });
    }
}

function downloadReport() {
    const prediction = document.getElementById('predictionTitle').textContent;
    const confidence = document.getElementById('confidenceText').textContent;

    const reportContent = `
CropGuard AI Disease Detection Report
=====================================

Analysis Date: ${new Date().toLocaleString()}
Prediction: ${prediction}
Confidence: ${confidence}

Top Predictions:
${Array.from(document.querySelectorAll('.prediction-item')).map(item => {
    const name = item.querySelector('.prediction-name').textContent;
    const conf = item.querySelector('.prediction-confidence').textContent;
    return `- ${name}: ${conf}`;
}).join('\n')}

=====================================
Generated by CropGuard AI
    `.trim();

    const blob = new Blob([reportContent], {
        type: 'text/plain'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cropguard_report_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ===== MODALS =====
function showLoadingModal() {
    const modal = document.getElementById('loadingModal');
    if (modal) modal.style.display = 'flex';
}

function hideLoadingModal() {
    const modal = document.getElementById('loadingModal');
    if (modal) modal.style.display = 'none';
}

function showError(message) {
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    // Ensure we always show a helpful message (avoid generic "An error occurred")
    let displayMsg = (message && String(message).trim()) ? message : 'An error occurred during analysis. Please try again.';
    if (displayMsg === 'An error occurred') {
        displayMsg = 'An error occurred during analysis. Please try again.';
    }
    if (errorModal && errorMessage) {
        errorMessage.textContent = displayMsg;
        errorModal.classList.add('show');
    } else {
        alert(displayMsg);
    }
}

function closeModals() {
    hideLoadingModal();
    const errorModal = document.getElementById('errorModal');
    if (errorModal) {
        errorModal.classList.remove('show');
    }
}

// ===== SMOOTH SCROLLING =====
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', function(e) {
    // ESC to close modals
    if (e.key === 'Escape') {
        closeModals();
    }

    // Enter to analyze if file is selected
    if (e.key === 'Enter' && window.selectedFile) {
        analyzeImage();
    }
});