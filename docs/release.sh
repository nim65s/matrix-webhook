#!/bin/bash -eux
# ./docs/release.sh [patch|minor|major|x.y.z]

[[ $(basename "$PWD") == docs ]] && cd ..


OLD=$(poetry version -s)

poetry version "$1"

NEW=$(poetry version -s)
DATE=$(date +%Y-%m-%d)

sed -i "/^## \[Unreleased\]/a \\\n## [v$NEW] - $DATE" CHANGELOG.md
sed -i "/^\[Unreleased\]/s/$OLD/$NEW/" CHANGELOG.md
sed -i "/^\[Unreleased\]/a [v$NEW]: https://github.com/nim65s/matrix-webhook/compare/v$OLD...v$NEW" CHANGELOG.md

git add pyproject.toml CHANGELOG.md
git commit -m "Release v$NEW"
git tag -s "v$NEW" -m "Release v$NEW"
git push
git push --tags
