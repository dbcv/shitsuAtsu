const size = 400;

//========================================
// Canvas
//========================================

const circle = document.getElementById("circle");
circle.style.position = "relative";

const canvas = document.createElement("canvas");
canvas.width = size;
canvas.height = size;


const markerCanvas = document.createElement("canvas");
markerCanvas.width = size;
markerCanvas.height = size;
markerCanvas.style.position = "absolute";
markerCanvas.style.left = "0";
markerCanvas.style.top = "0";
markerCanvas.style.pointerEvents = "none";

circle.appendChild(canvas);
circle.appendChild(markerCanvas);

const ctx = canvas.getContext("2d");
const markerCtx = markerCanvas.getContext("2d");

//========================================
// State
//========================================

const preview = document.getElementById("preview");

let dragging = false;

let L = 70;
let currentA = 0;
let currentB = 0;

let markerX = size / 2;
let markerY = size / 2;

//========================================
// Marker
//========================================

function drawMarker() {

    markerCtx.clearRect(0, 0, size, size);

    // 外側（黒）
    markerCtx.strokeStyle = "black";
    markerCtx.lineWidth = 4;

    markerCtx.beginPath();
    markerCtx.moveTo(markerX - 10, markerY);
    markerCtx.lineTo(markerX + 10, markerY);
    markerCtx.moveTo(markerX, markerY - 10);
    markerCtx.lineTo(markerX, markerY + 10);
    markerCtx.stroke();

    markerCtx.beginPath();
    markerCtx.arc(markerX, markerY, 8, 0, Math.PI * 2);
    markerCtx.stroke();

    // 内側（白）
    markerCtx.strokeStyle = "white";
    markerCtx.lineWidth = 2;

    markerCtx.beginPath();
    markerCtx.moveTo(markerX - 10, markerY);
    markerCtx.lineTo(markerX + 10, markerY);
    markerCtx.moveTo(markerX, markerY - 10);
    markerCtx.lineTo(markerX, markerY + 10);
    markerCtx.stroke();

    markerCtx.beginPath();
    markerCtx.arc(markerX, markerY, 8, 0, Math.PI * 2);
    markerCtx.stroke();
}

//========================================
// Color Update
//========================================

function updateColor(event) {

    const rect = circle.getBoundingClientRect();

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const x = event.clientX - centerX;
    const y = centerY - event.clientY;

    const radius = rect.width / 2;

    if (x * x + y * y > radius * radius) {
        return;
    }

    const a = x / radius * 128;
    const b = y / radius * 128;

    currentA = a;
    currentB = b;

    markerX = event.clientX - rect.left;
    markerY = event.clientY - rect.top;

    drawMarker();

    preview.style.backgroundColor = `lab(${L}% ${a} ${b})`;
    preview.querySelector("span").style.color = `lab(${L}% ${a} ${b})`;

    const rgb = labToRgb(L, a, b);

    window.modelMaterials.forEach(material => {
        material.color.set(rgb.hex);
    });
}

function updateL(value) {

    L = Number(value);

    preview.style.backgroundColor = `lab(${L}% ${currentA} ${currentB})`;
    preview.querySelector("span").style.color = `lab(${L}% ${currentA} ${currentB})`;

    const rgb = labToRgb(L, currentA, currentB);

    window.modelMaterials.forEach(material => {
        material.color.set(rgb.hex);
    });

    drawLabCircle(L);
    drawMarker();
}

//========================================
// Pointer Events
//========================================

circle.addEventListener("pointerdown", event => {

    dragging = true;
    updateColor(event);

    circle.setPointerCapture(event.pointerId);

});

circle.addEventListener("pointermove", event => {

    if (!dragging) return;

    updateColor(event);

});

circle.addEventListener("pointerup", event => {

    dragging = false;
    circle.releasePointerCapture(event.pointerId);

});

circle.addEventListener("pointercancel", () => {

    dragging = false;

});

//========================================
// Sliders
//========================================

document.getElementById("roughness").addEventListener("input", event => {

    const value = Number(event.target.value);

    window.modelMaterials.forEach(material => {
        material.roughness = value;
    });

});

document.getElementById("metalness").addEventListener("input", event => {

    const value = Number(event.target.value);

    window.modelMaterials.forEach(material => {
        material.metalness = value;
    });

});

document.getElementById("L-slider").addEventListener("input", event => {

    updateL(event.target.value);

});

//========================================
// Draw LAB Circle
//========================================

function drawLabCircle(L) {

    const img = ctx.createImageData(size, size);

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2;

    const scale = 128 / radius;

    for (let y = 0; y < size; y++) {

        for (let x = 0; x < size; x++) {

            const dx = x - cx;
            const dy = y - cy;

            if (dx * dx + dy * dy > radius * radius) {
                continue;
            }

            const a = dx * scale;
            const b = -dy * scale;

            const rgb = labToRgb(L, a, b);

            const i = (y * size + x) * 4;

            img.data[i] = rgb.r;
            img.data[i + 1] = rgb.g;
            img.data[i + 2] = rgb.b;
            img.data[i + 3] = 255;

        }

    }

    ctx.putImageData(img, 0, 0);

}

//========================================
// LAB → RGB
//========================================

function labToRgb(L, a, b) {

    let y = (L + 16) / 116;
    let x = a / 500 + y;
    let z = y - b / 200;

    const epsilon = 0.008856;
    const kappa = 903.29;

    const x3 = x * x * x;
    const y3 = y * y * y;
    const z3 = z * z * z;

    let X = x3 > epsilon ? x3 : (x - 16 / 116) / 7.787;
    let Y = y3 > epsilon ? y3 : (L - 16) / kappa;
    let Z = z3 > epsilon ? z3 : (z - 16 / 116) / 7.787;

    X *= 95.047;
    Y *= 100.000;
    Z *= 108.883;

    X /= 100;
    Y /= 100;
    Z /= 100;

    let r = X * 3.2406 + Y * -1.5372 + Z * -0.4986;
    let g = X * -0.9689 + Y * 1.8758 + Z * 0.0415;
    let bl = X * 0.0557 + Y * -0.2040 + Z * 1.0570;

    r = r > 0.0031308 ? 1.055 * Math.pow(r, 1 / 2.4) - 0.055 : r * 12.92;
    g = g > 0.0031308 ? 1.055 * Math.pow(g, 1 / 2.4) - 0.055 : g * 12.92;
    bl = bl > 0.0031308 ? 1.055 * Math.pow(bl, 1 / 2.4) - 0.055 : bl * 12.92;

    const R = Math.max(0, Math.min(255, Math.round(r * 255)));
    const G = Math.max(0, Math.min(255, Math.round(g * 255)));
    const B = Math.max(0, Math.min(255, Math.round(bl * 255)));

    return {
        r: R,
        g: G,
        b: B,
        hex:
            "#" +
            R.toString(16).padStart(2, "0") +
            G.toString(16).padStart(2, "0") +
            B.toString(16).padStart(2, "0")
    };

}

//========================================
// Initial Draw
//========================================

drawLabCircle(L);
drawMarker();