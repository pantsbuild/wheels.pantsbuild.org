#!/bin/bash
# Copyright 2024 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

output_dir="$1"
if [ -z "${output_dir}" ]; then
  echo "usage: $0 OUTPUT_DIRECTORY" 1>&2
  exit 1
fi
if [ -e "${output_dir}" ]; then
    echo "ERROR: Output directory exists. This script requires that it not exist already." 1>&2
    exit 1
fi
mkdir -p "${output_dir}"

set -xeo pipefail

# Generate the Pants PyPi-compatible index.
./generate_index.pex \
    --url-path-prefix=/simple \
    "${output_dir}/public/simple"

# Serve a copy of the generated index on port 8080.
python3.9 -m http.server -d "${output_dir}/public" --bind 127.0.0.1 8080 &
http_server_pid="$!"

# Setup another virtual environment in temporary directory and install a version of Pants into it.
# Note: The Python version (e.g., 3.9) must match the Python version required by the version of Pants
#  to be installed as a test, or else Pip will otherwise ignore the Pants version and fail.
pants_venv_dir="${output_dir}/pants-venv"
python3.9 -m venv "${pants_venv_dir}"
"${pants_venv_dir}/bin/pip" install -vv \
    --extra-index-url=http://127.0.0.1:8080/simple/ \
    pantsbuild.pants==2.24.1

# Kill the server explicitly so the test does not hang waiting for it to exit.
kill -9 "$http_server_pid"

# Verify that the Pants console script is in the expected location.
if [ ! -f "${pants_venv_dir}/bin/pants" ]; then
    echo "TEST FAILED: Expected the `pants` console script to be installed into the virtual environment's `bin` directory." 1>&2
    exit 1
fi

# Verify that the Pants version file is in the expected location.
if [ ! -f "${pants_venv_dir}/lib/python3.9/site-packages/pants/version.py" ]; then
    echo "TEST FAILED: Expected the Pants `version.py` to be installed into the virtual environment's site-packages." 1>&2
    exit 1
fi

echo "TEST SUCCESS!"
