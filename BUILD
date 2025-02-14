# Copyright 2025 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_sources(name="src")

pex_binary(
    name="generate_index",
    entry_point="generate_index.py",
)

shell_source(name="shell_src", source="test_generated_index.sh")

experimental_test_shell_command(
    name="integration_test",
    execution_dependencies=[":generate_index", ":shell_src"],
    command="./test_generated_index.sh output",
    extra_env_vars=["GH_TOKEN", "PATH"],
    path_env_modify="off",
    log_output=True,
    timeout=60,
)