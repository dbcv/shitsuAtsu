// demo_segment.js - SAM3 セグメンテーション＆マスク出力デモスクリプト

document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('demo-canvas');
  const ctx = canvas.getContext('2d');
  const overlayCanvas = document.getElementById('overlay-canvas');
  const oCtx = overlayCanvas.getContext('2d');

  let currentMode = 'pos'; // 'pos' or 'neg'
  let ppoints = [];
  let npoints = [];
  let imageObj = new Image();
  let naturalWidth = 0;
  let naturalHeight = 0;
  let displayScale = 1;

  // UI Elements
  const btnPos = document.getElementById('btn-pos-mode');
  const btnNeg = document.getElementById('btn-neg-mode');
  const btnClear = document.getElementById('btn-clear-points');
  const btnRun = document.getElementById('btn-run-sam');
  const btnTextRun = document.getElementById('btn-run-text-sam');
  const textPromptInput = document.getElementById('text-prompt-input');
  const loadingOverlay = document.getElementById('loading-overlay');

  // Result Elements
  const resultMaskImg = document.getElementById('result-mask-img');
  const resultCutoutImg = document.getElementById('result-cutout-img');
  const resultBboxImg = document.getElementById('result-bbox-img');
  const statPixels = document.getElementById('stat-pixels');
  const statPercentage = document.getElementById('stat-percentage');
  const statResolution = document.getElementById('stat-resolution');

  const btnDownloadMask = document.getElementById('btn-download-mask');
  const btnDownloadCutout = document.getElementById('btn-download-cutout');
  const btnDownloadBbox = document.getElementById('btn-download-bbox');
  const btnDownloadZip = document.getElementById('btn-download-zip');

  let lastResultData = null;

  // Load Base Image
  imageObj.crossOrigin = 'anonymous';
  imageObj.src = window.DEMO_CONFIG.imageURL;
  imageObj.onload = () => {
    naturalWidth = imageObj.naturalWidth;
    naturalHeight = imageObj.naturalHeight;

    canvas.width = naturalWidth;
    canvas.height = naturalHeight;
    overlayCanvas.width = naturalWidth;
    overlayCanvas.height = naturalHeight;

    redrawAll();
    statResolution.textContent = `${naturalWidth} × ${naturalHeight}`;
  };

  function redrawAll() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(imageObj, 0, 0);

    oCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    // Draw positive points (Green)
    ppoints.forEach(([x, y]) => {
      drawMarker(oCtx, x, y, '#10b981', '+');
    });

    // Draw negative points (Red)
    npoints.forEach(([x, y]) => {
      drawMarker(oCtx, x, y, '#ef4444', '−');
    });
  }

  function drawMarker(context, x, y, color, symbol) {
    context.save();
    context.shadowColor = 'rgba(0, 0, 0, 0.7)';
    context.shadowBlur = 6;
    context.fillStyle = color;
    context.beginPath();
    context.arc(x, y, 12, 0, Math.PI * 2);
    context.fill();

    context.lineWidth = 2.5;
    context.strokeStyle = '#ffffff';
    context.stroke();

    context.fillStyle = '#ffffff';
    context.font = 'bold 16px sans-serif';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(symbol, x, y);
    context.restore();
  }

  // Click on Overlay Canvas to add points
  overlayCanvas.addEventListener('click', (e) => {
    const rect = overlayCanvas.getBoundingClientRect();
    const scaleX = naturalWidth / rect.width;
    const scaleY = naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    if (currentMode === 'pos') {
      ppoints.push([x, y]);
    } else {
      npoints.push([x, y]);
    }

    redrawAll();
    updatePointsList();
  });

  // Mode Toggles
  btnPos.addEventListener('click', () => {
    currentMode = 'pos';
    btnPos.classList.add('demo-btn-success');
    btnPos.classList.remove('demo-btn-secondary');
    btnNeg.classList.remove('demo-btn-primary');
    btnNeg.classList.add('demo-btn-secondary');
  });

  btnNeg.addEventListener('click', () => {
    currentMode = 'neg';
    btnNeg.classList.add('demo-btn-primary');
    btnNeg.classList.remove('demo-btn-secondary');
    btnPos.classList.remove('demo-btn-success');
    btnPos.classList.add('demo-btn-secondary');
  });

  btnClear.addEventListener('click', () => {
    ppoints = [];
    npoints = [];
    redrawAll();
    updatePointsList();
  });

  function updatePointsList() {
    const countEl = document.getElementById('points-count');
    if (countEl) {
      countEl.textContent = `ポジティブ: ${ppoints.length} 点 / ネガティブ: ${npoints.length} 点`;
    }
  }

  // Run SAM3 API
  async function executeSegmentation(useText = false) {
    loadingOverlay.style.display = 'flex';

    const formData = new FormData();
    formData.append('photo_uuid', window.DEMO_CONFIG.photoUUID);

    if (useText) {
      formData.append('description', textPromptInput.value.trim());
      formData.append('ppoints', '[]');
      formData.append('npoints', '[]');
    } else {
      formData.append('ppoints', JSON.stringify(ppoints));
      formData.append('npoints', JSON.stringify(npoints));
      formData.append('description', textPromptInput.value.trim());
    }

    try {
      const response = await fetch(window.DEMO_CONFIG.apiSegmentURL, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      if (!response.ok || !result.success) {
        alert(result.message || result.error || 'SAM3の実行に失敗しました');
        return;
      }

      lastResultData = result;

      // Update previews
      resultMaskImg.src = `data:image/png;base64,${result.mask_base64}`;
      resultCutoutImg.src = `data:image/png;base64,${result.cutout_base64}`;
      if (result.bbox_base64) {
        resultBboxImg.src = `data:image/png;base64,${result.bbox_base64}`;
      }

      // Update stats
      statPixels.textContent = `${result.stats.foreground_pixels.toLocaleString()} px / ${result.stats.total_pixels.toLocaleString()} px`;
      statPercentage.textContent = `${result.stats.percentage} %`;

      // Enable downloads
      btnDownloadMask.disabled = false;
      btnDownloadCutout.disabled = false;
      if (result.bbox_base64) btnDownloadBbox.disabled = false;
      btnDownloadZip.disabled = false;

    } catch (err) {
      console.error(err);
      alert('エラーが発生しました: ' + err.message);
    } finally {
      loadingOverlay.style.display = 'none';
    }
  }

  btnRun.addEventListener('click', () => executeSegmentation(false));
  btnTextRun.addEventListener('click', () => executeSegmentation(true));

  // Helper download function
  function downloadDataUrl(dataUrl, filename) {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  btnDownloadMask.addEventListener('click', () => {
    if (lastResultData) {
      downloadDataUrl(`data:image/png;base64,${lastResultData.mask_base64}`, `mask_binary_${window.DEMO_CONFIG.photoUUID}.png`);
    }
  });

  btnDownloadCutout.addEventListener('click', () => {
    if (lastResultData) {
      downloadDataUrl(`data:image/png;base64,${lastResultData.cutout_base64}`, `cutout_rgba_${window.DEMO_CONFIG.photoUUID}.png`);
    }
  });

  btnDownloadBbox.addEventListener('click', () => {
    if (lastResultData && lastResultData.bbox_base64) {
      downloadDataUrl(`data:image/png;base64,${lastResultData.bbox_base64}`, `cutout_bbox_${window.DEMO_CONFIG.photoUUID}.png`);
    }
  });

  // Client-side ZIP creation for all SAM3 results
  btnDownloadZip.addEventListener('click', async () => {
    if (!lastResultData) return;

    // Use JSZip from CDN if available or construct backend call
    const exportData = {
      frames: [
        lastResultData.cutout_base64,
        lastResultData.mask_base64,
        ...(lastResultData.bbox_base64 ? [lastResultData.bbox_base64] : [])
      ],
      title: `sam3_materials_${window.DEMO_CONFIG.photoUUID}`,
      metadata: {
        photo_uuid: window.DEMO_CONFIG.photoUUID,
        stats: lastResultData.stats,
        bbox: lastResultData.bbox_info,
        generated_at: new Date().toISOString()
      }
    };

    try {
      const resp = await fetch(window.DEMO_CONFIG.apiExportZipURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportData)
      });
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      downloadDataUrl(url, `sam3_bundle_${window.DEMO_CONFIG.photoUUID}.zip`);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('ZIPのダウンロードに失敗しました: ' + e.message);
    }
  });
});
