// Validate workload name field
function validateWorkloadName(input) {
    const errorElement = document.getElementById('nameError');
    const pattern = new RegExp(input.pattern);

    // Reset previous states
    input.setCustomValidity('');
    errorElement.textContent = '';
    input.classList.remove('is-invalid');

    if (!input.checkValidity()) {
        let message = input.title;
        if (!pattern.test(input.value)) {
            message = "Invalid characters detected. Only use A-Z, a-z, 0-9, _, -";
        }
        input.setCustomValidity(message);
        input.classList.add('is-invalid');
        errorElement.textContent = message;
    }
}

// Validate CPU input to ensure it ends with 'm'
function validateCpu(input) {
  const value = input.value.trim();
  if (value && !value.endsWith('m')) {
    input.setCustomValidity('CPU value must end with "m" (e.g., 100m)');
  } else {
    input.setCustomValidity('');
  }
}

// Validate memory input to ensure it ends with 'M' or 'G'
function validateMemory(input) {
  const value = input.value.trim();
  if (value && !(value.endsWith('Mi') || value.endsWith('Gi'))) {
    input.setCustomValidity('Memory value must end with "Mi" or "Gi" (e.g., 256Mi)');
  } else {
    input.setCustomValidity('');
  }
}