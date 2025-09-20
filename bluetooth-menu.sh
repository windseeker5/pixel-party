#!/bin/bash

echo "================================"
echo "   Bluetooth Audio Switcher"
echo "================================"
echo ""

# Turn on Bluetooth
bluetoothctl power on >/dev/null 2>&1

# Start scanning in background
echo "Scanning for Bluetooth devices..."
bluetoothctl scan on >/dev/null 2>&1 &
SCAN_PID=$!

echo "Waiting for device names to resolve (10 seconds)..."
echo ""

# Wait longer for names to be discovered
sleep 10

# Kill the scan
kill $SCAN_PID 2>/dev/null

echo "Available Bluetooth Devices:"
echo "========================================"

# Get paired devices first
echo ""
echo "PAIRED DEVICES:"
echo "----------------------------------------"
paired_count=0
mapfile -t paired_devices < <(bluetoothctl paired-devices 2>/dev/null)

for device in "${paired_devices[@]}"; do
    if [ ! -z "$device" ]; then
        mac=$(echo "$device" | awk '{print $2}')
        # Get the actual name from bluetoothctl info
        name=$(bluetoothctl info "$mac" 2>/dev/null | grep "Name:" | cut -d: -f2- | sed 's/^ *//')
        if [ -z "$name" ]; then
            name=$(echo "$device" | cut -d' ' -f3-)
        fi
        connected=$(bluetoothctl info "$mac" 2>/dev/null | grep "Connected: yes" > /dev/null && echo "[CONNECTED]" || echo "")

        ((paired_count++))
        printf "%2d. %-30s (MAC: %s) %s\n" "$paired_count" "$name" "$mac" "$connected"
        all_devices+=("$mac|$name")
    fi
done

# Get all discovered devices
echo ""
echo "DISCOVERED DEVICES:"
echo "----------------------------------------"
discover_count=$paired_count

# Use scan results to get better names
mapfile -t discovered < <(bluetoothctl devices | grep -v "^\[")

for device in "${discovered[@]}"; do
    mac=$(echo "$device" | awk '{print $2}')

    # Skip if already in paired list
    if [[ " ${paired_devices[@]} " =~ " Device $mac " ]]; then
        continue
    fi

    # Try to get the real name from info
    real_name=$(bluetoothctl info "$mac" 2>/dev/null | grep "Name:" | cut -d: -f2- | sed 's/^ *//')

    # If no name from info, try from scan
    if [ -z "$real_name" ] || [ "$real_name" = "$mac" ]; then
        real_name=$(echo "$device" | cut -d' ' -f3-)
    fi

    # Skip if still just a MAC address
    if [[ "$real_name" =~ ^[0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}$ ]]; then
        real_name="Unknown Device ($mac)"
    fi

    ((discover_count++))
    printf "%2d. %-30s (MAC: %s)\n" "$discover_count" "$real_name" "$mac"
    all_devices+=("$mac|$real_name")
done

# Store total count
total_devices=$discover_count

echo ""
read -p "Enter device number (or 'q' to quit): " choice

# Check if user wants to quit
if [ "$choice" = "q" ]; then
    exit 0
fi

# Validate input
if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "$total_devices" ]; then
    echo "Invalid selection!"
    exit 1
fi

# Get selected device MAC and name
selected="${all_devices[$((choice-1))]}"
mac=$(echo "$selected" | cut -d'|' -f1)
name=$(echo "$selected" | cut -d'|' -f2)

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