/**
 * DeepGuard Analyze Media Handler
 */

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const previewBox = document.getElementById("preview-box");
  const previewContainer = document.getElementById("preview-container");
  const fileNameDisplay = document.getElementById("file-name-display");
  const fileSizeDisplay = document.getElementById("file-size-display");
  const btnAnalyze = document.getElementById("btn-analyze");
  const btnRemove = document.getElementById("btn-remove");
  const hudProgress = document.getElementById("hud-progress");
  const progressBarFill = document.getElementById("progress-bar-fill");
  const stepList = document.getElementById("hud-step-list");

  let selectedFile = null;

  if (!dropzone || !fileInput) return;

  // Drag and drop handlers
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('drag-over');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('drag-over');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  });

  dropzone.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  if (btnRemove) {
    btnRemove.addEventListener('click', (e) => {
      e.stopPropagation();
      resetFileSelection();
    });
  }

  function handleFileSelection(file) {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    const allowedImages = ['.jpg', '.jpeg', '.png', '.webp'];
    const allowedVideos = ['.mp4', '.mov', '.avi'];

    if (!allowedImages.includes(ext) && !allowedVideos.includes(ext)) {
      showToast(`Unsupported file extension '${ext}'. Please upload JPG, PNG, WEBP, MP4, MOV, or AVI.`, 'error');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      showToast('File size exceeds 50MB limit.', 'error');
      return;
    }

    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = formatBytes(file.size);

    // Generate Preview
    previewContainer.innerHTML = '';
    const fileURL = URL.createObjectURL(file);

    if (allowedImages.includes(ext)) {
      const img = document.createElement('img');
      img.src = fileURL;
      img.className = 'preview-media';
      previewContainer.appendChild(img);
    } else {
      const video = document.createElement('video');
      video.src = fileURL;
      video.className = 'preview-media';
      video.controls = true;
      previewContainer.appendChild(video);
    }

    previewBox.style.display = 'block';
    dropzone.style.display = 'none';
    btnAnalyze.disabled = false;
  }

  function resetFileSelection() {
    selectedFile = null;
    fileInput.value = '';
    previewContainer.innerHTML = '';
    previewBox.style.display = 'none';
    dropzone.style.display = 'block';
    btnAnalyze.disabled = true;
    hudProgress.style.display = 'none';
  }

  if (btnAnalyze) {
    btnAnalyze.addEventListener('click', async () => {
      if (!selectedFile) return;

      btnAnalyze.disabled = true;
      hudProgress.style.display = 'block';

      // Start HUD Progress Animation
      const steps = [
        "1. Validating upload payload integrity...",
        "2. Extracting EXIF camera & software metadata...",
        "3. Computing Error Level Analysis (ELA) & noise variance...",
        "4. Analyzing frequency spectrum & Laplacian sharpness...",
        "5. Running PyTorch face deepfake detection model...",
        "6. Aggregating confidence score & generating report..."
      ];

      stepList.innerHTML = '';
      steps.forEach((stepText, idx) => {
        const li = document.createElement('li');
        li.id = `hud-step-${idx}`;
        li.innerHTML = `<i class="fas fa-circle-notch"></i> ${stepText}`;
        stepList.appendChild(li);
      });

      // Animate steps
      let currentStep = 0;
      const interval = setInterval(() => {
        if (currentStep < steps.length) {
          const stepElem = document.getElementById(`hud-step-${currentStep}`);
          if (stepElem) {
            stepElem.className = 'active';
            if (currentStep > 0) {
              const prev = document.getElementById(`hud-step-${currentStep - 1}`);
              if (prev) {
                prev.className = 'done';
                prev.innerHTML = `<i class="fas fa-check-circle"></i> ${steps[currentStep - 1]}`;
              }
            }
          }
          progressBarFill.style.width = `${((currentStep + 1) / steps.length) * 80}%`;
          currentStep++;
        } else {
          clearInterval(interval);
        }
      }, 400);

      // Perform API upload call
      const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
      const isVideo = ['.mp4', '.mov', '.avi'].includes(ext);
      const endpoint = isVideo ? '/api/analyze/video' : '/api/analyze/image';

      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          body: formData
        });

        clearInterval(interval);

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Analysis request failed.');
        }

        const data = await response.json();
        progressBarFill.style.width = '100%';

        showToast('Analysis completed successfully!', 'success');
        
        setTimeout(() => {
          window.location.href = `results.html?id=${data.id}`;
        }, 600);

      } catch (err) {
        clearInterval(interval);
        hudProgress.style.display = 'none';
        btnAnalyze.disabled = false;
        showToast(err.message || 'Error conducting media analysis.', 'error');
      }
    });
  }
});
