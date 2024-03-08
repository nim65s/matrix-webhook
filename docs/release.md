# Publish a new release

A github actions handle the build of the release archives, and push them to PyPI and Github Releases.
To trigger it, we just need to:

1. use poetry to update the version number
2. update the changelog
3. update version number in flake.nix
4. git commit
5. git tag
6. git push
7. git push --tags


For this, an helper script is provided:

```bash
./docs/release.sh [patch|minor|major|x.y.z]
```
