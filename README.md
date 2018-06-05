# sawtooth-cookiejar
A simple Sawtooth "cookiejar" Transaction Family example (processor + client)

# Introduction

This is a minimal example of a Sawtooth 1.0 application.
This example demonstrates a simple use case, where a baker creates or eats one or more cookies.

A baker can:
1. bake one or more cookies to add to the cookie jar
2. eat one or more cookies in the cookie jar
3. count the cookies in the cookie jar

The cookie jar is identified by "mycookiejar" with a corresponding private key.
The cookie jar count is stored at an address derived from a prefix
(the "cookiejar" Transaction Family namespace) and
the SHA-512 hash of "mycookiejar".

# Components
The Python application is built in two parts:
1. The client application is written in two parts: _client.py file representing the backend stuff and the _cli.py representing the frontend stuff. The example is built by using the setup.py file located in one directory level up.

2. The Transaction Processor is written in Python.

**NOTE**

# Pre-requisites

This example uses docker-compose and Docker containers. If you do not have these installed please follow the instructions here: https://docs.docker.com/install/

**NOTE**

The preferred OS environment is Ubuntu 16.04.3 LTS x64.
Although other Linux distributions which support Docker should work.

# Building containers
To build TP code for Python and run the cookiejar.py example:

```bash
sudo docker-compose up --build
```

# Usage

To launch the client shell container, you could do this:
```bash
sudo docker exec -it cookiejar-client bash
```

You can locate the correct Docker client container name by using
`sudo docker ps`.

Sample command usage:

```bash
cookiejar.py bake 100 # Add 100 cookies to the cookie jar
cookiejar.py eat 50 # Remove 50 cookies from the cookie jar
cookiejar.py count # Display the number of cookies in the cookie jar

```

# License
This example and Hyperledger Sawtooth software are licensed under the [Apache License Version 2.0](LICENSE) software license.
