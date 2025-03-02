#!/usr/bin/env bash

cd "$(dirname "$0")"

(cd dashboard; npm run build)

docker build -t "krysa" .