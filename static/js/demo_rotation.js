// demo_rotation.js - Three.js PBR質感調整＆360度物体回転連番画像生成

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

let scene, camera, renderer, controls;
let targetObject = null;
let currentMaterial = null;
let modelMaterials = [];
let isCapturing = false;

// Captured frames
let capturedFrames = [];
let previewInterval = null;
let currentFrameIndex = 0;

document.addEventListener('DOMContentLoaded', () => {
  initThree();
  setupUI();
});

function initThree() {
  const container = document.getElementById('three-viewport');
  const width = container.clientWidth;
  const height = container.clientHeight;

  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(0, 0, 8);

  renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    preserveDrawingBuffer: true // Required for canvas.toDataURL
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;

  container.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  // Lighting
  const dirLight = new THREE.DirectionalLight(0xffffff, 2.0);
  dirLight.position.set(5, 10, 7);
  scene.add(dirLight);

  const ambLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambLight);

  // Load HDRI Environment
  const pmremGenerator = new THREE.PMREMGenerator(renderer);
  pmremGenerator.compileEquirectangularShader();
  const rgbeLoader = new RGBELoader();

  if (window.ROTATION_CONFIG.hdriURL) {
    rgbeLoader.load(window.ROTATION_CONFIG.hdriURL, (texture) => {
      const envMap = pmremGenerator.fromEquirectangular(texture).texture;
      scene.environment = envMap;
      texture.dispose();
      pmremGenerator.dispose();
    });
  }

  // Load 3D Model or Create Textured Object
  loadModelOrSphere();

  // Animation Loop
  function animate() {
    requestAnimationFrame(animate);
    controls.update();

    const autoRotateCb = document.getElementById('cb-auto-rotate');
    if (autoRotateCb && autoRotateCb.checked && targetObject && !isCapturing) {
      targetObject.rotation.y += 0.01;
    }

    renderer.render(scene, camera);
  }
  animate();

  // Handle Resize
  window.addEventListener('resize', () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });
}

function loadModelOrSphere() {
  const gltfLoader = new GLTFLoader();
  gltfLoader.setMeshoptDecoder(MeshoptDecoder);

  const initialRoughness = parseFloat(window.ROTATION_CONFIG.roughness) || 0.3;
  const initialMetalness = parseFloat(window.ROTATION_CONFIG.metalness) || 0.1;
  const initialAlbedo = window.ROTATION_CONFIG.albedo || '#ffffff';

  // Base texture if segmented image exists
  const textureLoader = new THREE.TextureLoader();
  let baseTexture = null;
  if (window.ROTATION_CONFIG.textureURL) {
    baseTexture = textureLoader.load(window.ROTATION_CONFIG.textureURL);
    baseTexture.colorSpace = THREE.SRGBColorSpace;
  }

  if (window.ROTATION_CONFIG.modelURL) {
    gltfLoader.load(
      window.ROTATION_CONFIG.modelURL,
      (gltf) => {
        targetObject = gltf.scene;
        targetObject.scale.set(3, 3, 3);
        targetObject.position.set(0, -1.5, 0);

        modelMaterials = [];
        targetObject.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.roughness = initialRoughness;
            child.material.metalness = initialMetalness;
            child.material.color = new THREE.Color(initialAlbedo);
            if (baseTexture) child.material.map = baseTexture;
            child.material.needsUpdate = true;
            modelMaterials.push(child.material);
          }
        });
        scene.add(targetObject);
      },
      undefined,
      (error) => {
        console.warn('GLB Load failed, falling back to Sphere:', error);
        createFallbackSphere(initialRoughness, initialMetalness, initialAlbedo, baseTexture);
      }
    );
  } else {
    createFallbackSphere(initialRoughness, initialMetalness, initialAlbedo, baseTexture);
  }
}

function createFallbackSphere(roughness, metalness, albedo, texture) {
  const geometry = new THREE.SphereGeometry(2, 64, 64);
  const material = new THREE.MeshStandardMaterial({
    roughness: roughness,
    metalness: metalness,
    color: new THREE.Color(albedo),
    map: texture || null
  });
  targetObject = new THREE.Mesh(geometry, material);
  modelMaterials = [material];
  scene.add(targetObject);
}

function updateMaterialProperties(roughness, metalness, albedo) {
  modelMaterials.forEach((mat) => {
    mat.roughness = roughness;
    mat.metalness = metalness;
    mat.color.set(albedo);
    mat.needsUpdate = true;
  });
}

function setupUI() {
  const sliderRoughness = document.getElementById('slider-roughness');
  const sliderMetalness = document.getElementById('slider-metalness');
  const inputAlbedo = document.getElementById('input-albedo');
  const valRoughness = document.getElementById('val-roughness');
  const valMetalness = document.getElementById('val-metalness');

  function onParamChange() {
    const r = parseFloat(sliderRoughness.value);
    const m = parseFloat(sliderMetalness.value);
    const a = inputAlbedo.value;

    valRoughness.textContent = r.toFixed(2);
    valMetalness.textContent = m.toFixed(2);

    updateMaterialProperties(r, m, a);
  }

  sliderRoughness.addEventListener('input', onParamChange);
  sliderMetalness.addEventListener('input', onParamChange);
  inputAlbedo.addEventListener('input', onParamChange);

  // Capture Button
  const btnCapture = document.getElementById('btn-capture-rotation');
  btnCapture.addEventListener('click', capture360Frames);

  // Download Button
  const btnDownloadZip = document.getElementById('btn-download-frames-zip');
  btnDownloadZip.addEventListener('click', downloadFramesZip);
}

async function capture360Frames() {
  if (!targetObject || isCapturing) return;

  isCapturing = true;
  const overlay = document.getElementById('capture-overlay');
  const progressText = document.getElementById('capture-progress-text');
  const frameSelect = document.getElementById('select-frame-count');
  const totalFrames = parseInt(frameSelect.value, 10) || 36;

  overlay.style.display = 'flex';
  capturedFrames = [];

  // Reset rotation and camera
  const originalRotationY = targetObject.rotation.y;

  const step = (Math.PI * 2) / totalFrames;

  for (let i = 0; i < totalFrames; i++) {
    targetObject.rotation.y = step * i;
    renderer.render(scene, camera);

    const dataUrl = renderer.domElement.toDataURL('image/png');
    capturedFrames.push(dataUrl);

    progressText.textContent = `キャプチャ中... (${i + 1} / ${totalFrames} フレーム)`;
    await new Promise((r) => setTimeout(r, 40));
  }

  // Restore original rotation
  targetObject.rotation.y = originalRotationY;
  isCapturing = false;
  overlay.style.display = 'none';

  // Render Preview
  renderFramesPreview();
}

function renderFramesPreview() {
  const filmstrip = document.getElementById('frame-filmstrip');
  filmstrip.innerHTML = '';

  capturedFrames.forEach((frameUrl, idx) => {
    const img = document.createElement('img');
    img.src = frameUrl;
    img.className = 'frame-thumb';
    img.title = `Frame #${idx + 1}`;
    filmstrip.appendChild(img);
  });

  const previewCard = document.getElementById('rotation-preview-card');
  previewCard.style.display = 'block';

  const previewImg = document.getElementById('animated-preview-img');
  const btnDownload = document.getElementById('btn-download-frames-zip');
  btnDownload.disabled = false;

  // Start Animation loop
  if (previewInterval) clearInterval(previewInterval);
  currentFrameIndex = 0;

  const fpsSlider = document.getElementById('slider-fps');
  const fpsValue = document.getElementById('val-fps');

  function startLoop() {
    const fps = parseInt(fpsSlider.value, 10) || 24;
    fpsValue.textContent = `${fps} FPS`;
    if (previewInterval) clearInterval(previewInterval);

    previewInterval = setInterval(() => {
      if (capturedFrames.length === 0) return;
      currentFrameIndex = (currentFrameIndex + 1) % capturedFrames.length;
      previewImg.src = capturedFrames[currentFrameIndex];
    }, 1000 / fps);
  }

  fpsSlider.oninput = startLoop;
  startLoop();
}

async function downloadFramesZip() {
  if (capturedFrames.length === 0) return;

  const btnDownload = document.getElementById('btn-download-frames-zip');
  btnDownload.disabled = true;
  btnDownload.textContent = 'ZIP生成中...';

  const exportPayload = {
    frames: capturedFrames,
    title: `rotation_360_${window.ROTATION_CONFIG.photoUUID}`,
    metadata: {
      photo_uuid: window.ROTATION_CONFIG.photoUUID,
      frame_count: capturedFrames.length,
      roughness: parseFloat(document.getElementById('slider-roughness').value),
      metalness: parseFloat(document.getElementById('slider-metalness').value),
      albedo: document.getElementById('input-albedo').value,
      timestamp: new Date().toISOString()
    }
  };

  try {
    const response = await fetch(window.ROTATION_CONFIG.apiExportZipURL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(exportPayload)
    });

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rotation_360_${window.ROTATION_CONFIG.photoUUID}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    alert('ZIPダウンロードに失敗しました: ' + err.message);
  } finally {
    btnDownload.disabled = false;
    btnDownload.textContent = '連番画像ZIPを一括ダウンロード';
  }
}
