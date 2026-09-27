#!/bin/bash

git log --format='%aN' | sort -u | while read name; do echo -en "$name\t"; git log --author="$name" --pretty=tformat: --numstat | awk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf "Added: %s, Removed: %s, Total: %s\n", add, subs, loc }' -; done

