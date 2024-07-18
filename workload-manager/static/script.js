document.addEventListener('DOMContentLoaded', function() {
    // Fetch nodes and populate node dropdowns
    fetch('/nodes')
        .then(response => response.json())
        .then(data => {
            const nodes = data.nodes;
            const nodeSelects = document.getElementsByClassName('node_name');
            for (let select of nodeSelects) {
                for (let node of nodes) {
                    const option = document.createElement('option');
                    option.value = node;
                    option.text = node;
                    select.add(option);
                }
            }
        })
        .catch(error => console.error('Error fetching nodes:', error));

    // Fetch workload types and populate workload type dropdowns
    fetch('/workload_types')
        .then(response => response.json())
        .then(data => {
            const types = data.types;
            const workloadTypeSelects = document.getElementsByClassName('workload_type');
            for (let select of workloadTypeSelects) {
                for (let type of types) {
                    const option = document.createElement('option');
                    option.value = type.workload_key;
                    option.text = type.workload_display_name;
                    select.add(option);
                }
            }
        })
        .catch(error => console.error('Error fetching workload types:', error));

    // Monitoring system deployment Form submission handler
    document.getElementById('monitoring-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch('/monitoring', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showAlert(data.status, data.message);
        })
        .catch(error => {
            showAlert('error', 'An error occurred while submitting the workload.');
        });
    });

    // Form submission handler
    document.getElementById('workload-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch('/submit', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showAlert(data.status, data.message);
        })
        .catch(error => {
            showAlert('error', 'An error occurred while submitting the workload.');
        });
    });

    // Add new workload section handler
    document.getElementById('addWorkloadBtn').addEventListener('click', function() {
        const workloadDiv = document.createElement('div');
        workloadDiv.innerHTML = `
            <div class="form-group">
                <label for="workload_type">Workload Type:</label>
                <select name="workload_type[]" class="form-control workload_type" required></select>
            </div>
            <div class="form-group">
                <label for="duration">Duration (seconds):</label>
                <input type="number" name="duration[]" class="form-control duration" min="1" value="120" required>
            </div>
            <div class="form-group">
                <label for="replicas">Replicas:</label>
                <input type="number" name="replicas[]" class="form-control replicas" min="1" value="1" required>
            </div>
            <div class="form-group">
                <label for="node_name">Node:</label>
                <select name="node_name[]" class="form-control node_name" required>
                    <option value="any">Any</option>
                </select>
            </div>
            <button type="button" class="btn btn-danger" onclick="removeWorkload(this)">Remove</button>
            <hr>
        `;
        document.getElementById('workloads').appendChild(workloadDiv);

        // Fetch workload types for the new section
        fetch('/workload_types')
            .then(response => response.json())
            .then(data => {
                const types = data.types;
                const workloadTypeSelects = workloadDiv.getElementsByClassName('workload_type');
                for (let select of workloadTypeSelects) {
                    for (let type of types) {
                        const option = document.createElement('option');
                        option.value = type.workload_key;
                        option.text = type.workload_display_name;
                        select.add(option);
                    }
                }
            })
            .catch(error => console.error('Error fetching workload types:', error));

        // Fetch nodes for the new section
        fetch('/nodes')
            .then(response => response.json())
            .then(data => {
                const nodes = data.nodes;
                const nodeSelects = workloadDiv.getElementsByClassName('node_name');
                for (let select of nodeSelects) {
                    for (let node of nodes) {
                        const option = document.createElement('option');
                        option.value = node;
                        option.text = node;
                        select.add(option);
                    }
                }
            })
            .catch(error => console.error('Error fetching nodes:', error));
    });

    // Handle adding workload type form submission
    document.getElementById('workload-type-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const workloadKey = document.getElementById('workloadKey').value;
        const workloadDisplayName = document.getElementById('workloadDisplayName').value;
        const workloadEnabled = document.getElementById('workloadEnabled').value;
        const files = document.getElementById('workloadYaml').files;

        if (!files.length > 0) {
            showAlert('error', 'Please upload a YAML file.');
            return;
        }

        const formData = new FormData();
        formData.append('workload_key', workloadKey);
        formData.append('workload_display_name', workloadDisplayName);
        formData.append('workload_enabled', workloadEnabled);

        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        fetch('/add_workload_type', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showAlert(data.status, data.message);
        })
        .catch(error => {
            showAlert('error', 'An error occurred while adding the workload type.');
        });
    });

    // Handle menu item clicks and section display
    const menuItems = document.querySelectorAll('#left-panel .menu-item');
    for (let menuItem of menuItems) {
        menuItem.addEventListener('click', function() {
            sessionStorage.setItem('currentSection', this.getAttribute('onclick').match(/'([^']+)'/)[1]);
        });
    }

    const currentSection = sessionStorage.getItem('currentSection');
    if (currentSection) {
        showSection(currentSection);
    } else {
        showSection('createWorkload');
    }
});

function removeWorkload(button) {
    button.closest('div').remove();
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
    } else {
        console.error(`No section found with id: ${sectionId}`);
    }
}

function showAlert(type, message) {
    const successAlert = document.getElementById('alert-success');
    const errorAlert = document.getElementById('alert-error');
    if (type === 'success') {
        successAlert.textContent = message;
        successAlert.style.display = 'block';
        errorAlert.style.display = 'none';
    } else {
        errorAlert.textContent = message;
        errorAlert.style.display = 'block';
        successAlert.style.display = 'none';
    }
    setTimeout(() => {
        successAlert.style.display = 'none';
        errorAlert.style.display = 'none';
    }, 5000);
}
