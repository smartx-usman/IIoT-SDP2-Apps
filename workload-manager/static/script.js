document.addEventListener('DOMContentLoaded', function() {
    // Store workload templates in a global variable
    let workloadTypes = [];

    // Initialize Ace editor for YAML input
    editor = ace.edit("editor");
    editor.setTheme("ace/theme/github");
    editor.session.setMode("ace/mode/yaml");

    // Initialize Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Fetch an existing user data
    $('#fetchUserBtn').on('click', function() {
        const username = $('#user-update-form #username').val();

        if (!username) return alert("Please enter a username first");

        $.ajax({
            url: `/workload-manager/get_user/${username}`,
            method: 'GET',
            success: function(data) {
                // Populate the form fields directly
                $('#user-update-form #role').val(data.role);
                $('#user-update-form #level').val(data.user_level);
                $('#user-update-form #quota_pods').val(data.quota_pods);
                $('#user-update-form #quota_cpu').val(data.quota_cpu);
                $('#user-update-form #quota_memory').val(data.quota_memory);

                // Clear password field for security (don't show old hashes)
                $('#user-update-form #password').val('').attr('placeholder', 'Leave blank to keep current password');
            },
            error: function(err) {
                alert("User not found or access denied.");
            }
        });
    });

    // Show active menu item
    const defaultSection = document.querySelector('.section:not([style*="none"])');
    if(defaultSection) {
        setActiveMenuItem(defaultSection.id);
    }

    // Show or hide fields based on user level and content generation method
    toggleConfigMethod();

    // Add event listener for CPU input validation
    document.querySelectorAll('input[name^="cpu"]').forEach(input => {
        input.addEventListener('input', function() {
          validateCpu(this);
        });
    });

    // Add event listener for memory input validation
    document.querySelectorAll('input[name^="memory"]').forEach(input => {
        input.addEventListener('input', function() {
          validateMemory(this);
        });
    });

    // Fetch nodes and populate node dropdowns
    fetch('/workload-manager/nodes')
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
    fetch('/workload-manager/workload_templates')
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
                    // Add data for hidden fields
                    option.dataset.deployMethod = type.deploy_method;
                    option.dataset.helmRepoName = type.helm_repo_name;
                    option.dataset.helmRepoURL = type.helm_repo_url;
                    option.dataset.helmChart = type.helm_chart;
                    option.dataset.helmChartVersion = type.helm_chart_version;
                    option.dataset.helmSetValues = type.helm_set_values;
                    select.add(option);

                    // console.log("Workload Types:", type);
                }

                // Trigger change event to populate hidden fields initially
                if (select.options.length > 0) {
                    select.selectedIndex = 0;
                    const workloadSection = select.closest('.workload-section');
                    populateWorkloadFields(workloadSection, select.options[0]);
                }

                //initializeWorkloadSections();
            }
        })
        .catch(error => console.error('Error fetching workload types:', error));

    document.getElementById('workloads').addEventListener('change', function(e) {
        if (e.target.classList.contains('workload_type')) {
            const workloadSection = e.target.closest('.workload-section');
            const selectedOption = e.target.options[e.target.selectedIndex];

            // Populate the fields for the selected workload type
            populateWorkloadFields(workloadSection, selectedOption);
        }
    });

    // User Registration Form submission handler
    document.getElementById('user-registration-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch('/workload-manager/register', {
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

    // User Edit Form submission handler
    document.getElementById('user-update-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch('/workload-manager/update_user', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            showAlert(data.status, data.message);
        })
        .catch(error => {
            showAlert('error', 'An error occurred while updating user details.');
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
        const totalStart = performance.now(); // Start total timer
        event.preventDefault();
        const formData = new FormData(this);
        const userNamespace = document.body.dataset.namespace;
        formData.append('namespace', userNamespace);

        /*for (const [key, value] of formData.entries()) {
            console.log(`${key}:`, value);
        }*/

        fetch('/workload-manager/deploy_workload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const totalEnd = performance.now();
            console.log(`Total execution time: ${(totalEnd - totalStart).toFixed(3)} ms`);
            showAlert(data.status, data.message);
        })
        .catch(error => {
            showAlert('error', 'An error occurred while submitting the workload.');
        });
    });

    // Add new workload section handler
    document.getElementById('addWorkloadBtn').addEventListener('click', function() {
        const workloadDiv = document.createElement('div');
        workloadDiv.className = 'workload-section';
        workloadDiv.innerHTML = `
            <fieldset class="form-group-section form-group-section-yellow">
            <legend class="form-group-section-title-main">Workload Details</legend>
            <div class="form-group">
                <label for="duration">Run Duration (seconds):
                    <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                        title="How long the workload should run before automatic termination (in seconds). Minimum 30 seconds.">
                        <i class="fas fa-info-circle"></i>
                    </span>
                </label>
                <input type="number" name="duration[]" class="form-control duration" min="30" value="120" required>
            </div>
            <div class="form-group">
                <label for="workload_type">Workload Template:
                    <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                        title="Select a pre-configured workload template to deploy">
                        <i class="fas fa-info-circle"></i>
                    </span>
                </label>
                <select name="workload_type[]" class="form-control workload_type" required></select>
            </div>
            <input type="hidden" name="deploy_method[]" class="form-control deploy_method">
            <div class="yaml-specific" style="display: none;">
                <div class="form-group">
                    <label for="replicas">No. of Replicas:
                        <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                            title="Number of identical pod instances to run. Only applicable for Deployment resources">
                            <i class="fas fa-info-circle"></i>
                        </span>
                    </label>
                    <input type="number" name="replicas[]" class="form-control replicas" min="1" value="1"
                           required>
                </div>
                <div class="form-group">
                    <label for="node_name">Cluster Node for Deployment:
                        <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                        title="Select a specific cluster node to run this workload, or 'Any' for automatic scheduling">
                            <i class="fas fa-info-circle"></i>
                        </span>
                    </label>
                    <select name="node_name[]" class="form-control node_name" required>
                        <option value="any">Any</option>
                    </select>
                </div>
            </div>
            <div class="helm-specific" style="display: none;">
                <div class="form-group" style="display: none;">
                    <label for="helm_repo_name">Repository Name (Used for adding repo):
                        <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                            title="Alias name for the Helm repository (used when adding repos)">
                                <i class="fas fa-info-circle"></i>
                        </span>
                    </label>
                    <input type="text" class="form-control helm-field helm_repo_name" name="helm_repo_name[]" placeholder="Repository Name" title="It is an alias you assign when adding a repository." >
                </div>
                <div class="form-group" style="display: none;">
                    <label for="helm_repo_url">Helm Repository URL:
                        <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                            title="URL of the Helm chart repository">
                            <i class="fas fa-info-circle"></i>
                        </span>
                    </label>
                    <input type="text" class="form-control helm-field helm_repo_url" name="helm_repo_url[]" placeholder="Helm Repository" title="This is the URL where the Helm chart repository is hosted.">
                </div>
                <div class="form-group">
                    <label for="helm_chart">Chart Name:
                        <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                            title="Name of the Helm chart to deploy (e.g., nginx, mysql)">
                            <i class="fas fa-info-circle"></i>
                        </span>
                    </label>
                    <input type="text" class="form-control helm-field helm_chart" name="helm_chart[]" placeholder="Chart Name" title="It is the URL path to the chart.">
                </div>
                <div class="advanced-helm-fields" style="display: none;">
                    <div class="form-group">
                        <label for="helm_chart_version">Chart Version:
                            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                                title="Specific version of the chart to install (leave blank for latest)">
                                <i class="fas fa-info-circle"></i>
                            </span>
                        </label>
                        <input type="text" class="form-control helm-field helm_chart_version" name="helm_chart_version[]" placeholder="Chart Version" title="It specifies chart version to install.">
                    </div>
                    <div class="form-group">
                        <label for="helm_set_values">Set Values:
                            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                                title="Custom chart values in key=value format (semicolon separated)">
                                <i class="fas fas-info-circle"></i>
                            </span>
                        </label>
                        <textarea class="form-control helm-field helm_set_values" name="helm_set_values[]"
                              placeholder="key1=value1;key2=value2" title="It will set values on the command line."></textarea>
                    </div>
                </div>
            </div>
            <button type="button" class="btn btn-danger" onclick="removeWorkload(this)">Remove Entry</button>
            </fieldset>
        `;

        const userLevel = document.body.dataset.userLevel;
        if (userLevel === 'intermediate' || userLevel === 'advanced') {
            workloadDiv.querySelector('.advanced-helm-fields').style.display = 'block';
        }

        document.getElementById('workloads').appendChild(workloadDiv);

        // Get the newly created workload type dropdown
        const newSelect = workloadDiv.querySelector('.workload_type');

        // Populate the dropdown with the pre-fetched workload types
        workloadTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.workload_name;
            option.text = type.workload_name;
            option.dataset.deployMethod = type.deploy_method;
            option.dataset.helmRepoName = type.helm_repo_name;
            option.dataset.helmRepoURL = type.helm_repo_url;
            option.dataset.helmChart = type.helm_chart;
            option.dataset.helmChartVersion = type.helm_chart_version;
            option.dataset.helmSetValues = type.helm_set_values;
            newSelect.add(option);
        });

        // Check if there's a pre-populated workload and use it to initialize the fields.
        if (newSelect.options.length > 0) {
            newSelect.selectedIndex = 0;
            // Explicitly call the function to populate the fields for the new block.
            populateWorkloadFields(workloadDiv, newSelect.options[0]);
        }

        // Fetch and populate nodes for the new section
        fetch('/workload-manager/nodes')
            .then(response => response.json())
            .then(data => {
                const nodeSelect = workloadDiv.querySelector('.node_name');
                const nodes = data.nodes;
                nodeSelect.innerHTML = '<option value="any">Any</option>'; // Clear and add default
                nodes.forEach(node => {
                    const option = document.createElement('option');
                    option.value = node;
                    option.text = node;
                    nodeSelect.add(option);
                });
            })
            .catch(error => console.error('Error fetching nodes:', error));
    });

    // Handle adding workload type form submission
    document.getElementById('workload-template-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const userLevel = document.body.dataset.userLevel;

        // Add manual fields
        const fieldsToAdd = [
            'workloadDisplayName',
            'workloadEnabled',
            'deployMethod',
            'configMethod'
        ];

        // Get the form element
        const form = document.getElementById('workload-template-form');
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
            const repoName = document.getElementById('helmRepoName').value.trim();
            const repoURL = document.getElementById('helmRepoURL').value.trim();
            const chart = document.getElementById('helmChart').value.trim();
            formData.append('helm_repo_name', repoName);
            formData.append('helm_repo_url', repoURL);
            formData.append('helm_chart_name', chart);

            if (userLevel === 'intermediate' || userLevel === 'advanced') {
                const helmChartVersion = document.getElementById('helmChartVersion').value.trim();
                const helmSetValues = document.getElementById('helmSetValues').value.trim();
                formData.append('helm_chart_version', helmChartVersion);
                formData.append('helm_set_values', helmSetValues);
            }

            /*if (userLevel === 'advanced') {
                const files = document.getElementById('helmValuesFile').files;
                if (files.length > 0) {
                    formData.append('helm_values_file', files[0]);
                }
            }*/
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
                //console.log(`Filtered Data - ${key}:`, value);
            }
        }

        fetch('/workload-manager/create_workload_template', {
            method: 'POST',
            body: filteredData
        })
        .then(response => response.json())
        .then(data => {
            // After successfully adding a new workload type, refresh all the dropdowns for workload_types
            fetch('/workload-manager/workload_templates')
              .then(response => response.json())
              .then(data => {
                workloadTypes = data.types;
                // Update ALL dropdowns
                const allDropdowns = document.querySelectorAll('.workload_type');
                allDropdowns.forEach(select => {
                  select.innerHTML = ''; // Clear existing options
                  workloadTypes.forEach(type => {
                    //console.log("Workload Types 2:", type);
                    const option = document.createElement('option');
                    option.value = type.workload_name;
                    option.text = type.workload_name;
                    option.dataset.deployMethod = type.deploy_method;
                    option.dataset.helmRepoName = type.helm_repo_name;
                    option.dataset.helmRepoURL = type.helm_repo_url;
                    option.dataset.helmChart = type.helm_chart;
                    option.dataset.helmChartVersion = type.helm_chart_version;
                    option.dataset.helmSetValues = type.helm_set_values;
                    select.appendChild(option);
                  });
                  // Re-trigger change event
                  select.dispatchEvent(new Event('change'));
                });
              });

            showAlert(data.status, data.message);
        })
        .catch(error => {
            showAlert('error', 'An error occurred while adding the workload type.');
        });
    });

    // Clear workload form button handler
    document.getElementById('clearFormBtn').addEventListener('click', function() {
        const workloadsContainer = document.getElementById('workloads');
        const initialWorkloadSectionHtml = workloadsContainer.innerHTML;
        workloadsContainer.innerHTML = '';
    });

    // Handle Edit and Redeploy workload form submission
    document.getElementById('editRedeployForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const form = e.target;

        const workloadId = document.getElementById('editWorkloadId').value;
        const workloadName = document.getElementById('editWorkloadName').value.trim();
        const method = document.getElementById('editDeployMethod').value;
        const duration = document.getElementById('editDuration').value;

        const payload = {
            previous_workload_id: workloadId,
            workload_name: workloadName,
            method: method,
            duration: duration
        };
        console.log("Method:", method);
        if (method === 'yaml') {
            payload.replicas = document.getElementById('editReplicas').value;
            payload.node_name = document.getElementById('editNodeName').value;
        }

        if (method === 'helm') {
            payload.chart_name = document.getElementById('editChartName').value;
            payload.version = document.getElementById('editVersion').value;
            payload.values = document.getElementById('editValues').value;
        }

        //console.log("Payload:", payload);

        fetch(`/edit_and_redeploy/${workloadId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            //if (response.ok) {
                closeEditModal();
                showAlert(data.status, data.message, true);
                fetchDeployedWorkloads(); // refresh table
            /*} else {
                showAlert('error', 'An error occurred while redeploying the workload.');
            }*/
        })
        .catch(err => {
            showAlert('error', 'An error occurred while redeploying the workload: ' + err.message);
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

// File editing options
let selectedFolder = "";
let selectedFile = "";
let editor;

// Initialize workload sections
function populateWorkloadFields(workloadSection, selectedOption) {
    const deployMethod = selectedOption.dataset.deployMethod;
    const helmFields = workloadSection.querySelector('.helm-specific');
    const yamlFields = workloadSection.querySelector('.yaml-specific');

    // Show/hide the correct form fields based on the deploy method
    helmFields.style.display = deployMethod === 'helm' ? 'block' : 'none';
    yamlFields.style.display = deployMethod === 'yaml' ? 'block' : 'none';

    // Update the hidden deploy_method field
    workloadSection.querySelector('.deploy_method').value = deployMethod;

    // Populate fields based on the deployment method
    if (deployMethod === 'helm') {
        workloadSection.querySelector('[name="helm_repo_name[]"]').value = selectedOption.dataset.helmRepoName;
        workloadSection.querySelector('[name="helm_repo_url[]"]').value = selectedOption.dataset.helmRepoURL;
        workloadSection.querySelector('[name="helm_chart[]"]').value = selectedOption.dataset.helmChart;

        // Handle advanced Helm fields based on user level
        const userLevel = document.body.dataset.userLevel;
        if (userLevel === 'intermediate' || userLevel === 'advanced') {
            const advancedHelmFields = workloadSection.querySelector('.advanced-helm-fields');
            if (advancedHelmFields) {
                advancedHelmFields.style.display = 'block';
                workloadSection.querySelector('[name="helm_chart_version[]"]').value = selectedOption.dataset.helmChartVersion;
                workloadSection.querySelector('[name="helm_set_values[]"]').value = selectedOption.dataset.helmSetValues;
            }
        }
    } else {
        // Clear Helm fields if the method changes to YAML
        workloadSection.querySelectorAll('.helm-field').forEach(field => field.value = '');
        const advancedHelmFields = workloadSection.querySelector('.advanced-helm-fields');
        if (advancedHelmFields) {
            advancedHelmFields.style.display = 'none';
        }
    }
}

// Remove a workload section
function removeWorkload(button) {
    button.closest('div').remove();
}

// Show or hide fields based on deployment method
function toggleDeployMethod() {
    const method = document.getElementById('deployMethod').value;
    document.getElementById('yamlSection').style.display = method === 'yaml' ? 'block' : 'none';
    document.getElementById('helmSection').style.display = method === 'helm' ? 'block' : 'none';

    const userLevel = document.body.dataset.userLevel;

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
}

// Show or hide fields static or dynamic configuration method
function toggleConfigMethod() {
    const method = document.getElementById('configMethod').value;
    document.getElementById('dynamicConfig').style.display = method === 'dynamic' ? 'block' : 'none';
    document.getElementById('uploadConfig').style.display = method === 'upload' ? 'block' : 'none';
}
