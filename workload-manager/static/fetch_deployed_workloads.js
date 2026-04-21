// Fetch deployed workloads via an AJAX call
function fetchDeployedWorkloads() {
    // Clear previous monitoring and file browsing sections
    document.getElementById("singleMonitoringDiv").style.display = "none";
    document.getElementById("fileModal").style.display = "none";
    document.getElementById("editorContainer").style.display = "none";

    // Fetch deployed workloads from the server
    fetch('/workload-manager/deployed_workloads')
        .then(response => response.json())
        .then(data => {
            var workloadList = document.getElementById('workload-list');
            workloadList.innerHTML = "";  // Clear previous contents

            // If there are workloads, display them
            if (data.length > 0) {
                const userRole = document.body.dataset.role;

                // Create table for workloads
                const table = document.createElement('table');
                const header = table.createTHead();
                const headerRow = header.insertRow();
                headerRow.style.backgroundColor = '#e6b3cc';
                headerRow.style.color = 'black';
                headerRow.style.fontWeight = 'bold';

                // Create dynamic header based on admin status
                let colIndex = 0;
                headerRow.insertCell(colIndex++).innerHTML = "Workload";
                if (userRole === 'admin') headerRow.insertCell(colIndex++).innerHTML = "Owner";
                headerRow.insertCell(colIndex++).innerHTML = "Method";
                headerRow.insertCell(colIndex++).innerHTML = "Created At";
                headerRow.insertCell(colIndex++).innerHTML = "Duration";
                headerRow.insertCell(colIndex++).innerHTML = "Replicas";
                headerRow.insertCell(colIndex++).innerHTML = "Node";
                headerRow.insertCell(colIndex++).innerHTML = "Chart";
                headerRow.insertCell(colIndex++).innerHTML = "Version";
                headerRow.insertCell(colIndex++).innerHTML = "Values";
                headerRow.insertCell(colIndex++).innerHTML = "Status";
                headerRow.insertCell(colIndex++).innerHTML = "Actions";

                const body = table.createTBody();
                data.forEach(workload => {
                    const creation_time = workload.created_at.substring(0, workload.created_at.lastIndexOf('.'));
                    const row = body.insertRow();

                    // Dynamic data cells
                    let cellIndex = 0;
                    row.insertCell(cellIndex++).innerHTML = workload.workload_name;
                    if (userRole === 'admin') row.insertCell(cellIndex++).innerHTML = workload.username;
                    row.insertCell(cellIndex++).innerHTML = workload.deploy_method;
                    row.insertCell(cellIndex++).innerHTML = creation_time;
                    row.insertCell(cellIndex++).innerHTML = workload.duration;
                    row.insertCell(cellIndex++).innerHTML = (workload.deploy_method === 'yaml') ? (workload.replicas === null || workload.replicas === 'null' ? '' : workload.replicas) : '';
                    row.insertCell(cellIndex++).innerHTML = (workload.deploy_method === 'yaml') ? (workload.node_name === null || workload.node_name === 'null' ? '' : workload.node_name) : '';
                    row.insertCell(cellIndex++).innerHTML = (workload.deploy_method === 'helm') ? (workload.chart_name === null || workload.chart_name === 'null' ? '' : workload.chart_name) : '';
                    row.insertCell(cellIndex++).innerHTML = (workload.deploy_method === 'helm') ? (workload.chart_version === null || workload.chart_version === 'null' ? '' : workload.chart_version) : '';
                    row.insertCell(cellIndex++).innerHTML = (workload.deploy_method === 'helm') ? (workload.set_values === null || workload.set_values === 'null' ? '' : workload.set_values) : '';
                    //row.insertCell(cellIndex++).innerHTML = workload.status;

                    const statusCell = row.insertCell(cellIndex++);
                    statusCell.innerHTML = workload.is_completed;

                    if (workload.is_completed === true) {
                        statusCell.innerHTML = 'Finished';
                        statusCell.style.backgroundColor = '#d4edda'; // A soft green
                        statusCell.style.color = '#155724'; // Dark green text for contrast
                    }
                    else {
                        statusCell.innerHTML = 'Running';
                        statusCell.style.backgroundColor = '#fff3cd'; // A soft orange/yellow
                        statusCell.style.color = '#856404'; // Dark yellow/brown text
                    }

                    // Action buttons
                    const actionCell = row.insertCell(cellIndex++);

                    // Monitor Button
                    const monitorBtn = document.createElement('button');
                    monitorBtn.className = 'btn btn-sm btn-outline-primary me-1';
                    monitorBtn.title = 'Metrics';
                    monitorBtn.innerHTML = '<i class="fas fa-chart-line"></i>';
                    monitorBtn.onclick = () => monitorSingleWorkload(workload.workload_id, workload.workload_name, workload.created_at, workload.duration, "Metrics");
                    actionCell.appendChild(monitorBtn);

                    // Logs Button
                    const logsBtn = document.createElement('button');
                    logsBtn.className = 'btn btn-sm btn-outline-primary me-1';
                    logsBtn.title = 'Logs';
                    logsBtn.innerHTML = '<i class="fas fa-stream"></i>';
                    logsBtn.onclick = () => monitorSingleWorkload(workload.workload_id, workload.workload_name, workload.created_at, workload.duration, "Logs");
                    actionCell.appendChild(logsBtn);

                    // Browse Button
                    const browseBtn = document.createElement('button');
                    browseBtn.className = 'btn btn-sm btn-outline-secondary me-1';
                    browseBtn.title = 'Browse';
                    browseBtn.innerHTML = '<i class="fas fa-folder-open"></i>';
                    browseBtn.onclick = () => browseWorkloadFiles(workload.workload_id, workload.username, workload.workload_name);
                    actionCell.appendChild(browseBtn);

                    // Edit Button
                    const editBtn = document.createElement('button');
                    editBtn.className = 'btn btn-sm btn-outline-warning ms-1';
                    editBtn.title = 'Edit';
                    editBtn.innerHTML = '<i class="fas fa-edit"></i>';
                    editBtn.onclick = () => openEditModal(workload);
                    actionCell.appendChild(editBtn);

                    // Redeploy Button
                    const redeployBtn = document.createElement('button');
                    redeployBtn.className = 'btn btn-sm btn-outline-success';
                    redeployBtn.title = 'Redeploy';
                    redeployBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
                    redeployBtn.onclick = () => redeployWorkload(workload.workload_id, workload.workload_name);
                    actionCell.appendChild(redeployBtn);
                });
                workloadList.appendChild(table);
            }
            else {
                workloadList.innerHTML = '<p style="color: #ff0066;">No previously deployed workloads exist for the user.</p>';
            }
        })
        .catch(error => {
            console.error("Error fetching deployed workloads:", error);
        });
}

// Monitor a single workload in Grafana
function monitorSingleWorkload(workload_id, workload_name, created_at, duration, monitor) {
    var serverUrl = window.grafanaInternalURL
    var serverPublicUrl = window.grafanaServerPublicUrl
    var namespace = document.body.dataset.namespace;
    var username = document.body.dataset.namespace;

    var fromISO = new Date(new Date(created_at).getTime() - 60 * 1000)//.toISOString(); // 1 minutes before
    var toISO = new Date(new Date(created_at).getTime() + (duration + 60) * 1000)//.toISOString(); // 1 minutes after

    const from = formatAsStockholmISO(fromISO);
    const to = formatAsStockholmISO(toISO);

    if (serverPublicUrl) {
        serverUrl = serverPublicUrl;
    }

    var grafanaUrl = "";

    if (monitor === "Metrics") {
        grafanaUrl = `${serverUrl}/d/metrics-${namespace}-uid/metrics-dashboard-${username}?from=${from}&to=${to}&var-workload_id=${workload_id}&var-namespace=${namespace}`;
    }
    else {
        grafanaUrl = `${serverUrl}/d/logs-${namespace}-uid/logs-dashboard-${username}?from=${from}&to=${to}&var-workload_id=${workload_id}&var-namespace=${namespace}`;
    }
    //var grafanaUrl = `${serverUrl}/d/${namespace}/user-dashboard-${username}?from=${from}&to=${to}&var-workload_id=${workload_id}`;

    const container = document.getElementById("singleMonitoringDiv");
    container.innerHTML = `
            <div>
                <h5 style="background-color: #bf4080;">${monitor} Dashboard for ${workload_name} Workload</h5>
                <iframe src="${grafanaUrl}" width="100%" height="500px" style="border:none;"></iframe>
            </div>
    `;
    document.getElementById("fileModal").style.display = "none";
    document.getElementById("editorContainer").style.display = "none";
    container.style.display = "block";
}

// Browse files in a workload
function browseWorkloadFiles(workload_id, username, workload_name) {
  const rootFolderName = `${username}/${workload_id}`;
  selectedFolder = rootFolderName;

  fetch(`/workload-manager/list_files?folder=${rootFolderName}`)
    .then(res => res.json())
    .then(files => {
      const list = document.getElementById("fileList");
      list.innerHTML = "";

      const tree = buildFileTree(files);

      // Wrap the tree under a root node
      const root = {};
      root[rootFolderName] = tree;

      renderTree(list, root, rootFolderName);

      document.getElementById("singleMonitoringDiv").style.display = "none";
      document.getElementById("fileModal").style.display = "block";
      document.getElementById("editorContainer").style.display = "block";

      const firstFile = findFirstFile(tree);
      if (firstFile) loadYAML(rootFolderName, firstFile);
    });
}

function buildFileTree(paths) {
  const root = {};

  paths.forEach(path => {
    const parts = path.split('/');
    let current = root;

    parts.forEach((part, idx) => {
      if (!current[part]) {
        // If it's the last part, treat it as a file (null)
        current[part] = (idx === parts.length - 1) ? null : {};
      }
      // If it's not a file, move deeper
      if (current[part] !== null) {
        current = current[part];
      }
    });
  });

  return root;
}

function renderTree(container, node, basePath, currentPath = "", isRoot = true) {
  for (const key in node) {
    const fullPath = isRoot ? "" : `${currentPath}${key}`;  // <-- Skip key for root folder node
    const li = document.createElement("li");
    li.style.cursor = "pointer";
    li.style.marginBottom = "5px";

    if (node[key] === null) {
      // It's a file
      li.innerHTML = `<i class="fas fa-file-alt text-secondary mr-1"></i> ${key}`;
      li.onclick = (e) => {
        e.stopPropagation();
        loadYAML(basePath, fullPath);
        };
    } else {
      // It's a folder
      const icon = document.createElement("i");
      icon.className = isRoot ? "fas fa-folder-open text-primary mr-1" : "fas fa-folder text-warning mr-1";
      const folderLabel = document.createElement("span");
      folderLabel.textContent = ` ${key}`;
      folderLabel.style.marginLeft = "4px";

      const nestedList = document.createElement("ul");
      nestedList.style.display = isRoot ? "block" : "none";
      nestedList.style.paddingLeft = "15px";
      nestedList.style.listStyle = "none";

      li.appendChild(icon);
      li.appendChild(folderLabel);
      li.appendChild(nestedList);

      li.onclick = function (e) {
        e.stopPropagation();
        const isOpen = nestedList.style.display === "block";
        nestedList.style.display = isOpen ? "none" : "block";
        icon.className = isOpen ? "fas fa-folder text-warning mr-1" : "fas fa-folder-open text-warning mr-1";
      };

      // 👇 Pass fullPath only if not root
      renderTree(nestedList, node[key], basePath, isRoot ? "" : `${fullPath}/`, false);
    }

    container.appendChild(li);
  }
}

function findFirstFile(tree, path = "") {
  for (const key in tree) {
    const currentPath = path + key;
    if (tree[key] === null) return currentPath;
    const sub = findFirstFile(tree[key], `${currentPath}/`);
    if (sub) return sub;
  }
  return null;
}

function loadYAML(folder, file) {
  selectedFile = file;
  document.getElementById("currentFilename").textContent = file;

  fetch(`/workload-manager/get_yaml?folder=${folder}&filename=${file}`)
    .then(res => res.text())
    .then(content => {
      editor.setValue(content, -1);
      document.getElementById("editorContainer").style.display = "block";
      //document.getElementById("fileModal").style.display = "none";
    });
}

function saveYAML() {
  const content = editor.getValue();
  fetch(`/workload-manager/save_yaml`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      folder: selectedFolder,
      filename: selectedFile,
      content: content
    })
  })
  .then(res => res.text())
  .then(msg => showAlert('success', msg));
}

function downloadYAML() {
  const content = editor.getValue();
  const filename = selectedFile || "download.yaml";

  const blob = new Blob([content], { type: "text/yaml" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  // Cleanup
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 0);
}

// Open the edit and redeploy modal for a workload
function openEditModal(workload) {
    const userLevel = document.body.dataset.userLevel;

    document.getElementById('editWorkloadId').value = workload.workload_id;
    document.getElementById('editWorkloadName').value = workload.workload_name;
    document.getElementById('editDeployMethod').value = workload.deploy_method;
    document.getElementById('editDuration').value = workload.duration || '';

    // Get references to containers
    const modalYamlFields = document.getElementById('editYamlFields');
    const modalHelmFields = document.getElementById('editHelmFields');

    // Clear all field visibility first
    modalYamlFields.style.display = 'none';
    modalHelmFields.style.display = 'none';

    if (workload.deploy_method == 'yaml') {
        modalYamlFields.style.display = 'block';

        document.getElementById('editReplicas').value = workload.replicas || '';
        const nodeSelect = document.getElementById('editNodeName');
        nodeSelect.innerHTML = '<option value="any">Any</option>';

        fetch('/workload-manager/nodes')
            .then(response => response.json())
            .then(data => {
                const nodes = data.nodes;
                for (let node of nodes) {
                    const option = document.createElement('option');
                    option.value = node;
                    option.text = node;
                    if (workload.node_name === node) {
                        option.selected = true;
                    }
                    nodeSelect.appendChild(option);
                }

                // Show Bootstrap modal
                $('#editModal').modal('show');
            })
            .catch(error => console.error('Error fetching nodes:', error));
    } else if (workload.deploy_method === 'helm'){
        modalHelmFields.style.display = 'block';

        document.getElementById('editChartName').value = workload.chart_name || '';

        if (userLevel === 'intermediate' || userLevel === 'advanced') {
            document.getElementById('editVersion').value = workload.chart_version || '';
            document.getElementById('editValues').value = workload.set_values || '';
        }
        $('#editModal').modal('show');
    }
}

function closeEditModal() {
    $('#editModal').modal('hide');
}

// Redeploy a workload
function redeployWorkload(workload_id, workload_name) {
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Redeploying...';
    button.classList.add('processing');

    fetch('/workload-manager/redeploy_workload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            workload_id: workload_id,
            workload_name: workload_name
        })
    })
    .then(response => response.json())
    .then(data => {
        button.disabled = false;
        //button.textContent = 'Redeploy';
        button.classList.remove('processing');

        showAlert(data.status, data.message, true);
    })
    .catch(error => {
        button.disabled = false;
        //button.textContent = 'Redeploy';
        button.innerHTML = '<i class="fas fa-sync-alt"></i>';
        button.classList.remove('processing');
        button.className = 'btn btn-sm btn-outline-success';
        showAlert('error', 'An error occurred while redeploying the workload.' + error.message);
    });
}

// Change UTC time to local time
function formatAsStockholmISO(date) {
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false, // 24-hour format
        timeZone: 'Europe/Stockholm',
    };

    // Create a formatter for the Swedish locale and Stockholm timezone
    const formatter = new Intl.DateTimeFormat('sv-SE', options);

    // Format the date. The result will be something like "YYYY-MM-DD HH:MM:SS" based on the Stockholm timezone.
    const parts = formatter.formatToParts(date);
    let year, month, day, hour, minute, second;

    for (const part of parts) {
        switch (part.type) {
            case 'year': year = part.value; break;
            case 'month': month = part.value; break;
            case 'day': day = part.value; break;
            case 'hour': hour = part.value; break;
            case 'minute': minute = part.value; break;
            case 'second': second = part.value; break;
        }
    }

    return `${year}-${month}-${day}T${hour}:${minute}:${second}`;
}