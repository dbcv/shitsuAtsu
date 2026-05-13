let image = null;
let imageLoaded = false;
let imageScale = 1;
let imageX = 0;
let imageY = 0;

function loadImage(url) {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
        image = img;
        imageLoaded = true;
        setupImageInitialTransform();
        redraw();
    };
    img.onerror = () => console.error('画像を読み込めませんでした:', url);
    img.src = url;
}

function setupImageInitialTransform() {
    if (!image) return;

    const canvasW = canvas.width / dpr;
    const canvasH = canvas.height / dpr;
    const imgRatio = image.width / image.height;
    const canvasRatio = canvasW / canvasH;

    if (imgRatio > canvasRatio) {
        imageScale = canvasW / image.width;
    } else {
        imageScale = canvasH / image.height;
    }

    const displayW = image.width * imageScale;
    const displayH = image.height * imageScale;
    imageX = (canvasW - displayW) / 2;
    imageY = (canvasH - displayH) / 2;
}

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const editSegmentedImageElement = document.getElementById('edit-segmented-image');
const saveSegmentedImageElement = document.getElementById('segmented-image-save');

const editPopover = document.getElementById('edit-popover2');
const saveButton = document.getElementById('save-button');
let lastResultBase64 = null;
const csrfToken = document.getElementById('csrf-token-input').value;


let dpr = window.devicePixelRatio || 1;

let points = [];
let positive_points = [];
let negative_points = [];
let tool = 'pen';
const brushRadius = 5;
let scale = 1.0;
let originX = 0;
let originY = 0;

const MIN_SCALE = 0.5;
const MAX_SCALE = 3.0;

let isPinching = false;
let pinchStartDist = 0;
let pinchStartScale = 1;
let pinchFocalUser = { x: 0, y: 0 };   // focal point in user (論理) coords
let pinchRect = null;                  // canvas rect at pinch start

function resizeCanvasForDisplay() {
    const rect = canvas.getBoundingClientRect();
    dpr = window.devicePixelRatio || 1;
    const displayW = Math.round(rect.width * dpr);
    const displayH = Math.round(rect.height * dpr);
    if (canvas.width !== displayW || canvas.height !== displayH) {
        canvas.width = displayW;
        canvas.height = displayH;
    }
    redraw();
}
window.addEventListener('resize', resizeCanvasForDisplay);

document.getElementById('p-pen').addEventListener('click', () => {
    tool = 'p-pen';
    document.getElementById('p-pen').classList.add("active");
    document.getElementById('n-pen').classList.remove("active");
    document.getElementById('eraser').classList.remove("active");
});
document.getElementById('n-pen').addEventListener('click', () => {
    tool = 'n-pen'
    document.getElementById('n-pen').classList.add("active");
    document.getElementById('p-pen').classList.remove("active");
    document.getElementById('eraser').classList.remove("active");
});
document.getElementById('eraser').addEventListener('click', () => {
    tool = 'eraser';
    document.getElementById('eraser').classList.add("active");
    document.getElementById('p-pen').classList.remove("active");
    document.getElementById('n-pen').classList.remove("active");
});

function getDistance(t1, t2) {
    const dx = t1.clientX - t2.clientX;
    const dy = t1.clientY - t2.clientY;
    return Math.hypot(dx, dy);
}
function getMidpoint(t1, t2, rect) {
    const mx = (t1.clientX + t2.clientX) / 2 - rect.left;
    const my = (t1.clientY + t2.clientY) / 2 - rect.top;
    return { x: mx, y: my };
}

function isPointOnImage(p) {
    if (!imageLoaded || !image) return false;

    const imgLeft = imageX;
    const imgTop = imageY;
    const imgRight = imageX + image.width * imageScale;
    const imgBottom = imageY + image.height * imageScale;

    return (
        p.x >= imgLeft &&
        p.x <= imgRight &&
        p.y >= imgTop &&
        p.y <= imgBottom
    );
}

function getPointOnImage(p) {
    if (!imageLoaded || !image) {
        console.warn("画像がまだ読み込まれていません。");
        return null;
    }

    const imgLeft = imageX;
    const imgTop = imageY;
    const imgRight = imageX + image.width * imageScale;
    const imgBottom = imageY + image.height * imageScale;

    if (p.x < imgLeft || p.x > imgRight || p.y < imgTop || p.y > imgBottom) {
        console.log("点は画像外です。");
        return null;
    }

    const relX = (p.x - imgLeft) / (image.width * imageScale);
    const relY = (p.y - imgTop) / (image.height * imageScale);

    const imgX = relX * image.width;
    const imgY = relY * image.height;

    console.log(`画像上の座標: (${imgX.toFixed(1)}, ${imgY.toFixed(1)})`);
    return { x: imgX, y: imgY };
}


function clientToUser(touch) {
    const rect = canvas.getBoundingClientRect();
    const cssX = touch.clientX - rect.left;
    const cssY = touch.clientY - rect.top;
    const userX = (cssX - originX) / scale;
    const userY = (cssY - originY) / scale;
    return { x: userX, y: userY };
}

let sendSam2Timeout = null;

function redraw() {
    if (sendSam2Timeout) {
        clearTimeout(sendSam2Timeout);
        sendSam2Timeout = null;
    }

    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.restore();

    ctx.setTransform(dpr * scale, 0, 0, dpr * scale, dpr * originX, dpr * originY);

    if (imageLoaded && image) {
        ctx.drawImage(
            image,
            imageX, imageY,
            image.width * imageScale,
            image.height * imageScale
        );
    }
    ctx.fillStyle = 'black';
    for (const p of positive_points) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, brushRadius, 0, Math.PI * 2);
        ctx.fillStyle = "blue";
        ctx.fill();
    }
    for (const p of negative_points) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, brushRadius, 0, Math.PI * 2);
        ctx.fillStyle = "red";
        ctx.fill();
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0);

    sendSam2Timeout = setTimeout(() => {
        let tmp_positive_points = positive_points.map(x => getPointOnImage(x))
        let tmp_negative_points = negative_points.map(x => getPointOnImage(x))
        const formData = new FormData();
        formData.append('photo_uuid', objectuuid);
        formData.append('ppoints', JSON.stringify(tmp_positive_points));
        formData.append('npoints', JSON.stringify(tmp_negative_points));

        fetch("/api/segment2/", {
            method: 'POST',
            body: formData,
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(data.image_base64)
                    editSegmentedImageElement.src = `data:image/png;base64,${data.image_base64}`;
                    saveSegmentedImageElement.src = `data:image/png;base64,${data.crop}`;
                    lastResultBase64 = `data:image/png;base64,${data.crop}`;
                    editPopover.showPopover()
                } else {
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }, 1000)
}

let singleTouchTimeout = null;

canvas.addEventListener('touchstart', (e) => {

    e.preventDefault();

    if (e.touches.length === 1) {
        // 一旦保留
        const touch = e.touches[0];
        singleTouchTimeout = setTimeout(() => {

            if (tool === 'p-pen') {
                const p = clientToUser(touch);
                if (isPointOnImage(p)) {
                    positive_points.push(p);
                    getPointOnImage(p);
                    redraw();
                }
            } else if (tool === 'n-pen') {
                const p = clientToUser(touch);
                if (isPointOnImage(p)) {
                    negative_points.push(p);
                    getPointOnImage(p);
                    redraw();
                }
            }
            else if (tool === 'eraser') {
                const p = clientToUser(touch);
                if (isPointOnImage(p)) {
                    positive_points = positive_points.filter(pt => {
                        const dx = pt.x - p.x;
                        const dy = pt.y - p.y;
                        return dx * dx + dy * dy > (brushRadius + 5) ** 2;
                    });
                    negative_points = negative_points.filter(pt => {
                        const dx = pt.x - p.x;
                        const dy = pt.y - p.y;
                        return dx * dx + dy * dy > (brushRadius + 5) ** 2;
                    });
                    redraw();
                }
            }
            singleTouchTimeout = null;
        }, 30); // ←ここを調整（80〜120msが自然）
    } else if (e.touches.length === 2) {
        // ピンチ開始時に1本指待機をキャンセル
        if (singleTouchTimeout) {
            clearTimeout(singleTouchTimeout);
            singleTouchTimeout = null;
        }

        // （ここからピンチ処理）
        isPinching = true;
        pinchStartDist = getDistance(e.touches[0], e.touches[1]);
        pinchStartScale = scale;
        pinchRect = canvas.getBoundingClientRect();
        const mid = getMidpoint(e.touches[0], e.touches[1], pinchRect);
        pinchFocalUser.x = (mid.x - originX) / scale;
        pinchFocalUser.y = (mid.y - originY) / scale;
    }
});

// touchmove: ピンチ中はズーム（かつ2本指の中点移動＝パン）
// 要件により1本指moveは無視（何もしない）
canvas.addEventListener('touchmove', (e) => {
    e.preventDefault();

    if (!isPinching || e.touches.length < 2) return;

    // current midpoint & distance (CSS coords)
    const rect = pinchRect || canvas.getBoundingClientRect();
    const newMid = getMidpoint(e.touches[0], e.touches[1], rect);
    const newDist = getDistance(e.touches[0], e.touches[1]);

    // scale の更新（相対変化）
    if (pinchStartDist > 0) {
        const newScaleUnclamped = pinchStartScale * (newDist / pinchStartDist);
        const newScale = Math.min(Math.max(newScaleUnclamped, MIN_SCALE), MAX_SCALE);

        // focalUser は pinch 開始時に計算済み：その user-space 座標が、
        // newMid (CSS) に見えるように origin を設定する：
        // newOrigin = newMidCss - focalUser * newScale
        const newOriginX = newMid.x - pinchFocalUser.x * newScale;
        const newOriginY = newMid.y - pinchFocalUser.y * newScale;

        // 適用
        scale = newScale;
        originX = newOriginX;
        originY = newOriginY;
        redraw();
    }
});

canvas.addEventListener('touchend', (e) => {
    // 指が減ったときに1本指待機が残っていたら消す
    if (singleTouchTimeout) {
        clearTimeout(singleTouchTimeout);
        singleTouchTimeout = null;
    }
    if (e.touches.length < 2) {
        isPinching = false;
    }
});

// 初期化
resizeCanvasForDisplay();
loadImage(imageURL);

saveButton.addEventListener('click', () => {

    saveButton.disabled = true;
    saveButton.textContent = '保存中...';

    const formData = new FormData();
    formData.append('photo_uuid', objectuuid);
    formData.append('image_base64', lastResultBase64);

    fetch(api_save_segment_URL, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                saveButton.textContent = '保存済み';
                saveButton.style.display = "none";
                location.href = `/gallery3`;
            } else {
                alert('保存に失敗しました: ' + data.error);
                saveButton.disabled = false;
                saveButton.textContent = '確定して次へ';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('保存処理中に通信エラーが発生しました。');
            saveButton.disabled = false;
            saveButton.textContent = '確定して次へ';
        });
});