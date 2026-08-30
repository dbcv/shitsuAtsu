document.addEventListener('DOMContentLoaded', () => {
  const trigger = document.getElementById('forgot-password-trigger');
  const dialog = document.getElementById('forgot-password-dialog');
  const closeBtn = document.getElementById('close-dialog-btn');
  const closeIconBtn = document.getElementById('close-dialog-icon-btn');

  if (trigger && dialog) {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      dialog.showModal();
    });
  }

  const closeDialog = () => {
    if (dialog && dialog.open) {
      dialog.close();
    }
  };

  if (closeBtn) closeBtn.addEventListener('click', closeDialog);
  if (closeIconBtn) closeIconBtn.addEventListener('click', closeDialog);

  if (dialog) {
    dialog.addEventListener('click', (e) => {
      const dialogCard = dialog.querySelector('.dialog-card');
      if (dialogCard && !dialogCard.contains(e.target)) {
        dialog.close();
      }
    });
  }
});
