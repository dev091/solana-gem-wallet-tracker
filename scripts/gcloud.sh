#!/bin/bash
# Google Cloud CLI on D:, config (incl. login tokens) kept in git-ignored data/secrets/gcloud.
export CLOUDSDK_PYTHON='D:\DeveloperStorage\venvs\solana-tracker\Scripts\python.exe'
export CLOUDSDK_CONFIG='D:\Crypto Investment\solana-tracker\data\secrets\gcloud'
exec /d/DeveloperStorage/google-cloud-sdk/bin/gcloud.cmd "$@"
