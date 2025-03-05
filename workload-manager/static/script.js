document.addEventListener('DOMContentLoaded', function() {
    // Show active menu item
    const defaultSection = document.querySelector('.section:not([style*="none"])');
    if(defaultSection) {
        setActiveMenuItem(defaultSection.id);
    }

    // Show or hide fields based on user level and content generation method
    toggleConfigMethod();

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
            workloadTypes = data.types;
            const workloadTypeSelects = document.getElementsByClassName('workload_type');
            for (let select of workloadTypeSelects) {
                select.innerHTML = ''; // Clear existing options
                for (let type of workloadTypes) {
                    const option = document.createElement('option');
                    option.value = type.workload_name;
                    option.text = type.workload_name;
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
        const userNamespace = document.body.dataset.namespace;
        formData.append('namespace', userNamespace);
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
            <button type="button" id="addWorkloadBtn" class="btn btn-primary">Add More Workload</button>
            <hr>
        `;
        document.getElementById('workloads').appendChild(workloadDiv);

        // Fetch workload types for the new section
        const workloadTypeSelects = workloadDiv.getElementsByClassName('workload_type');
        for (let select of workloadTypeSelects) {
            for (let type of workloadTypes) {
                const option = document.createElement('option');
                option.value = type.workload_name;
                option.text = type.workload_name;
                select.add(option);
            }
        }

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

        // Add manual fields
        const fieldsToAdd = [
            'workloadDisplayName',
            'workloadEnabled',
            'deployMethod',
            'configMethod'
        ];

        // Get the form element
        const form = document.getElementById('workload-type-form');
        const formData = new FormData(form);

        fieldsToAdd.forEach(field => {
            const value = document.getElementById(field).value;
            if (value) formData.append(field, value);
        });

        const deploymentMethod = document.getElementById('deployMethod').value;

        if (deploymentMethod === 'yaml') {
            const configurationMethod = document.getElementById('configMethod').value;

            if (configurationMethod === 'upload') {
                const files = document.getElementById('workloadYaml').files;

                if (!files.length > 0) {
                    showAlert('error', 'Please upload a YAML file.');
                    return;
                }

                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i]);
                }
            }
            else if (configurationMethod === 'dynamic') {
                const resourceType = document.getElementById('resourceType').value;

                if (resourceType) formData.append('resourceType', resourceType);
            }
            else {
                showAlert('error', 'Select a configuration method (Dynamic or Upload)');
            }
        }
        else if (deploymentMethod === 'helm') {
            const helmChart = document.getElementById('helmChart').value;
            const helmVersion = document.getElementById('helmVersion').value;
            const helmRepo = document.getElementById('helmRepo').value;
            const helmValues = document.getElementById('helmValues').value;

            formData.append('helm_chart', helmChart);
            formData.append('helm_version', helmVersion);
            formData.append('helm_repo', helmRepo);
            formData.append('helm_values', helmValues);
        }
        else {
            showAlert('error', 'Select a deployment method (YAML or Helm)');
        }

        // Filter out empty fields
        const filteredData = new FormData();
        for (const [key, value] of formData.entries()) {
            // Check for empty strings, null, undefined, or empty files
            if ((typeof value === 'string' && value.trim() !== '') ||
                (value instanceof File && value.name && value.size > 0) ||
                (typeof value !== 'string' && value !== null && value !== undefined)) {
                filteredData.append(key, value);
            }
        }

        //console.log('Final FormData:');
        //for (const [key, value] of filteredData.entries()) {
        //    console.log(`${key}:`, value);
        //}

        /*try {
                const response = fetch("/add_workload_type", {
                method: 'POST',
                body: filteredData,
            });

            if (response.ok) {
              showAlert(data.status, data.message);
              // Reload the page to reflect new workload type
              location.reload();
            } else {
              console.error("Failed to add workload type");
            }
          } catch (error) {
            showAlert('error', 'An error occurred while adding the workload type.');
          }*/

        fetch('/add_workload_type', {
            method: 'POST',
            body: filteredData
        })
        .then(response => response.json())
        .then(data => {
            // After successfully adding a new workload type, refresh all the dropdowns for workload_types
            fetch('/workload_types')
              .then(response => response.json())
              .then(data => {
                workloadTypes = data.types;
                // Update ALL dropdowns
                const allDropdowns = document.querySelectorAll('.workload_type');
                allDropdowns.forEach(select => {
                  select.innerHTML = ''; // Clear existing options
                  workloadTypes.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.workload_name;
                    option.text = type.workload_name;
                    select.appendChild(option);
                  });
                });
              });

            showAlert(data.status, data.message);
            // Reload the page to reflect new workload type
            //location.reload();
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

let workloadTypes = []; // Global variable to store fetched types

function removeWorkload(button) {
    button.closest('div').remove();
}

// Update service fields based on service type
function updateServiceFields() {
    const resourceType = document.getElementById('resourceType').value;
    const serviceType = document.querySelector('[name="service_type"]').value;
    const serviceFieldsDiv = document.getElementById('serviceOptions');

    // Common fields for both ClusterIP and NodePort
    const commonFields = `
        <div class="form-group">
            <label>Port:</label>
            <input type="number" class="form-control" name="svcPort" required>
        </div>
        <div class="form-group">
            <label>Target Port:</label>
            <input type="number" class="form-control" name="targetPort" required>
        </div>
        <div class="form-group">
            <label>Protocol:</label>
            <select class="form-control" name="svcProtocol">
                <option value="TCP">TCP</option>
                <option value="UDP">UDP</option>
            </select>
        </div>
    `;

    let serviceSpecificFields = '';

    if (serviceType === 'NodePort') {
        serviceSpecificFields = `
            <div class="form-group">
                <label>Node Port:</label>
                <input type="number" class="form-control" name="nodePort" min="30000" max="32767">
            </div>
        `;
    }

    // Combine fields based on service type
    const html = serviceType ?
        commonFields + serviceSpecificFields :
        '<p>Select a service type to configure</p>';

    // Update the container and toggle visibility
    serviceFieldsDiv.innerHTML = html;
    serviceFieldsDiv.style.display = serviceType ? 'block' : 'none';

}

// Update form fields based on resource type and user level
function updateFormFields() {
    const resourceType = document.getElementById('resourceType').value;
    const userLevel = document.body.dataset.userLevel;
    const userNamespace = document.body.dataset.namespace;

    // Show/hide service section
    document.querySelector('.service-section').style.display =
        ['Deployment', 'StatefulSet', 'DaemonSet'].includes(resourceType) ? 'block' : 'none';

    // Get fields for current resource and user level
    const fields = FIELDS_CONFIG[resourceType][userLevel] || [];
    //console.log("Debug: Fields:", fields);
    //console.log("User Level:", userLevel);
    //document.getElementById('dynamicFields').style.display = 'none';

    // Generate HTML for fields
    const html = fields.map(field => `
            ${generateFieldInput(field, userLevel)}
    `).join('');

    //console.log("Debug: Final HTML:", html);
    document.getElementById('dynamicFields').innerHTML = html;
}

function generateFieldInput(field, userLevel) {
    //console.log("Debug: Generating field:", field, "and user level:", userLevel);
    const baseHtml = {
        image: '<div class="form-group" id="div_container_image"><label>Container Image:</label><input type="text" class="form-control" name="image" id="image" value="usman476/coap:latest" placeholder="Enter container info."></div>',
        command: '<div class="form-group" id="div_container_interpreter"><label>Command Interpreter:</label><input type="text" class="form-control" name="cmd_interpreter" id="cmd_interpreter" value="python3" placeholder="Enter command interpreter (e.g., shell)"></div>',
        args: '<div class="form-group" id="div_container_arguments"><label>Command Arguments (space-separated):</label><input type="text" class="form-control" name="cmd_arguments" id="cmd_arguments" value="coap-server.py" placeholder="arg1 arg2 arg3"></div>',
        port: '<div class="form-group" id="div_container_port"><label>Container Port:</label><input type="number" class="form-control" name="container_port" id="container_port" value="5683" placeholder="Enter container port number"></div>',
        replicas: '<div class="form-group"><label for="replicas">No. of Replicas:</label><input type="number" name="replicas" class="form-control replicas" min="1" value="1" required></div>',
        env: '<div class="form-group" id="envVars"><div class="form-group env-entry"><label>Environment Variables:</label><input type="text" class="form-control" name="envName[]" placeholder="ENV_NAME"><input type="text" class="form-control" name="envValue[]" placeholder="ENV_VALUE"><button type="button" class="btn btn-danger" onclick="removeEntry(this)">Remove</button><button type="button" class="btn btn-primary" onclick="addEnvVar()">Add More</button></div></div>',
        imagePullPolicy: '<div class="form-group" id="div_image_pull_policy"><label>Image Pull Policy:</label><select name="imagePullPolicy" id="pull_policy" class="form-control"><option value="Always">Always</option><option value="IfNotPresent" selected>IfNotPresent</option><option value="Never">Never</option></select></div>',
        volumes: '<div class="form-group" id="volumes"><div class="form-group volume-entry"><label>Volumes and Mounts:</label><input type="text" class="form-control" name="volumeName[]" placeholder="Volume Name (e.g., shared-data)" required><select class="form-control" name="volumeType[]"><option value="emptyDir">emptyDir</option><option value="hostPath" selected>hostPath</option><option value="configMap">configMap</option></select><input type="text" class="form-control" name="volumeSource[]" placeholder="Source (e.g., /host/path)" required><input type="text" class="form-control" name="mountPath[]" placeholder="Mount Path (e.g., /container/path)" required><button type="button" class="btn btn-danger" onclick="removeVolume(this)">Remove</button><button type="button" id="addVolumeBtn" class="btn btn-primary" onclick="addVolume()">Add More</button></div></div>',
        resources: '<div class="resource-section form-group"><label>Requests:</label> <input class="form-control" type="text" name="cpuRequest" placeholder="CPU (e.g., 100m)"> <input class="form-control" type="text" name="memoryRequest" placeholder="Memory (e.g., 256Mi)"> <label>Limits:</label> <input class="form-control" type="text" name="cpuLimit" placeholder="CPU Limit"> <input class="form-control" type="text" name="memoryLimit" placeholder="Memory Limit"></div>',
        restartPolicy: '<div class="advanced-section form-group"><div class="restart-section form-group"><label>Restart Policy:</label><select class="form-control" name="restartPolicy"><option value="Always">Always</option><option value="OnFailure">OnFailure</option><option value="Never">Never</option></select></div></div>',
        affinity: '<div class="affinity-section form-group"><label>Affinity Rule:</label> <input class="form-control" type="text" name="nodeAffinityKey" placeholder="Node label key"> <input class="form-control" type="text" name="nodeAffinityValue" placeholder="Node label value"></div>',
        toleration: '<div class="toleration-section form-group"><label>Toleration:</label> <input type="text" class="form-control" name="tolerationKey" placeholder="Toleration key"> <input type="text" class="form-control" name="tolerationValue" placeholder="Toleration value"> <select class="form-control" name="tolerationEffect"><option class="form-control" value="NoSchedule">NoSchedule</option> <option class="form-control" value="PreferNoSchedule">PreferNoSchedule</option> <option class="form-control" value="NoExecute">NoExecute</option></select></div>',
        securityContext: '<div class="security-context form-group"><label>Security Context:</label> <input type="number" class="form-control" name="runAsUser" placeholder="Run as User ID"> <input type="number" class="form-control" name="runAsGroup" placeholder="Run as Group ID"> <input type="checkbox" name="privileged"> Privileged</div>',
        probes: '<div class="probe-section form-group"><label>Liveness Probe</label> <input type="text" class="form-control" name="livenessPath" placeholder="Path (e.g., /healthz)"> <input type="number" class="form-control" name="livenessPort" placeholder="Port"> <input type="number" class="form-control" name="livenessInitialDelay" placeholder="Initial Delay (s)"> <label>Readiness Probe</label> <input type="text" class="form-control" name="readinessPath" placeholder="Path"> <input type="number" class="form-control" name="readinessPort" placeholder="Port"> <input type="number" class="form-control" name="readinessInitialDelay" placeholder="Initial Delay (s)"></div>',
    };

    return baseHtml[field] || `<input type="text" class="form-control" name="${field}">`;
}

// Show or hide fields based on deployment method
function toggleDeployMethod() {
    const method = document.getElementById('deployMethod').value;
    document.getElementById('yamlSection').style.display = method === 'yaml' ? 'block' : 'none';
    document.getElementById('helmSection').style.display = method === 'helm' ? 'block' : 'none';

    // Show/hide advanced Helm fields based on user level
    const userLevel = document.body.dataset.userLevel;
    //console.log("User Level:", userLevel);
    if (method === 'helm') {
        if (userLevel === 'beginner' || userLevel === 'intermediate' || userLevel === 'advanced') {
            document.getElementById('helm_beginner_div').style.display = method === 'helm' ? 'block' : 'none';
        }

        if (userLevel === 'intermediate' || userLevel === 'advanced') {
            document.getElementById('helm_intermediate_div').style.display = method === 'helm' ? 'block' : 'none';
        }

        if (userLevel === 'advanced') {
            document.getElementById('helm_advanced_div').style.display = method === 'helm' ? 'block' : 'none';
        }
    }
    //document.querySelectorAll('.helm-advanced-fields').forEach(el => {
    //    el.style.display = userLevel === 'advanced' ? 'block' : 'none';
    //});
}

// Show or hide fields static or dynamic configuration method
function toggleConfigMethod() {
    const method = document.getElementById('configMethod').value;
    // const yamlFileInput = document.getElementById('workloadYaml');
    // const containerImage = document.getElementById('image');
    document.getElementById('dynamicConfig').style.display = method === 'dynamic' ? 'block' : 'none';
    document.getElementById('uploadConfig').style.display = method === 'upload' ? 'block' : 'none';

    //if (method === 'upload') {
        //yamlFileInput.setAttribute('required', 'required');
        //containerImage.removeAttribute('required');
    //}
    /*if (method === 'dynamic') {
        yamlFileInput.removeAttribute('required');
        containerImage.setAttribute('required', 'required');
        cmd_interpreter.setAttribute('required', 'required');
        cmd_arguments.setAttribute('required', 'required');
    } else {
        containerImage.removeAttribute('required');
        cmd_interpreter.removeAttribute('required');
        cmd_arguments.removeAttribute('required');
        yamlFileInput.setAttribute('required', 'required');
    }*/
}

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

// Add environment variables dynamically
function addEnvVar() {
  const div = document.createElement('div');
  div.className = 'env-entry form-group';
  div.innerHTML = `
    <hr>
    <label>Environment Variables:</label>
    <input type="text" class="form-control" name="envName[]" placeholder="ENV_NAME">
    <input type="text" class="form-control" name="envValue[]" placeholder="ENV_VALUE">
    <button type="button" class="btn btn-danger" onclick="removeEntry(this)">Remove</button>
    <button type="button" class="btn btn-primary" onclick="addEnvVar()">Add More</button>
  `;
  document.getElementById('envVars').appendChild(div);
}

// Remove environment variable entry
function removeEntry(btn) {
  btn.closest('.env-entry').remove();
}

// Add volume entry dynamically
function addVolume() {
  const div = document.createElement('div');
  div.className = 'volume-entry form-group';
  div.innerHTML = `
    <hr>
    <label>Volumes and Mounts:</label>
    <input type="text" name="volumeName[]" placeholder="Volume Name">
    <select class="form-control" name="volumeType[]">
      <option value="emptyDir">emptyDir</option>
      <option value="hostPath">hostPath</option>
      <option value="configMap">configMap</option>
    </select>
    <input class="form-control" type="text" name="volumeSource[]" placeholder="Path/Name">
    <input class="form-control" type="text" name="mountPath[]" placeholder="Mount Path">
    <button type="button" class="btn btn-danger" onclick="removeVolume(this)">Remove</button>
    <button type="button" id="addVolumeBtn" class="btn btn-primary" onclick="addVolume()">Add More</button>
  `;
  document.getElementById('volumes').appendChild(div);
}

// Remove volume entry
function removeVolume(button) {
  button.closest('.volume-entry').remove();
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
                headerRow.style.backgroundColor = '#535379'; // Dark blue-gray background
                headerRow.style.color = 'white';
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

// Fetch running workloads via an AJAX call
function fetchRunningWorkloads() {
    //const spinner = document.getElementById('loading-spinner');
    const tableBody = document.getElementById('workload-table-body');

    //try {
        // Show spinner
        //spinner.style.display = 'block';
        //tableBody.innerHTML = '';  // Clear previous content

        fetch('/running_workloads')
            .then(response => response.json())
            .then(data => {
                var workloadList = document.getElementById('workload-list-delete');
                workloadList.innerHTML = "";  // Clear previous contents

                // If there are workloads, display them
                if (data.length > 0) {
                    var table = document.createElement('table');
                    var header = table.createTHead();
                    var headerRow = header.insertRow(0);
                    headerRow.style.backgroundColor = '#535379';
                    headerRow.style.color = 'white';
                    headerRow.insertCell(0).innerHTML = "Workload Name";
                    headerRow.insertCell(1).innerHTML = "Duration";
                    headerRow.insertCell(2).innerHTML = "Node";
                    headerRow.insertCell(3).innerHTML = "Deployed By";
                    headerRow.insertCell(4).innerHTML = "Created At";
                    headerRow.insertCell(5).innerHTML = "Action";

                    var body = table.createTBody();
                    data.forEach(workload => {
                        var row = body.insertRow();
                        row.insertCell(0).innerHTML = workload.workload_name;
                        row.insertCell(1).innerHTML = workload.duration;
                        row.insertCell(2).innerHTML = workload.node_name;
                        row.insertCell(3).innerHTML = workload.username;
                        row.insertCell(4).innerHTML = workload.created_at;
                        var deleteButton = document.createElement('button');
                        deleteButton.textContent = 'Delete';
                        deleteButton.className = 'btn btn-danger';
                        deleteButton.onclick = function() {
                            deleteWorkload(workload.workload_name);
                        };
                        row.insertCell(5).appendChild(deleteButton);
                    });

                    workloadList.appendChild(table);
                } else {
                    workloadList.innerHTML = "<p>No workloads deployed yet.</p>";
                }
            })
            .catch(error => {
                console.error("Error fetching running workloads:", error);
            });
    //} catch (error) {
    //    console.error('Error:', error);
    //    tableBody.innerHTML = `<tr><td colspan="4">Error loading workloads</td></tr>`;
    //} finally {
    //    // Hide spinner whether successful or not
    //    spinner.style.display = 'none';
  //}
}

// Delete a running workload via an AJAX call
function deleteWorkload(workload_name) {
    console.log('Deleting workload:', workload_name);
    fetch('/delete_running_workloads', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            workload_name: workload_name
        })
    })
    .then(response => response.json())
    .then(data => {
        showAlert(data.status, data.message);
        fetchRunningWorkloads();
    })
    .catch(error => {
        showAlert('error', 'An error occurred while deleting the workload.');
    });
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    const activeSection = document.getElementById(sectionId);
    if(activeSection) {
        if (sectionId === 'listWorkload') {
            fetchDeployedWorkloads();
        }
        if (sectionId === 'deleteWorkload') {
            fetchRunningWorkloads();
        }
        activeSection.style.display = 'block';
    }

    // Update menu state
    setActiveMenuItem(sectionId);
}

function setActiveMenuItem(targetId) {
    // Remove active class from all items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active class to clicked item
    const activeItem = document.querySelector(`[onclick*="${targetId}"]`);
    if(activeItem) {
        activeItem.classList.add('active');
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
