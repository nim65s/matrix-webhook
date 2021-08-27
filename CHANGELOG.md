# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- add grafana formatter
- add formatted_body to bypass markdown with direct
  [matrix-custom-HTML](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-message-msgtypes)
- allow "key" to be passed as a parameter
- allow "room_id" to be passed as a parameter or with the data
- rename "text" to "body".
- Publish releases also on github from github actions
- fix tests for recent synapse docker image

## [3.1.1] - 2021-07-18

## [3.1.0] - 2021-07-18

- Publish on PyPI & Docker Hub with Github Actions
  in [#10](https://github.com/nim65s/matrix-webhook/pull/10)
  by [@nim65s](https://github.com/nim65s)

## [3.0.0] - 2021-07-18

- Simplify code
  in [#1](https://github.com/nim65s/matrix-webhook/pull/1)
  by [@homeworkprod](https://github.com/homeworkprod)
- Update aiohttp use and docs
  in [#5](https://github.com/nim65s/matrix-webhook/pull/5)
  by [@svenseeberg](https://github.com/svenseeberg)
- Setup Tests, Coverage & CI ; update tooling
  in [#7](https://github.com/nim65s/matrix-webhook/pull/7)
  by [@nim65s](https://github.com/nim65s)
- Setup argparse & logging
  in [#8](https://github.com/nim65s/matrix-webhook/pull/8)
  by [@nim65s](https://github.com/nim65s)
- Setup packaging
  in [#9](https://github.com/nim65s/matrix-webhook/pull/9)
  by [@nim65s](https://github.com/nim65s)

## [2.0.0] - 2020-03-14
- Update to matrix-nio & aiohttp & markdown

## [1.0.0] - 2020-02-14
- First release with matrix-client & http.server

[Unreleased]: https://github.com/nim65s/matrix-webhook/compare/v3.1.1...master
[3.1.1]: https://github.com/nim65s/matrix-webhook/compare/v3.1.0...v3.1.1
[3.1.0]: https://github.com/nim65s/matrix-webhook/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/nim65s/matrix-webhook/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/nim65s/matrix-webhook/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/nim65s/matrix-webhook/releases/tag/v1.0.0
