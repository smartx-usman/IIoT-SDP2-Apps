const FIELDS_CONFIG = {
    'Pod': {
        beginner: ['image', 'command', 'args', 'port'],
        intermediate: ['env', 'imagePullPolicy', 'resources', 'volumeMounts', 'volumes'],
        advanced: ['affinity', 'toleration', 'securityContext', 'livenessProbe', 'readinessProbe']
    },
    'Deployment': {
        beginner: ['image', 'command', 'args', 'port'],
        intermediate: ['env', 'imagePullPolicy', 'resources', 'volumeMounts', 'volumes'],
        advanced: ['affinity', 'toleration', 'securityContext', 'livenessProbe', 'readinessProbe']
    },
    'Job': {
        beginner: ['image', 'command'],
        advanced: ['backoffLimit', 'ttlSecondsAfterFinished']
    },
    'Service': {
        beginner: ['type', 'port', 'targetPort', 'protocol']
    }
};