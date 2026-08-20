import * as THREE from 'three'

import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'

const scene = new THREE.Scene()

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / (window.innerHeight * 0.3), 0.1, 1000)

camera.position.set(0, -3, 10)

const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true
})

// closedBy dialog Polyfill
const supportsClosedBy =
    "closedBy" in HTMLDialogElement.prototype;

if (supportsClosedBy) {
    // 特に何もしない
} else {
    const backdrop = document.querySelectorAll(":not(dialog):not(dialog *)")
    backdrop.forEach(el => {
        el.addEventListener("click", (e) => {
            const openDialogs = document.querySelectorAll("dialog[open]")
            openDialogs.forEach(dialog => {
                if (e.target == dialog) {
                    dialog.close()
                }
            })
        })
    })
}

renderer.setSize(window.innerWidth, window.innerHeight * 0.3)
renderer.setPixelRatio(window.devicePixelRatio)

renderer.outputColorSpace = THREE.SRGBColorSpace
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.toneMappingExposure = 1.0

document.getElementById('three-container').appendChild(renderer.domElement)

const directionalLight = new THREE.DirectionalLight(
    0xffffff,
    1.5
)

directionalLight.position.set(5, 10, 5)

scene.add(directionalLight)

const pmremGenerator = new THREE.PMREMGenerator(renderer)
pmremGenerator.compileEquirectangularShader()

const rgbeLoader = new RGBELoader()

rgbeLoader.load(hdriURL, (texture) => {
    const envMap = pmremGenerator.fromEquirectangular(texture).texture
    scene.environment = envMap
    scene.background = envMap
    texture.dispose()
    pmremGenerator.dispose()
})

const controls = new OrbitControls(
    camera,
    renderer.domElement
)

controls.enableDamping = true
controls.target.set(0, 0, 0)

const loader = new GLTFLoader()

loader.setMeshoptDecoder(MeshoptDecoder)

const dracoLoader = new DRACOLoader()

dracoLoader.setDecoderPath(
    "{% static 'js/draco@1.5.7/decoders/' %}"
)
window.modelMaterials = []


loader.setDRACOLoader(dracoLoader)
// alert(roughness+','+metalness+','+albedo)
loader.load(
    modelURL,
    (gltf) => {
        const model = gltf.scene
        model.scale.set(3, 3, 3);

        model.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true
                child.receiveShadow = true

                const material = child.material

                if (material) {
                    if ('roughness' in material) { material.roughness = roughness }

                    if ('metalness' in material) { material.metalness = metalness }

                    if ('color' in material) { material.color.set(albedo) }

                    material.envMapIntensity = 1.0
                    material.needsUpdate = true
                }
                window.modelMaterials.push(material)
                initColorPicker(albedo)
            }
        })


        scene.add(model)
    }
)

window.addEventListener('resize', () => {

    camera.aspect =
        window.innerWidth / (window.innerHeight * 0.3)

    camera.updateProjectionMatrix()

    renderer.setSize(
        window.innerWidth,
        window.innerHeight * 0.3
    )
})

const saveButton = document.getElementById('save-button');


saveButton.addEventListener('click', () => {
    saveButton.disabled = true;
    const csrfToken = document.getElementById('csrf-token-input').value;
    const roughness = window.modelMaterials?.[0]?.roughness ?? 0.0;
    const metalness = window.modelMaterials?.[0]?.metalness ?? 0.0;
    const albedo = window.modelMaterials?.[0]?.color
        ? '#' + window.modelMaterials[0].color.getHexString()
        : '#FFFFFF';

    // 1. ユーザーの現在のカメラ状態と背景を一時退避
    const savedPos = camera.position.clone();
    const savedTarget = controls.target.clone();
    const savedBg = scene.background;

    // 2. キャプチャ用の統一アングル・透過背景に設定
    camera.position.set(0, -3, 10);
    controls.target.set(0, 0, 0);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();

    // 透過背景（環境光・反射 scene.environment は有効のまま）
    scene.background = null;

    // レンダリングして WebP 形式のキャプチャを取得
    renderer.render(scene, camera);
    const captureDataUrl = renderer.domElement.toDataURL('image/webp', 0.85);

    // 3. ユーザーの操作状態を復元
    camera.position.copy(savedPos);
    controls.target.copy(savedTarget);
    scene.background = savedBg;
    renderer.render(scene, camera);

    const data = {
        photo_uuid: objectuuid,
        roughness: roughness,
        metalness: metalness,
        albedo: albedo,
        capture_image: captureDataUrl
    };

    console.log('Saving reflectance parameters and capture preview...');

    fetch(api_save_reflectance_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            location.href = gallery3URL;
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('保存処理中に通信エラーが発生しました。');
            saveButton.disabled = false;
        });
});

function animate() {

    requestAnimationFrame(animate)

    controls.update()

    renderer.render(scene, camera)
}

animate()