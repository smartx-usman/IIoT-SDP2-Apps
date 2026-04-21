// Update form fields based on resource type and user level
function updateFormFields() {
    const resourceType = document.getElementById('resourceType').value;
    const userLevel = document.body.dataset.userLevel;
    const userNamespace = document.body.dataset.namespace;

    // Show/hide service section
    document.querySelector('.service-section').style.display =
        ['Deployment', 'StatefulSet', 'DaemonSet'].includes(resourceType) ? 'block' : 'none';
    document.getElementById('serviceOptions').style.display = ['Deployment', 'StatefulSet', 'DaemonSet'].includes(resourceType) ? 'block' : 'none';

    // Get fields for current resource and user level
    const fields = FIELDS_CONFIG[resourceType][userLevel] || [];

    // Generate HTML for fields
    const html = fields.map(field => `
            ${generateFieldInput(field, userLevel)}
    `).join('');

    document.getElementById('dynamicFields').innerHTML = html;
}

function generateFieldInput(field, userLevel) {
    const baseHtml = {
      image: `<fieldset class="form-group-section form-group-section-blue">
        <legend class="form-group-section-title-sub">Container Basic Settings</legend>
        <div class="form-group" id="div_container_image">
          <label>Container Image:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Container image name and tag (e.g., nginx:latest)">
                <i class="fas fa-info-circle"></i>
            </span>
          </label>
          <input type="text" class="form-control" name="image" id="image" value="usman476/coap:latest" placeholder="Enter container info.">
        </div>`,
      command: `<div class="form-group" id="div_container_interpreter">
        <label>Command Interpreter:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Entrypoint command interpreter (e.g., /bin/sh, python)">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="text" class="form-control" name="cmd_interpreter" id="cmd_interpreter" value="python3" placeholder="Enter command interpreter (e.g., shell)">
      </div>`,
      args: `<div class="form-group" id="div_container_arguments">
        <label>Command Arguments (space-separated):
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Arguments passed to the command interpreter, space-separated">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="text" class="form-control" name="cmd_arguments" id="cmd_arguments" value="coap-server.py" placeholder="arg1 arg2 arg3">
      </div>`,
      port: `<div class="form-group" id="div_container_port">
        <label>Container Port:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Port number exposed by the container (1-9999)">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="number" class="form-control" name="container_port" id="container_port" value="5683" min="1" max="9999" placeholder="Enter container port number">
      </div>`,
      replicas: `<div class="form-group">
        <label for="replicas">No. of Replicas:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Specify the number of same copies to run for the deployment.">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="number" name="replicas" class="form-control replicas" min="1" value="1" required>
      </div></fieldset>`,
      imagePullPolicy: `<fieldset class="form-group-section form-group-section-blue">
        <legend class="form-group-section-title-sub">Resources and Storage Settings</legend>
        <div class="form-group" id="div_image_pull_policy">
        <label>Image Pull Policy:
            <label>Image Pull Policy:
                <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                    title="When to pull container images from registry">
                    <i class="fas fa-info-circle"></i>
                </span>
            </label>
        </label>
        <select name="imagePullPolicy" id="pull_policy" class="form-control">
          <option value="Always">Always</option>
          <option value="IfNotPresent" selected>IfNotPresent</option>
          <option value="Never">Never</option>
        </select>
      </div>`,
      env: `<div class="form-group" id="envVars">
        <div class="form-group env-entry">
          <label>Environment Variables:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Environment variables injected into the container">
                <i class="fas fa-info-circle"></i>
            </span>
          </label>
          <input type="text" class="form-control" name="envName[]" placeholder="ENV_NAME">
          <input type="text" class="form-control" name="envValue[]" placeholder="ENV_VALUE">
          <button type="button" class="btn btn-danger" onclick="removeEntry(this)">Remove</button>
          <button type="button" class="btn btn-primary" onclick="addEnvVar()">Add More</button>
        </div>
      </div>`,
      volumes: `<div class="form-group" id="volumes">
        <div class="form-group volume-entry">
          <label>Volumes and Mounts:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Configure persistent storage and mount points">
                <i class="fas fa-info-circle"></i>
            </span>
          </label>
          <input type="text" class="form-control" name="volumeName[]" placeholder="Volume Name (e.g., shared-data)">
          <select class="form-control" name="volumeType[]">
            <option value="hostPath" selected>hostPath</option>
          </select>
          <input type="text" class="form-control" name="volumeSource[]" placeholder="Source (e.g., /host/path)">
          <input type="text" class="form-control" name="mountPath[]" placeholder="Mount Path (e.g., /container/path)">
          <button type="button" class="btn btn-danger" onclick="removeVolume(this)">Remove</button>
          <button type="button" id="addVolumeBtn" class="btn btn-primary" onclick="addVolume()">Add More</button>
        </div>
      </div>
      </fieldset>`,
      resources: `<div class="resource-section form-group">
        <label>Requests:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Minimum resources guaranteed for the container. CPU must be in millicores (e.g., 100m), Memory in Mi or Gi¨ (e.g., 256Mi)">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input class="form-control" type="text" name="cpuRequest" pattern="^\d+m$" placeholder="CPU (e.g., 100m)" oninput="validateCpu(this)">
        <input class="form-control" type="text" name="memoryRequest" pattern="^\d+(Mi|Gi)$" placeholder="Memory (e.g., 256Mi)" oninput="validateMemory(this)">
        <label>Limits:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Maximum resources the container can use. CPU must be in millicores (e.g., 200m), Memory in Mi or Gi (e.g., 512Gi)">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input class="form-control" type="text" name="cpuLimit" pattern="^\d+m$" placeholder="CPU Limit" oninput="validateCpu(this)">
        <input class="form-control" type="text" name="memoryLimit" pattern="^\d+(Mi|Gi)$" placeholder="Memory Limit" oninput="validateMemory(this)">
      </div>`,
      restartPolicy: `<fieldset class="form-group-section form-group-section-blue">
        <legend class="form-group-section-title-sub">Advanced Settings</legend>
        <div class="advanced-section form-group">
        <div class="restart-section form-group">
          <label>Restart Policy:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Container restart behavior">
                <i class="fas fa-info-circle"></i>
            </span>
          </label>
          <select class="form-control" name="restartPolicy">
            <option value="Always">Always</option>
            <option value="OnFailure">OnFailure</option>
            <option value="Never">Never</option>
          </select>
        </div>
      </div>`,
      affinity: `<div class="affinity-section form-group">
        <label>Affinity Rule:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Schedule pods on specific nodes using labels">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input class="form-control" type="text" name="nodeAffinityKey" placeholder="Node label key">
        <input class="form-control" type="text" name="nodeAffinityValue" placeholder="Node label value">
      </div>`,
      toleration: `<div class="toleration-section form-group">
        <label>Toleration:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Allow pods to schedule on tainted nodes">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="text" class="form-control" name="tolerationKey" placeholder="Toleration key">
        <input type="text" class="form-control" name="tolerationValue" placeholder="Toleration value">
        <select class="form-control" name="tolerationEffect">
          <option class="form-control" value="NoSchedule">NoSchedule</option>
          <option class="form-control" value="PreferNoSchedule">PreferNoSchedule</option>
          <option class="form-control" value="NoExecute">NoExecute</option>
        </select>
      </div>`,
      securityContext: `<div class="security-context form-group">
        <label>Security Context:
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Container security privileges">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="number" class="form-control" name="runAsUser" placeholder="Run as User ID">
        <input type="number" class="form-control" name="runAsGroup" placeholder="Run as Group ID">
        <input type="checkbox" name="privileged"> Privileged
      </div>`,
      probes: `<div class="probe-section form-group">
        <label>Liveness Probe
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Container health checks">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="text" class="form-control" name="livenessPath" placeholder="Path (e.g., /healthz)">
        <input type="number" class="form-control" name="livenessPort" placeholder="Port">
        <input type="number" class="form-control" name="livenessInitialDelay" placeholder="Initial Delay (s)">
        <label>Readiness Probe
            <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                title="Container readiness checks">
                <i class="fas fa-info-circle"></i>
            </span>
        </label>
        <input type="text" class="form-control" name="readinessPath" placeholder="Path">
        <input type="number" class="form-control" name="readinessPort" placeholder="Port">
        <input type="number" class="form-control" name="readinessInitialDelay" placeholder="Initial Delay (s)">
      </div></fieldset>`,
    };

    return baseHtml[field] || `<input type="text" class="form-control" name="${field}">`;
}

// Update service fields based on service type
function updateServiceFields() {
    const resourceType = document.getElementById('resourceType').value;
    const serviceType = document.querySelector('[name="service_type"]').value;
    const serviceFieldsDiv = document.getElementById('serviceOptions');

    // Common fields for both ClusterIP and NodePort
    const commonFields = `
        <fieldset class="form-group-section form-group-section-blue">
            <legend class="form-group-section-title-sub">Service Details</legend>
        <div class="form-group">
            <label>Port:
                <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                    title="Port exposed by the service within the cluster">
                    <i class="fas fa-info-circle"></i>
                </span>
            </label>
            <input type="number" class="form-control" name="svcPort" required>
        </div>
        <div class="form-group">
            <label>Target Port:
                <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                    title="Port on the container where traffic is sent">
                    <i class="fas fa-info-circle"></i>
                </span>
            </label>
            <input type="number" class="form-control" name="targetPort" required>
        </div>
        <div class="form-group">
            <label>Protocol:
                <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                    title="Network protocol used by the service">
                    <i class="fas fa-info-circle"></i>
                </span>
            </label>
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
                <label>Node Port:
                    <span class="ml-1" data-toggle="tooltip" data-placement="right" style="cursor: pointer; color: #007bff;"
                    title="Port exposed on cluster nodes (30000-32767)">
                    <i class="fas fa-info-circle"></i>
                </span>
                </label>
                <input type="number" class="form-control" name="nodePort" min="30000" max="32767">
            </div>
        `;
    }

    // Combine fields based on service type
    const html = serviceType ?
        commonFields + serviceSpecificFields + `</fieldset>`:
        '<p>Select a service type to configure</p>';

    // Update the container and toggle visibility
    serviceFieldsDiv.innerHTML = html;
    serviceFieldsDiv.style.display = serviceType ? 'block' : 'none';
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
    <input type="text" class="form-control" name="volumeName[]" placeholder="Volume Name (e.g., shared-data)">
    <select class="form-control" name="volumeType[]">
      <option value="hostPath">hostPath</option>
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