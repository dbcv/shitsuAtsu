const circle = document.getElementById("circle");
const preview = document.getElementById("preview");

let dragging = false;
let L = 70;
let currentA = 0;
let currentB = 0;

function updateColor(event) {
    const rect = circle.getBoundingClientRect();

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const x = event.clientX - centerX;
    const y = centerY - event.clientY;

    const r = Math.sqrt(x * x + y * y);
    const radius = rect.width / 2;

    // 円外なら無視
    if (r > radius) {
        return;
    }

    const thetaRad = Math.atan2(y, x);
    let thetaDeg = thetaRad * 180 / Math.PI;

    if (thetaDeg < 0) {
        thetaDeg += 360;
    }

    const a = (x / radius) * 128;
    const b = (y / radius) * 128;

    currentA = a;
    currentB = b;

    console.log({
        x,
        y,
        r,
        thetaDeg,
        a,
        b
    });

    preview.style.backgroundColor = `lab(${L}% ${a} ${b})`;
    const rgb = labToRgb(L, a, b);
    window.modelMaterials.forEach((material) => {
        material.color.set(rgb.hex)
    })
}

function updateL(value) {
    L = Number(value);
    console.log(L);
    preview.style.backgroundColor = `lab(${L}% ${currentA} ${currentB})`;
    const rgb = labToRgb(L, currentA, currentB);
    window.modelMaterials.forEach((material) => {
        material.color.set(rgb.hex)
    })
}

// 押し始め
circle.addEventListener("pointerdown", (event) => {
    dragging = true;
    updateColor(event);

    // ポインタを捕捉
    circle.setPointerCapture(event.pointerId);
});

// 移動中
circle.addEventListener("pointermove", (event) => {
    if (!dragging) {
        return;
    }

    updateColor(event);
});

// 離した
circle.addEventListener("pointerup", () => {
    dragging = false;
});

// キャンセル
circle.addEventListener("pointercancel", () => {
    dragging = false;
});

function labToRgb(L, a, b) {
    // 1. LAB から XYZ への変換 (D65基準)
    let y = (L + 16) / 116;
    let x = a / 500 + y;
    let z = y - b / 200;

    const epsilon = 0.008856;
    const kappa = 903.29;

    let x3 = x * x * x;
    let y3 = y * y * y;
    let z3 = z * z * z;

    let X = x3 > epsilon ? x3 : (x - 16 / 116) / 7.787;
    let Y = y3 > epsilon ? y3 : (L - 16) / kappa;
    let Z = z3 > epsilon ? z3 : (z - 16 / 116) / 7.787;

    // D65 における三刺激値の基準値
    X *= 95.047;
    Y *= 100.000;
    Z *= 108.883;

    // 2. XYZ から Linear RGB への変換
    X /= 100;
    Y /= 100;
    Z /= 100;

    let r = X * 3.2406 + Y * -1.5372 + Z * -0.4986;
    let g = X * -0.9689 + Y * 1.8758 + Z * 0.0415;
    let bl = X * 0.0557 + Y * -0.2040 + Z * 1.0570;

    // 3. ガンマ補正 (sRGB空間へ)
    r = r > 0.0031308 ? 1.055 * Math.pow(r, 1 / 2.4) - 0.055 : r * 12.92;
    g = g > 0.0031308 ? 1.055 * Math.pow(g, 1 / 2.4) - 0.055 : g * 12.92;
    bl = bl > 0.0031308 ? 1.055 * Math.pow(bl, 1 / 2.4) - 0.055 : bl * 12.92;

    const R = Math.max(0, Math.min(255, Math.round(r * 255)));
    const G = Math.max(0, Math.min(255, Math.round(g * 255)));
    const B = Math.max(0, Math.min(255, Math.round(bl * 255)));

    const hex =
        "#" +
        R.toString(16).padStart(2, "0") +
        G.toString(16).padStart(2, "0") +
        B.toString(16).padStart(2, "0");

    // 0〜255 の範囲にクランプして整数化
    return {
        r: R,
        g: G,
        b: B,
        hex: hex
    };
}

const roughnessSlider = document.getElementById("roughness");

roughnessSlider.addEventListener("input", (event) => {
    console.log(event.target.value);
    window.modelMaterials.forEach((material) => {
        material.roughness = event.target.value
    })
});

const metalnessSlider = document.getElementById("metalness");

metalnessSlider.addEventListener("input", (event) => {
    console.log(event.target.value);
    window.modelMaterials.forEach((material) => {
        material.metalness = event.target.value
    })
});

const LSlider = document.getElementById("L-slider");

LSlider.addEventListener("input", (event) => {
    L = Number(event.target.value);
    updateL(event.target.value);
    //drawLabCircle(L);
});

const size = 400;

const canvas = document.createElement("canvas");
canvas.width = size;
canvas.height = size;

document.getElementById("circle").appendChild(canvas);

const ctx = canvas.getContext("2d");
const img = ctx.createImageData(size, size);

function drawLabCircle(L) {
    

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2;

    for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {

            const dx = x - cx;
            const dy = y - cy;

            const r = Math.sqrt(dx * dx + dy * dy);

            if (r > radius) continue;

            const a = dx / radius * 128;
            const b = -dy / radius * 128;

            const rgb = labToRgb(L, a, b);

            const i = (y * size + x) * 4;

            img.data[i + 0] = rgb.r;
            img.data[i + 1] = rgb.g;
            img.data[i + 2] = rgb.b;
            img.data[i + 3] = 255;
        }
    }

    ctx.putImageData(img, 0, 0);
}

drawLabCircle(70);