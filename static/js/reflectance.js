import * as THREE from 'three'

import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'
import { DRACOLoader }from 'three/addons/loaders/DRACOLoader.js'

const scene = new THREE.Scene()

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / (window.innerHeight * 0.3), 0.1, 1000)

camera.position.set(0, -3, 10)

const renderer = new THREE.WebGLRenderer({
    antialias: true
})

renderer.setSize(window.innerWidth, window.innerHeight*0.3)
renderer.setPixelRatio(window.devicePixelRatio)

renderer.outputColorSpace = THREE.SRGBColorSpace
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.toneMappingExposure = 1.0

document.getElementById('three-container').appendChild(renderer.domElement)

// const canvas = document.createElement('canvas')
// canvas.width = 1024
// canvas.height = 1024

// const ctx = canvas.getContext('2d')

// ctx.fillStyle = '#ffffff'
// ctx.fillRect(0, 0, canvas.width, canvas.height)

// ctx.strokeStyle = '#000000'
// ctx.lineWidth = 2

// const gridSize = 64

// for (let i = 0; i <= canvas.width; i += gridSize) {
//     ctx.beginPath()
//     ctx.moveTo(i, 0)
//     ctx.lineTo(i, canvas.height)
//     ctx.stroke()

//     ctx.beginPath()
//     ctx.moveTo(0, i)
//     ctx.lineTo(canvas.width, i)
//     ctx.stroke()
// }

// const gridTexture = new THREE.CanvasTexture(canvas)


// const room = new THREE.Mesh(
//     new THREE.BoxGeometry(20, 20, 20),
//     new THREE.MeshStandardMaterial({
//         map: gridTexture,
//         emissive: 0xffffff,
//         emissiveMap: gridTexture,
//         emissiveIntensity: 2,
//         side: THREE.BackSide
//     })
// )

// scene.add(room)

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

// const renderTarget =
//     new THREE.WebGLCubeRenderTarget(512)

// const cubeCamera =
//     new THREE.CubeCamera(
//         0.1,
//         1000,
//         renderTarget
//     )

// scene.add(cubeCamera)

// scene.environment = renderTarget.texture



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
    "{% static 'js/draco@1.5.7/decorders/' %}"
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
                    if ('roughness' in material) {material.roughness = roughness}

                    if ('metalness' in material) {material.metalness = metalness}

                    if ('color' in material) {material.color.set(albedo)}

                    material.envMapIntensity = 1.0
                    material.needsUpdate = true
                }
                window.modelMaterials.push(material)
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

function animate() {

    requestAnimationFrame(animate)

    controls.update()

    renderer.render(scene, camera)
    // cubeCamera.update(renderer, scene)
}

animate()