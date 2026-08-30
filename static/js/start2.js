const fileInput = document.getElementById('file-input');
const uploadForm = document.getElementById('upload-form');
const loadingSpinner = document.getElementById('loading-spinner');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

document.querySelector("button.start-go").addEventListener("click", () => {
    const description = document.getElementById('description-input') ? document.getElementById('description-input').value.trim() : '';
    if (!description) {
        alert('撮影対象物の詳細を入力してください。');
        return;
    }
    fileInput.setAttribute("capture", "environment");
    fileInput.click();
});
document.querySelector("button.start-device").addEventListener("click", () => {
    const description = document.getElementById('description-input') ? document.getElementById('description-input').value.trim() : '';
    if (!description) {
        alert('撮影対象物の詳細を入力してください。');
        return;
    }
    fileInput.removeAttribute("capture");
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    const description = document.getElementById('description-input') ? document.getElementById('description-input').value : '';

    if (!file) {
        return;
    }

    const formData = new FormData();
    formData.append('image', file);
    formData.append('description', description);

    loadingSpinner.style.display = 'flex';
    loadingSpinner.showPopover()

    fetch(uploadURL, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
        body: formData,
    })
        .then(response => response.json())
        .then(data => {

            if (data.success && data.segment_url) {
                window.location.href = data.segment_url;
            } else {
                alert(`エラーが発生しました: ${data.error}`);
                loadingSpinner.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('アップロード中に通信エラーが発生しました。');
            loadingSpinner.style.display = 'none';
        });

    uploadForm.reset();
});

const content = document.getElementById("start-caution");

function centerContent() {
    if (!content) return;

    // ポップオーバーが開いていないときは何もしない
    if (!content.matches(':popover-open')) {
        return;
    }

    if (window.visualViewport) {
        const vv = window.visualViewport;
        const viewportHeight = vv.height;
        const windowHeight = window.innerHeight;

        // 仮想キーボード等で visualViewport が大幅に縮小している場合 (innerHeight の 85% 未満)
        if (viewportHeight < windowHeight * 0.85) {
            const contentHeight = content.offsetHeight;
            const top = vv.offsetTop + Math.max(10, (viewportHeight - contentHeight) / 2);
            content.style.top = `${top}px`;
            content.style.bottom = 'auto';
            content.style.margin = '0 auto';
        } else {
            // 通常時: Popover API 標準の画面中央配置 (inset: 0; margin: auto) に委ねる
            content.style.top = '';
            content.style.bottom = '';
            content.style.margin = '';
        }
    }
}

document.querySelector("button#start-goto-content02")?.addEventListener("click", () => {
    document.getElementById("start-caution-content01").style.display = "none";
    document.getElementById("start-caution-content02").style.display = "flex";
    requestAnimationFrame(centerContent);
});

document.querySelector("button.startButton")?.addEventListener("click", () => {
    document.getElementById("start-caution-content01").style.display = "flex";
    document.getElementById("start-caution-content02").style.display = "none";
    requestAnimationFrame(centerContent);
});

if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", centerContent);
    window.visualViewport.addEventListener("scroll", centerContent);
}

if (content) {
    content.addEventListener("toggle", (event) => {
        if (event.newState === "open") {
            requestAnimationFrame(centerContent);
        } else {
            content.style.top = '';
            content.style.bottom = '';
            content.style.margin = '';
        }
    });
}