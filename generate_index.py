import os

import github


def main() -> str:
    gh = github.Github(auth=github.Auth.Token(os.environ["GH_TOKEN"]))
    repo = gh.get_repo("pantsbuild/pants")
    releases = repo.get_releases()
    index = "\n".join(
        [
            "<html>",
            "<body>",
            "<h1>Links for Pantsbuild Wheels</h1>",
            *(
                f'<a href="{asset.browser_download_url}">{asset.name}</a><br>'
                for release in releases
                if release.tag_name.startswith("release_2")
                for asset in release.assets
                if asset.name.endswith(".whl")
            ),
            "</body>",
            "</html>",
        ]
    )
    return index


if __name__ == "__main__":
    print(main())