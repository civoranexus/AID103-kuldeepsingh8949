// CropGuard AI Frontend JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize drag and drop functionality
    initializeDragDrop();

    // Initialize file input
    initializeFileInput();

    // Initialize smooth scrolling
    initializeSmoothScrolling();

    // Initialize animations
    initializeAnimations();
}

function initializeDragDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
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

function initializeFileInput() {
    const fileInput = document.getElementById('fileInput');

    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            // Reset previous state when new file is selected
            const resultsSection = document.getElementById('results');
            if (resultsSection) {
                resultsSection.style.display = 'none';
            }
            
            // Clear previous selected file
            window.selectedFile = null;
            
            // Handle new file
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

    // Validate file size (max 10MB)
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

            // Enable analyze button
            if (analyzeBtn) {
                analyzeBtn.style.display = 'block';
            }

            // Store file for later use
            window.selectedFile = file;
        }
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    const previewSection = document.getElementById('previewSection');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('results');

    // Hide preview and show upload area
    if (previewSection) previewSection.style.display = 'none';
    if (uploadArea) uploadArea.style.display = 'block';
    
    // Show upload section if it was hidden
    const uploadSection = document.getElementById('upload');
    if (uploadSection) {
        uploadSection.style.display = 'block';
    }

    // Clear file input
    if (fileInput) fileInput.value = '';
    window.selectedFile = null;

    // Hide results if visible
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
    
    // Reset button state
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Disease';
    }
}

function analyzeImage() {
    if (!window.selectedFile) {
        showError('Please select an image first');
        return;
    }

    // Disable analyze button to prevent multiple simultaneous requests
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    }

    // Show loading modal
    showLoadingModal();

    // Create FormData for upload
    const formData = new FormData();
    formData.append('file', window.selectedFile);

    // Add timeout and better error handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

    // Send to server with timeout
    fetch('/predict', {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
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

        if (data.success) {
            showResults(data);
        } else {
            showError(data.error || 'An error occurred during analysis');
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        hideLoadingModal();
        
        // Re-enable analyze button on error
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Disease';
        }

        if (error.name === 'AbortError') {
            showError('Request timed out. The server might be busy. Please try again.');
        } else {
            showError('Network error. Please check your connection and try again.');
        }
        console.error('Error:', error);
    });
}

function showResults(data) {
    // Update result image - use server path if available, otherwise use preview
    const resultImage = document.getElementById('resultImage');
    const previewImage = document.getElementById('previewImage');
    
    if (resultImage) {
        if (data.image_path) {
            resultImage.src = data.image_path;
        } else if (previewImage && previewImage.src) {
            resultImage.src = previewImage.src;
        }
    }

    // Update main prediction
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
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Keep upload section visible but show results
    // Don't hide upload section - allow users to analyze another image
    // The "Analyze Another" button will handle resetting
}

function hideResults() {
    const resultsSection = document.getElementById('results');
    resultsSection.style.display = 'none';
    document.getElementById('upload').style.display = 'block';
}

function resetUpload() {
    // Reset all UI elements
    const uploadSection = document.getElementById('upload');
    const resultsSection = document.getElementById('results');
    const previewSection = document.getElementById('previewSection');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    // Show upload section
    if (uploadSection) {
        uploadSection.style.display = 'block';
    }
    
    // Hide results
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
    
    // Reset preview
    if (previewSection) {
        previewSection.style.display = 'none';
    }
    
    // Show upload area
    if (uploadArea) {
        uploadArea.style.display = 'block';
    }
    
    // Clear file input
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset button state
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Disease';
    }
    
    // Clear selected file
    window.selectedFile = null;
    
    // Scroll back to upload section
    if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: 'smooth' });
    }
}

function downloadReport() {
    // Create a simple text report
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

    // Create and download file
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cropguard_report_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function showLoadingModal() {
    const modal = document.getElementById('loadingModal');
    modal.classList.add('show');
}

function hideLoadingModal() {
    const modal = document.getElementById('loadingModal');
    modal.classList.remove('show');
}

function showError(message) {
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorModal.classList.add('show');
}

function closeModals() {
    document.getElementById('loadingModal').classList.remove('show');
    document.getElementById('errorModal').classList.remove('show');
}

function initializeSmoothScrolling() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
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

function scrollToUpload() {
    document.getElementById('upload').scrollIntoView({ behavior: 'smooth' });
}

function scrollToFeatures() {
    document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
}

function initializeAnimations() {
    // Add fade-in animation to feature cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);

    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        observer.observe(card);
    });

    // Observe step cards
    document.querySelectorAll('.step').forEach(step => {
        observer.observe(step);
    });
}

// Utility functions
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

// Add some visual feedback for button interactions
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn')) {
        e.target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            e.target.style.transform = '';
        }, 150);
    }
});

// Handle window resize for responsive adjustments
window.addEventListener('resize', debounce(function() {
    // Add any responsive adjustments here if needed
}, 250));

// Add keyboard navigation support
document.addEventListener('keydown', function(e) {
    // ESC key to close modals
    if (e.key === 'Escape') {
        closeModals();
    }

    // Enter key to analyze if file is selected
    if (e.key === 'Enter' && window.selectedFile && !document.querySelector('.modal.show')) {
        analyzeImage();
    }
});

// Add loading states to buttons
function setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        button.classList.add('loading');
    } else {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-search"></i> Analyze Disease';
        button.classList.remove('loading');
    }
}

// Update analyze button state
const analyzeBtn = document.getElementById('analyzeBtn');
if (analyzeBtn) {
    const originalAnalyzeImage = analyzeImage;
    analyzeImage = function() {
        setButtonLoading(analyzeBtn, true);
        originalAnalyzeImage().finally(() => {
            setButtonLoading(analyzeBtn, false);
        });
    };
}

// Add image validation feedback
function validateImage(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            // Check minimum dimensions
            if (img.width < 64 || img.height < 64) {
                reject('Image is too small. Please use an image at least 64x64 pixels.');
            } else if (img.width > 4096 || img.height > 4096) {
                reject('Image is too large. Please use an image smaller than 4096x4096 pixels.');
            } else {
                resolve(file);
            }
        };
        img.onerror = () => reject('Invalid image file.');
        img.src = URL.createObjectURL(file);
    });
}

// Update handleFile to include image validation
const originalHandleFile = handleFile;
handleFile = function(file) {
    validateImage(file)
        .then(validatedFile => {
            originalHandleFile(validatedFile);
        })
        .catch(error => {
            showError(error);
        });
};

// Add browser compatibility checks
function checkBrowserSupport() {
    const features = {
        'File API': typeof File !== 'undefined',
        'FileReader API': typeof FileReader !== 'undefined',
        'FormData': typeof FormData !== 'undefined',
        'fetch API': typeof fetch !== 'undefined'
    };

    const unsupported = Object.entries(features)
        .filter(([feature, supported]) => !supported)
        .map(([feature]) => feature);

    if (unsupported.length > 0) {
        showError(`Your browser doesn't support: ${unsupported.join(', ')}. Please update your browser.`);
        return false;
    }

    return true;
}

// Check browser support on load
if (!checkBrowserSupport()) {
    console.error('Browser not supported');
}