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
        if (sectionId === 'showMonitoring') {
            var serverUrl = window.grafanaInternalURL
            var serverPublicUrl = window.grafanaServerPublicUrl
            var namespace = document.body.dataset.namespace;
            var username = document.body.dataset.namespace;

            if (serverPublicUrl) {
                serverUrl = serverPublicUrl;
            }

            var grafanaUrl = `${serverUrl}/d/cluster-${namespace}-uid/cluster-wide-resources-dashboard-${username}?var-Node=$__all&var-Namespace=${namespace}`;
            //var grafanaUrl = `/grafana/d/${namespace}/user-dashboard-${username}`;
            var iframe = document.getElementById("grafana-iframe");
            iframe.src = grafanaUrl;
            //iframe.src = "/grafana_proxy/d/"+namespace+"/user-dashboard-"+username;  // Proxy request to Grafana
            iframe.style.display = "block";
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

function showAlert(type, message, reload = false) {
    const popupContainer = document.getElementById('popup-alert-container');
    const popupMessage = document.getElementById('popup-message');
    const popupAlert = document.getElementById('popup-alert');
    const closeButton = document.getElementById('popup-close-button');

    popupMessage.textContent = message;

    if (type === 'success') {
        //popupAlert.style.backgroundColor = '#d4edda';
        popupAlert.style.color = '#66CDAA';
        popupAlert.style.border = '4px outset #66CDAA';
        popupAlert.className = 'alert alert-success';
    } else {
        //popupAlert.style.backgroundColor = '#f8d7da';
        popupAlert.style.color = '#DC143C';
        popupAlert.style.border = '4px outset #DC143C';
        popupAlert.className = 'alert alert-error';
    }

    popupContainer.style.display = 'flex'; // Show the pop-up container

    // Automatically hide the pop-up after 2 seconds
    const timeoutId = setTimeout(() => {
        popupContainer.style.display = 'none';
        if (reload) {
            window.location.reload();
        }
    }, 2000);

    // Add an event listener to the close button to clear the timeout if the user closes manually
    closeButton.onclick = () => {
        popupContainer.style.display = 'none';
        clearTimeout(timeoutId); // Clear the automatic timeout
        if (reload) {
            window.location.reload();
        }
    };
}