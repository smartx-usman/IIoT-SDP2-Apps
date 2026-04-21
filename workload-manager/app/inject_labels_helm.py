#!/usr/bin/env python3
import logging
import os
import sys
import yaml

LABEL_KEY = "workload_id"
LABEL_VALUE = os.environ.get("WORKLOAD_ID", "0")

def inject_labels(doc):
    try:
        if "spec" in doc and "template" in doc["spec"]:
            # Add label to pod template
            pod_labels = doc["spec"]["template"].setdefault("metadata", {}).setdefault("labels", {})
            pod_labels[LABEL_KEY] = LABEL_VALUE

            # Add label to selector if applicable (e.g., for Deployment, StatefulSet)
            if "selector" in doc["spec"]:
                match_labels = doc["spec"]["selector"].setdefault("matchLabels", {})
                match_labels[LABEL_KEY] = LABEL_VALUE
    except Exception:
        logging.error("Error injecting labels into document", exc_info=True)
        pass

with sys.stdin as f:
    docs = list(yaml.safe_load_all(f))

for doc in docs:
    if doc is not None:
        inject_labels(doc)

yaml.safe_dump_all(docs, sys.stdout)
