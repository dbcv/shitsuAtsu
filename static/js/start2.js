const fileInput = document.getElementById('file-input');
const uploadForm = document.getElementById('upload-form');
const loadingSpinner = document.getElementById('loading-spinner');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

document.querySelector("button.start-go").addEventListener("click", () => {
    fileInput.setAttribute("capture", "environment");
    fileInput.click();
});
document.querySelector("button.start-device").addEventListener("click", () => {
    fileInput.removeAttribute("capture");
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) {
        return;
    }

    const formData = new FormData();
    formData.append('image', file);

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