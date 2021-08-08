# Publish a new release

A github actions handle the build of the release archives, and push them to PyPI and Github Releases.
To trigger it, we just need to:

1. use poetry to update the version number
2. update the changelog
3. git commit
4. git tag
5. git push
6. git push --tags


For this, an helper script is provided:

```bash
./docs/release.sh [patch|minor|major|x.y.z]
```
