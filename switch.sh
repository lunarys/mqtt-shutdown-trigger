#!/bin/bash


if [ "$1" == "--help" ] || [ "$1" == "-h" ] || [ "$1" == "help"]; then
	echo "Usage: $0 <disable|enable|hold|continue> [ON|OFF] [name]"
	exit 0
fi

op="${1:-"switch-hold"}"
dir="/etc/mqtt-integration/shutdown-service"
disable="disable"
hold="hold"
disable_file="$dir/$disable"
hold_file="$dir/$hold"

function switch {
	local mode="$1"
	local currfile="$2"

	if [ -z "$mode" ]; then
		if [ -f "$currfile" ]; then
			local mode=OFF
		else
			local mode=ON
		fi
	fi

	if [ "$mode" == "ON" ]; then
		echo " -> ON"
		touch $currfile
	elif [ "$mode" == "OFF" ]; then
		echo " -> OFF"
		rm $currfile
	else
		echo "Mode unknown: $mode"
	fi

}

function switch-enable {
	local mode="$1"
	local currfile="$disable_file"

	if [ -z "$mode" ]; then
		if [ -f "$currfile" ]; then
			local mode=OFF
		else
			local mode=ON
		fi
	fi

	echo "Switching disable flag:"
	switch "$mode" "$currfile"
}

function switch-hold {
	local mode="$1"
	local name="$2"
	if [ -z "$name" ]; then
		local currfile="$hold_file"
	else
		local currfile="${hold_file}-${name}"
	fi

	echo "Switching hold flag:"
	switch "$mode" "$currfile"
}

case "$op" in
	# Default action
	"switch-hold")
		switch-hold ""
		;;
	# Explicit actions
	"disable")
		switch-enable ON
		;;
	"enable")
		switch-enable OFF
		;;
	"hold")
		switch-hold ON $2
		;;
	"continue" | "unhold")
		switch-hold OFF $2
		;;
	*)
esac
