# Sawtooth Cookie Jar C++ Transaction Processor
Sawtooth Transaction Processor written in C++ for cookie jar transaction family

## Building and running the C++ transaction processor

The Sawtooth C++ SDK is new and under development.
It requires the Sawtooth `nightly` (not `stable`) build repositories and
`libprotobuf.so`.
To install the nightly build, see
https://sawtooth.hyperledger.org/docs/core/releases/latest/app_developers_guide/ubuntu.html

To build and run this C++ TP, follow the instructions in the top-level
[README.md file](../README.md)
under "Docker Usage", except run the following `docker-compose`
command to build the C++ transaction processor and to start the validator:

```bash
sudo docker-compose -f docker-compose-cxx.yaml up --build
```
The `docker-compose-cxx.yaml` file is the same as the `docker-compose.yaml` file for Python except it builds the C++ transaction processor (using script `cxxprocessor/build.sh`) and starts the C++ TP.

