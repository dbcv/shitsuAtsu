const size = 400;

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

const preview = document.getElementById("preview");

let dragging = false;

let L = 70;
let currentA = 0;
let currentB = 0;

let markerX = size / 2 - 100 ;
let markerY = size / 2;

function drawMarker() {

    markerCtx.clearRect(0, 0, size, size);

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

function rgbToLab(r, g, b) {
    r /= 255;
    g /= 255;
    b /= 255;

    // ガンマ補正
    r = r > 0.04045 ? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92;
    g = g > 0.04045 ? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92;
    b = b > 0.04045 ? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92;

    // sRGB  XYZ (D65)
    let X = r * 0.4124564 + g * 0.3575761 + b * 0.1804375;
    let Y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750;
    let Z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041;

    // D65ホワイトポイントで正規化
    X /= 0.95047;
    Y /= 1.00000;
    Z /= 1.08883;

    // XYZ CIELAB
    const epsilon = 0.00885645167; 
    const kappa = 7.78703703704;

    X = X > epsilon ? Math.cbrt(X) : (kappa * X) + (16 / 116);
    Y = Y > epsilon ? Math.cbrt(Y) : (kappa * Y) + (16 / 116);
    Z = Z > epsilon ? Math.cbrt(Z) : (kappa * Z) + (16 / 116);

    const resultL = (116 * Y) - 16;
    const resulta = 500 * (X - Y);
    const resultb = 200 * (Y - Z);

    return { L: resultL, a: resulta, b: resultb };
}


function initColorPicker(albedo) {
    console.log(`initColorPicker called with albedo: ${albedo}`); // albedo is a hex string like "#4b3c64"

    const initialLab = rgbToLab(
        parseInt(albedo.slice(1, 3), 16),
        parseInt(albedo.slice(3, 5), 16),
        parseInt(albedo.slice(5, 7), 16)
    );
    console.log(initialLab); // {L: 0.5101497862024686, a: 0.5939015573667994, b: -0.9494629242531027}

    L = initialLab.L;
    document.getElementById("L-slider").value = L;
    currentA = initialLab.a;
    currentB = initialLab.b;

    document.getElementById("color-picker").show()

    const rect = circle.getBoundingClientRect();
    const radius = rect.width / 2;

    console.log(`radius: ${radius}, currentA: ${currentA}, currentB: ${currentB}`);

    markerX = (currentA / 128) * radius + radius;
    markerY = radius - (currentB / 128) * radius;

    console.log(`markerX: ${markerX}, markerY: ${markerY}`);

    preview.style.backgroundColor = `lab(${L}% ${currentA} ${currentB})`;
    preview.querySelector("span").style.color = `lab(${L}% ${currentA} ${currentB})`;

    document.getElementById("roughness").value = window.modelMaterials[0].roughness;
    document.getElementById("metalness").value = window.modelMaterials[0].metalness;
    document.getElementById("L-slider").value = L;

    drawLabCircle(L);
    drawMarker();

    document.getElementById("color-picker").close()
    document.getElementById("gray-wall").style.display = "none";
}