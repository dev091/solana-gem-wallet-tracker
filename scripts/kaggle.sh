#!/bin/bash
# Kaggle CLI with its token kept in git-ignored data/secrets/kaggle; downloads land in data/history/kaggle.
export KAGGLE_CONFIG_DIR='D:\Crypto Investment\solana-tracker\data\secrets\kaggle'
# New-style token: a text file holding the token from kaggle.com Settings -> API Tokens.
T='D:/Crypto Investment/solana-tracker/data/secrets/kaggle/access_token'
[ -f "$T" ] && export KAGGLE_API_TOKEN="$T"
cd "/d/Crypto Investment/solana-tracker/data/history/kaggle" || exit 1
exec /d/DeveloperStorage/venvs/solana-tracker/Scripts/kaggle.exe "$@"
