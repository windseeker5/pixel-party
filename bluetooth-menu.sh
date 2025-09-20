#!/bin/bash

echo "================================"
echo "   Bluetooth Audio Switcher"
echo "================================"
echo ""

# Turn on Bluetooth
bluetoothctl power on >/dev/null 2>&1

# Scan for devices (5 seconds)
echo "Scanning for Bluetooth devices (5 seconds)..."
echo "This will find both paired and new devices nearby"
echo ""
timeout 5 bluetoothctl scan on >/dev/null 2>&1

# Get list of all devices (paired and nearby)
echo ""
echo "Available Bluetooth Devices:"
echo "----------------------------"

# Store devices in array
mapfile -t devices < <(bluetoothctl devices | grep -v "^\[")

# Display numbered list with both name and MAC
for i in "${!devices[@]}"; do
    mac=$(echo "${devices[$i]}" | awk '{print $2}')
    name=$(echo "${devices[$i]}" | cut -d' ' -f3-)

    # Check if device is connected
    connected=$(bluetoothctl info "$mac" 2>/dev/null | grep "Connected: yes" > /dev/null && echo "[CONNECTED]" || echo "")

    # Display with MAC address
    printf "%2d. %-30s (MAC: %s) %s\n" "$((i+1))" "$name" "$mac" "$connected"
done

echo ""
read -p "Enter device number (or 'q' to quit): " choice

# Check if user wants to quit
if [ "$choice" = "q" ]; then
    exit 0
fi

# Validate input
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#devices[@]}" ]; then
    echo "Invalid selection!"
    exit 1
fi

# Get selected device MAC
selected="${devices[$((choice-1))]}"
mac=$(echo "$selected" | awk '{print $2}')
name=$(echo "$selected" | cut -d' ' -f3-)

echo ""
echo "Connecting to: $name"
echo "MAC: $mac"
echo ""

# Try to connect
bluetoothctl connect "$mac"

# If successful, set as default audio
if [ $? -eq 0 ]; then
    echo ""
    echo "Setting as default audio output..."
    sleep 2

    # Find the Bluetooth sink and set as default
    sink=$(pactl list short sinks | grep bluez | awk '{print $2}')
    if [ ! -z "$sink" ]; then
        pactl set-default-sink "$sink"
        echo "✓ Audio output switched to $name"
    else
        echo "Note: Device connected but may need manual audio routing"
    fi
else
    echo "Failed to connect. Device may need pairing first."
    echo "Run: bluetoothctl pair $mac"
fi