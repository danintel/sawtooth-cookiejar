# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

FROM ubuntu:xenial

RUN \
 if [ ! -z $HTTP_PROXY ] && [ -z $http_proxy ]; then \
  http_proxy=$HTTP_PROXY; \
 fi; \
 if [ ! -z $HTTPS_PROXY ] && [ -z $https_proxy ]; then \
  https_proxy=$HTTPS_PROXY; \
 fi; \
 apt-get update; \
 apt-get install curl -y; \
 echo "deb http://repo.sawtooth.me/ubuntu/ci xenial universe" >> /etc/apt/sources.list \
 && curl -sSL 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x8AA7AF1F1091A5FD' | apt-key add - \
 && echo "deb http://repo.sawtooth.me/ubuntu/nightly xenial universe" >> /etc/apt/sources.list \
 && curl -sSL 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x44FC67F19B2466EA' | apt-key add - \
 && apt-get update \
 && apt-get install -y -q \
    apt-transport-https \
    build-essential \
    ca-certificates \
    maven \
    default-jre \
    default-jdk \
    git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*


EXPOSE 4004/tcp

WORKDIR /project/cookiejar/javaprocessor

CMD bash -c "./build_java_processor.sh"
