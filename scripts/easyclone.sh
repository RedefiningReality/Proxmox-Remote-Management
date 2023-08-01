#!/bin/bash

# Runs clone with a set of predefined arguments
# $1 -> 1st command line argument
# $2 -> 2nd command line argument
# ...
# ex. easyclone doge P@$$w0rd! 7 => create a clone for user doge with password P@$$w0rd! and assign it a network bridge with subnet 192.168.7.0/24
clone 450-455 -c $1 -i 500 -u -p $2 -g Seminar -b -bs 192.168.$3.0/24 -bv 450-452,454,402 -v
