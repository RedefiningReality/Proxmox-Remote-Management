#!/bin/bash

# Runs purge with a set of predefined arguments
# $1 -> 1st command line argument
# $2 -> 2nd command line argument
# ...
# ex. purge doge => remove user doge and associated virtual machines and bridges
purge $1 -u -b -bv 402 -v
