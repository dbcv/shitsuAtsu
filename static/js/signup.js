document.addEventListener('DOMContentLoaded', () => {
  const formSteps = document.querySelectorAll('.form-step');
  const stepItems = document.querySelectorAll('.step-item');
  const stepLines = document.querySelectorAll('.step-line');
  const signupForm = document.querySelector('#signup-form form');
  let currentStep = 1;

  function showStep(stepNumber) {
    formSteps.forEach(step => {
      if (parseInt(step.dataset.step, 10) === stepNumber) {
        step.classList.add('active');
        const firstInput = step.querySelector('input:not([type="checkbox"]):not([type="hidden"])');
        if (firstInput) firstInput.focus();
      } else {
        step.classList.remove('active');
      }
    });

    stepItems.forEach(item => {
      const stepIdx = parseInt(item.dataset.step, 10);
      if (stepIdx === stepNumber) {
        item.classList.add('active');
        item.classList.remove('completed');
      } else if (stepIdx < stepNumber) {
        item.classList.remove('active');
        item.classList.add('completed');
      } else {
        item.classList.remove('active', 'completed');
      }
    });

    stepLines.forEach(line => {
      const lineIdx = parseInt(line.dataset.line, 10);
      if (lineIdx < stepNumber) {
        line.classList.add('active');
      } else {
        line.classList.remove('active');
      }
    });

    currentStep = stepNumber;
  }

  function validateStep(stepNumber) {
    const currentStepEl = document.querySelector(`.form-step[data-step="${stepNumber}"]`);
    if (!currentStepEl) return true;

    if (stepNumber === 2) {
      const pass = document.getElementById('id_password');
      const passConfirm = document.getElementById('id_password_confirm');
      if (pass && passConfirm && pass.value !== passConfirm.value) {
        passConfirm.setCustomValidity('パスワードが一致しません');
        passConfirm.reportValidity();
        return false;
      } else if (passConfirm) {
        passConfirm.setCustomValidity('');
      }
    }

    const requiredInputs = currentStepEl.querySelectorAll('input[required]');
    for (let input of requiredInputs) {
      if (!input.checkValidity()) {
        input.reportValidity();
        return false;
      }
    }

    return true;
  }

  document.querySelectorAll('.btn-next').forEach(btn => {
    btn.addEventListener('click', () => {
      if (validateStep(currentStep)) {
        showStep(currentStep + 1);
      }
    });
  });

  document.querySelectorAll('.btn-prev').forEach(btn => {
    btn.addEventListener('click', () => {
      showStep(currentStep - 1);
    });
  });

  if (signupForm) {
    signupForm.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && currentStep < 3) {
        e.preventDefault();
        const nextBtn = document.querySelector(`.form-step[data-step="${currentStep}"] .btn-next`);
        if (nextBtn) nextBtn.click();
      }
    });
  }

  document.querySelectorAll('.password-toggle-check').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const wrapper = e.target.closest('.password-wrapper');
      const passwordInput = wrapper ? wrapper.querySelector('input[type="password"], input[type="text"]') : null;
      if (passwordInput) {
        passwordInput.type = e.target.checked ? 'text' : 'password';
      }
    });
  });
});
