#!/bin/bash
# $1 image value you want to replace
# $2 is the file you want to edit
sed -i "" "/^\(version: \).*/s//\1$1/" $2