#!/bin/bash
set -e

curl -f http://localhost:8000/api/v1/health || exit 1 