from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import sys
from packaging.utils import parse_wheel_filename
from urllib.parse import urlparse
from textwrap import dedent

import github

##
## Output a PEP 503 compliant package repository for Pants wheels.
## See https://peps.python.org/pep-0503/
##


def get_pants_python_packages(gh: github.Github) -> tuple[str, ...]:
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
        name, version, build_tag, tags = parse_wheel_filename(asset.name)
        packages[name][version].append(asset)
    
    return packages


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--url-path-prefix", default="/", action="store")
    parser.add_argument("output_dir", action="store")
    opts = parser.parse_args(args)

    github_client = github.Github(auth=github.Auth.Token(os.environ["GH_TOKEN"]))
    packages = get_pants_python_packages(github_client)
    package_names = sorted(packages.keys())

    prefix = opts.url_path_prefix

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
            f.write(f"""<li><a href="{prefix}{package_name}/">{package_name}</li>\n""")
        f.write(dedent(
            """\
            </ul>
            </body>
            </html>
            """
        ))

    # http://repository.example.com/simple/PACKAGE_NAME/
    for package_name in package_names:
        package = packages[package_name]
    
        package_output_dir = output_dir / package_name
        package_output_dir.mkdir()

        package_version_keys = sorted(package.keys())

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
                package_version_assets = package[package_version_key]
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
