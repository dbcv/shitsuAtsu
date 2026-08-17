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

document.querySelector("button#start-goto-content02").addEventListener("click", () => {
    document.getElementById("start-caution-content01").style.display = "none";
    document.getElementById("start-caution-content02").style.display = "flex";
});

document.querySelector("button.startButton").addEventListener("click", () => {
    document.getElementById("start-caution-content01").style.display = "flex";
    document.getElementById("start-caution-content02").style.display = "none";
});

const content = document.getElementById("start-caution");

function centerContent() {
  const viewportHeight = window.visualViewport.height;
  const contentHeight = content.offsetHeight;
  const windowHeight = window.innerHeight;
  //console.log(`Viewport height: ${viewportHeight}, Content height: ${contentHeight}, Window height: ${windowHeight}`);
  const top = (viewportHeight - contentHeight) / 2;
  if (viewportHeight == windowHeight) {
    content.style.top = `0px`;
  } else {
    content.style.top = `${top}px`;
  }
}

window.visualViewport.addEventListener("resize", centerContent);
window.visualViewport.addEventListener("scroll", centerContent);

centerContent();