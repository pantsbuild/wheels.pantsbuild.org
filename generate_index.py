# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

import argparse
from collections import defaultdict
import os
from pathlib import Path
import sys
from typing import Any, Iterable
import github.GitReleaseAsset
from packaging.utils import parse_wheel_filename
from packaging.version import Version
from urllib.parse import urlparse
from textwrap import dedent

import github

##
## Output a PEP 503 compliant package repository for Pants wheels.
## See https://peps.python.org/pep-0503/
##


def get_pants_python_packages(gh: github.Github) -> dict[str, dict[Version, list[Any]]]:
    repo = gh.get_repo("pantsbuild/pants")
    all_releases = repo.get_releases()

    pants_wheel_assets = [
        asset
        for release in all_releases
        if release.tag_name.startswith("release_2")
        for asset in release.assets
        if asset.name.endswith(".whl")
    ]

    packages = defaultdict(lambda: defaultdict(list))

    for asset in pants_wheel_assets:
        name, version, _build_tag, _tags = parse_wheel_filename(asset.name)
        packages[name][version].append(asset)
    
    return packages


def _legacy_flat_links(packages: dict[str, dict[Version, list[Any]]]) -> tuple[str, ...]:
    return [
        f'<a href="{asset.browser_download_url}">{asset.name}</a><br>'
        for package_versions in packages.values()
        for _, version_release_assets in sorted(package_versions.items(), reverse=True)
        for asset in version_release_assets
    ]

# http://repository.example.com/simple/PACKAGE_NAME/
def _write_package_specific_index(output_dir: Path, package_name: str, package_versions: dict[Version, list[Any]]) -> None:
    package_output_dir = output_dir / package_name
    package_output_dir.mkdir()

    package_version_keys = sorted(package_versions.keys(), reverse=True)

    with open(package_output_dir / "index.html", "w") as f:
        f.write(dedent(
            f"""\
            <!DOCTYPE html>
            <html>
            <body>
            <h1>Links for Pantsbuild Wheels - {package_name}</h1>
            <ul>
            """
        ))

        for package_version_key in package_version_keys:
            package_version_assets = package_versions[package_version_key]
            package_version_assets.sort(key=lambda x: x.name)
            for asset in package_version_assets:
                f.write(f"""<li><a href="{asset.browser_download_url}">{asset.name}</a></li>\n""")
        
        f.write(dedent(
            """\
            </ul>
            </body>
            </html>
            """
        ))



def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--url-path-prefix", default="/", action="store")
    parser.add_argument("output_dir", action="store")
    opts = parser.parse_args(args)

    github_client = github.Github(auth=github.Auth.Token(os.environ["GH_TOKEN"]))
    packages = get_pants_python_packages(github_client)
    package_names = sorted(packages.keys())

    prefix = opts.url_path_prefix
    if prefix and prefix.endswith("/"):
        prefix = prefix[0:-1]

    output_dir = Path(opts.output_dir)
    if output_dir.exists():
        raise Exception(f"Output directory `{output_dir}` already exists.")
    output_dir.mkdir(parents=True)

    # http://repository.example.com/simple/
    with open(output_dir / "index.html", "w") as f:
        f.write(dedent(
            """\
            <!DOCTYPE html>
            <html>
            <body>
            <h1>Links for Pantsbuild Wheels</h1>
            <ul>
            """
        ))
        
        for package_name in package_names:
            f.write(f"""<li><a href="{prefix}/{package_name}/">{package_name}</a></li>\n""")

        f.write("\n".join(_legacy_flat_links(packages)))

        f.write(dedent(
            """\
            </ul>
            </body>
            </html>
            """
        ))

    # http://repository.example.com/simple/PACKAGE_NAME/
    for package_name in package_names:
        _write_package_specific_index(output_dir, package_name, packages[package_name])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
