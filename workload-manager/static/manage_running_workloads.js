// Fetch running workloads via an AJAX call
function fetchRunningWorkloads() {
    const tableBody = document.getElementById('workload-table-body');

    fetch('/workload-manager/running_workloads')
    .then(response => response.json())
    .then(data => {
        var workloadList = document.getElementById('workload-list-delete');
        workloadList.innerHTML = "";  // Clear previous contents

        // If there are workloads, display them
        if (data.length > 0) {
            const userRole = document.body.dataset.role;
            const userLevel = document.body.dataset.userLevel

            // Create table for workloads
            const table = document.createElement('table');
            const header = table.createTHead();
            const headerRow = header.insertRow();
            headerRow.style.backgroundColor = '#e6b3cc';
            headerRow.style.color = 'black';
            headerRow.style.fontWeight = 'bold';

            let colIndex = 0;
            headerRow.insertCell(colIndex++).innerHTML = "Workload";
            if (userRole === 'admin') headerRow.insertCell(colIndex++).innerHTML = "Owner";
            headerRow.insertCell(colIndex++).innerHTML = "Method";
            headerRow.insertCell(colIndex++).innerHTML = "Duration";
            headerRow.insertCell(colIndex++).innerHTML = "Created At";
            headerRow.insertCell(colIndex++).innerHTML = "Actions";

            var body = table.createTBody();
            data.forEach(workload => {
                var row = body.insertRow();
                creation_time = (workload.created_at).substring(0, (workload.created_at.lastIndexOf('.')));

                let cellIndex = 0;
                row.insertCell(cellIndex++).innerHTML = workload.workload_name;
                if (userRole === 'admin') row.insertCell(cellIndex++).innerHTML = workload.username;
                row.insertCell(cellIndex++).innerHTML = workload.deploy_method;
                row.insertCell(cellIndex++).innerHTML = workload.duration;
                row.insertCell(cellIndex++).innerHTML = creation_time;

                // Action buttons
                const actionCell = row.insertCell(cellIndex++);

                if (userLevel === 'intermediate' || userLevel === 'advanced')
                {
                    // Edit Button
                    const editBtn = document.createElement('button');
                    editBtn.className = 'btn btn-sm btn-outline-warning ms-1';
                    editBtn.title = 'Update';
                    editBtn.innerHTML = '<i class="fas fa-edit"></i>';
                    editBtn.onclick = () => openEditModal(workload);
                    actionCell.appendChild(editBtn);
                }

                // Delete Button
                var deleteButton = document.createElement('button');
                //deleteButton.textContent = 'Delete';
                deleteButton.className = 'btn btn-sm btn-outline-primary me-1';
                deleteButton.title = 'Delete';
                deleteButton.innerHTML = '<i class="fa-solid fa-trash"></i>';
                deleteButton.onclick = () => deleteWorkload(workload.workload_id, workload.workload_name, workload.deploy_method);
                actionCell.appendChild(deleteButton);
            });

            workloadList.appendChild(table);
        } else {
            workloadList.innerHTML = '<p style="color: #ff0066;">No currently running workloads found for the user.</p>';
        }
    })
    .catch(error => {
        console.error("Error fetching running workloads:", error);
    });
}

// Delete a running workload via an AJAX call
function deleteWorkload(workload_id, workload_name, deploy_method) {
    const button = event.target;
    button.disabled = true;
    button.textContent = ' Deleting...';
    button.classList.add('processing');

    fetch('/workload-manager/delete_running_workloads', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            workload_id: workload_id,
            workload_name: workload_name,
            deploy_method: deploy_method,
            /*created_at: created_at,
            duration: duration,*/
        })
    })
    .then(response => response.json())
    .then(data => {
        button.disabled = false;
        button.textContent = 'Delete';
        button.classList.remove('processing');

        showAlert(data.status, data.message);
        fetchRunningWorkloads();
    })
    .catch(error => {
        button.disabled = false;
        button.textContent = 'Delete';
        button.classList.remove('processing');
        showAlert('error', 'An error occurred while deleting the workload.');
    });
}