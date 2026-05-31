import * as THREE from 'three'

import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'
import { DRACOLoader }from 'three/addons/loaders/DRACOLoader.js'

const scene = new THREE.Scene()

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000)

camera.position.set(7, -1.5, -4)
camera.lookAt(0, 0, 0)

const renderer = new THREE.WebGLRenderer({
    antialias: true
})

renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)

renderer.outputColorSpace = THREE.SRGBColorSpace
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.toneMappingExposure = 1.0

document.getElementById('three-container').appendChild(renderer.domElement)

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

const directionalLight = new THREE.DirectionalLight(
    0xffffff,
    1.5
)

directionalLight.position.set(5, 10, 5)

scene.add(directionalLight)

const controls = new OrbitControls(
    camera,
    renderer.domElement
)

controls.enableDamping = true
controls.target.set(0, -1.5, 0)
controls.update()

const loader = new GLTFLoader()

loader.setMeshoptDecoder(MeshoptDecoder)

const dracoLoader = new DRACOLoader()

dracoLoader.setDecoderPath(
    "{% static 'vendor/draco@1.5.7/decorders/' %}"
)

loader.setDRACOLoader(dracoLoader)

loader.load(
    modelURL,
    (gltf) => {
        const model = gltf.scene
        model.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true
                child.receiveShadow = true
                const material = child.material
                if (material) {
                    console.log('parameters', imageAlbedo, imageRoughness, imageMetalness)
                    material.color = new THREE.Color(imageAlbedo)
                    material.roughness = parseFloat(imageRoughness)
                    material.metalness = parseFloat(imageMetalness)
                    material.envMapIntensity = 1.0
                    material.needsUpdate = true
                }
            }
        })
        scene.add(model)
        const box = new THREE.Box3().setFromObject(model)
        const center = box.getCenter(new THREE.Vector3())

        model.position.sub(center)
    },
    undefined,
    (error) => {
        console.error(error)
    }
)

window.addEventListener('resize', () => {

    camera.aspect =
        window.innerWidth / window.innerHeight

    camera.updateProjectionMatrix()

    renderer.setSize(
        window.innerWidth,
        window.innerHeight
    )
})

function animate() {

    requestAnimationFrame(animate)

    controls.update()

    renderer.render(scene, camera)
}

animate()