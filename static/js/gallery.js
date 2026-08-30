document.addEventListener('DOMContentLoaded', () => {
    function updateGalleryTab() {
        const hash = window.location.hash;
        const isSegmented = (hash === '#segmented' || hash === '#segmented_photos');

        const originalsPane = document.getElementById('originals');
        const segmentedPane = document.getElementById('segmented');
        const originalBtn = document.getElementById('tab-btn-original');
        const segmentedBtn = document.getElementById('tab-btn-segmented');

        if (isSegmented) {
            if (originalsPane) originalsPane.classList.remove('active');
            if (segmentedPane) segmentedPane.classList.add('active');
            if (originalBtn) originalBtn.classList.remove('active');
            if (segmentedBtn) segmentedBtn.classList.add('active');
        } else {
            if (originalsPane) originalsPane.classList.add('active');
            if (segmentedPane) segmentedPane.classList.remove('active');
            if (originalBtn) originalBtn.classList.add('active');
            if (segmentedBtn) segmentedBtn.classList.remove('active');
        }
    }

    window.addEventListener('hashchange', updateGalleryTab);
    updateGalleryTab();

    const csrfTokenEl = document.getElementById('csrf-token-input');
    const deleteUrlEl = document.getElementById('delete-url-input');
    const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';
    const deleteUrl = deleteUrlEl ? deleteUrlEl.value : '';

    const modal = document.getElementById('image-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalPreviewImg = document.getElementById('modal-preview-img');
    const modalEditLink = document.getElementById('modal-edit-link');
    const modalDeleteBtn = document.getElementById('modal-delete-btn');
    const modalCloseIcon = document.getElementById('modal-close-icon');
    const modalCancelBtn = document.getElementById('modal-cancel-btn');

    const modalViewToggle = document.getElementById('modal-view-toggle');
    const toggleRenderedBtn = document.getElementById('toggle-rendered-btn');
    const toggleCutoutBtn = document.getElementById('toggle-cutout-btn');
    const modalParamInfo = document.getElementById('modal-param-info');
    const paramRoughness = document.getElementById('param-roughness');
    const paramMetalness = document.getElementById('param-metalness');
    const paramAlbedo = document.getElementById('param-albedo');
    const paramAlbedoSwatch = document.getElementById('param-albedo-swatch');

    let currentItem = {
        uuid: null,
        type: null,
        renderedUrl: null,
        cutoutUrl: null,
        hasRendered: false
    };

    function openModal(button) {
        currentItem.uuid = button.dataset.uuid;
        currentItem.type = button.dataset.type;
        currentItem.renderedUrl = button.dataset.renderedUrl || button.dataset.previewUrl;
        currentItem.cutoutUrl = button.dataset.cutoutUrl || button.dataset.previewUrl;
        currentItem.hasRendered = button.dataset.hasRendered === 'true';

        if (modalTitle) modalTitle.textContent = "";
        if (modalPreviewImg) {
            modalPreviewImg.src = button.dataset.previewUrl;
            modalPreviewImg.alt = button.dataset.title || 'プレビュー';
        }
        if (modalEditLink) {
            modalEditLink.href = button.dataset.editUrl;
        }

        if (currentItem.type === 'segmented') {
            if (currentItem.hasRendered) {
                if (modalViewToggle) modalViewToggle.style.display = 'flex';
                if (toggleRenderedBtn) toggleRenderedBtn.classList.add('active');
                if (toggleCutoutBtn) toggleCutoutBtn.classList.remove('active');
            } else {
                if (modalViewToggle) modalViewToggle.style.display = 'none';
            }

            if (button.dataset.roughness !== undefined) {
                if (modalParamInfo) modalParamInfo.style.display = 'flex';
                if (paramRoughness) paramRoughness.textContent = button.dataset.roughness;
                if (paramMetalness) paramMetalness.textContent = button.dataset.metalness;
                const albedoVal = button.dataset.albedo || '#FFFFFF';
                if (paramAlbedo) paramAlbedo.textContent = albedoVal;
                if (paramAlbedoSwatch) paramAlbedoSwatch.style.backgroundColor = albedoVal;
            } else {
                if (modalParamInfo) modalParamInfo.style.display = 'none';
            }
        } else {
            if (modalViewToggle) modalViewToggle.style.display = 'none';
            if (modalParamInfo) modalParamInfo.style.display = 'none';
        }

        if (modal && typeof modal.showModal === 'function') {
            modal.showModal();
        }
    }

    if (toggleRenderedBtn && toggleCutoutBtn) {
        toggleRenderedBtn.addEventListener('click', function () {
            toggleRenderedBtn.classList.add('active');
            toggleCutoutBtn.classList.remove('active');
            if (currentItem.renderedUrl && modalPreviewImg) {
                modalPreviewImg.src = currentItem.renderedUrl;
            }
        });

        toggleCutoutBtn.addEventListener('click', function () {
            toggleCutoutBtn.classList.add('active');
            toggleRenderedBtn.classList.remove('active');
            if (currentItem.cutoutUrl && modalPreviewImg) {
                modalPreviewImg.src = currentItem.cutoutUrl;
            }
        });
    }

    function closeModal() {
        if (modal && modal.open) {
            modal.close();
            if (modalPreviewImg) modalPreviewImg.src = '';
        }
    }

    const tabContent = document.querySelector('.tab-content');
    if (tabContent) {
        tabContent.addEventListener('click', function (event) {
            const itemBtn = event.target.closest('.gallery-item-btn');
            if (itemBtn) {
                openModal(itemBtn);
            }
        });
    }

    if (modalCloseIcon) modalCloseIcon.addEventListener('click', closeModal);
    if (modalCancelBtn) modalCancelBtn.addEventListener('click', closeModal);

    if (modal) {
        modal.addEventListener('click', function (event) {
            if (event.target === modal) {
                closeModal();
            }
        });
    }

    // 削除処理
    if (modalDeleteBtn) {
        modalDeleteBtn.addEventListener('click', function () {
            if (!currentItem.uuid || !currentItem.type) return;

            if (confirm('この画像を本当に削除しますか？この操作は元に戻せません。')) {
                const formData = new FormData();
                formData.append('uuid', currentItem.uuid);
                formData.append('type', currentItem.type);

                modalDeleteBtn.disabled = true;

                const targetUrl = deleteUrl || "/api/delete_image/";

                fetch(targetUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const imageElement = document.getElementById(`photo-${currentItem.uuid}`);
                            if (imageElement) {
                                imageElement.remove();
                            }
                            closeModal();
                        } else {
                            alert('削除に失敗しました: ' + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('削除処理中に通信エラーが発生しました。');
                    })
                    .finally(() => {
                        modalDeleteBtn.disabled = false;
                    });
            }
        });
    }
});
