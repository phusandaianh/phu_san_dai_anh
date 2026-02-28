#!/usr/bin/env bash
# Build script cho Render
set -o errexit

pip install -r requirements.txt

# Tạo thư mục cần thiết
mkdir -p uploads/treatment-plans uploads/pricing uploads/ctg-images instance
