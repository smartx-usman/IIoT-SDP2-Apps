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

    // User Registration Form submission handler
    document.getElementById('user-registration-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch('/register', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showAlert(data.status, data.message);
        })
        .catch(error => {
            showAlert('error', 'An error occurred while registering new user.');
        });
    });

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

// Fetch deployed workloads via an AJAX call
function fetchDeployedWorkloads() {
    fetch('/deployed_workloads')
        .then(response => response.json())
        .then(data => {
            var workloadList = document.getElementById('workload-list');
            workloadList.innerHTML = "";  // Clear previous contents

            // If there are workloads, display them
            if (data.length > 0) {
                var table = document.createElement('table');
                var header = table.createTHead();
                var headerRow = header.insertRow(0);
                headerRow.insertCell(0).innerHTML = "Workload Name";
                headerRow.insertCell(1).innerHTML = "Duration";
                headerRow.insertCell(2).innerHTML = "Replicas";
                headerRow.insertCell(3).innerHTML = "Node";
                headerRow.insertCell(4).innerHTML = "Status";
                headerRow.insertCell(5).innerHTML = "Deployed By";
                headerRow.insertCell(6).innerHTML = "Created At";

                var body = table.createTBody();
                data.forEach(workload => {
                    var row = body.insertRow();
                    row.insertCell(0).innerHTML = workload.workload_name;
                    row.insertCell(1).innerHTML = workload.duration;
                    row.insertCell(2).innerHTML = workload.replicas;
                    row.insertCell(3).innerHTML = workload.node_name;
                    row.insertCell(4).innerHTML = workload.status;
                    row.insertCell(5).innerHTML = workload.username;
                    row.insertCell(6).innerHTML = workload.created_at;
                });

                workloadList.appendChild(table);
            } else {
                workloadList.innerHTML = "<p>No workloads deployed yet.</p>";
            }
        })
        .catch(error => {
            console.error("Error fetching deployed workloads:", error);
        });
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });

    const section = document.getElementById(sectionId);
    if (section) {
        if (sectionId === 'listWorkload') {
            fetchDeployedWorkloads();
        }
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
