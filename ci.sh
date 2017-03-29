#!/bin/bash

# If jenkins sets the branch, listen to it.
branch=${GIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}
imgtag=${branch#*/}

docker_opts=""

if [ $(docker version -f '{{.Server.Experimental}}') == "true" ]; then
  echo "Docker experimental found, let's squash for smaller image!'"
  docker_opts="${docker_opts} --squash=true"
fi

docker build ${docker_opts} --pull -t partup/kong-ecs:$imgtag .

tag=$(git describe --exact-match 2>/dev/null || echo "")
if [ $tag ]; then
  docker tag partup/kong-ecs:$imgtag partup/kong-ecs:$tag
  docker push partup/kong-ecs:$tag
fi

docker push partup/kong-ecs:$imgtag
