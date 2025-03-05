const FIELDS_CONFIG = {
    'Pod': {
        beginner: ['image', 'command', 'args', 'port'],
        intermediate: ['image', 'command', 'args', 'port', 'env', 'imagePullPolicy', 'resources', 'volumes'],
        advanced: ['image', 'command', 'args', 'port', 'env', 'imagePullPolicy', 'resources', 'volumes', 'restartPolicy', 'affinity', 'toleration', 'securityContext', 'probes']
    },
    'Deployment': {
        beginner: ['image', 'command', 'args', 'port', 'replicas'],
        intermediate: ['image', 'command', 'args', 'port', 'replicas', 'env', 'imagePullPolicy', 'resources', 'volumes'],
        advanced: ['image', 'command', 'args', 'port', 'replicas', 'env', 'imagePullPolicy', 'resources', 'volumes', 'restartPolicy', 'affinity', 'toleration', 'securityContext', 'probes']
    },
    'Job': {
        beginner: ['image', 'command'],
        advanced: ['backoffLimit', 'ttlSecondsAfterFinished']
    },
    'Service': {
        beginner: ['type', 'port', 'targetPort', 'protocol']
    }
};