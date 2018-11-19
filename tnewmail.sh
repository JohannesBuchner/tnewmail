#!/bin/bash
{
	echo "called with: $*"
	python $(dirname $0)/tnewmail.py --summary "$1" --body "$2" 2>&1
} >> /tmp/tnewmail.log
