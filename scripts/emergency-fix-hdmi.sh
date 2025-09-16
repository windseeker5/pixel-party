#!/bin/bash

# Emergency HDMI fix script for Raspberry Pi SD card

echo "🔧 Emergency HDMI Fix for Raspberry Pi"
echo "======================================"

# Find boot partition
BOOT_PART=$(lsblk | grep -E 'sd[a-z][0-9]' | grep -E '[0-9]+M' | head -1 | awk '{print $1}')
if [ -z "$BOOT_PART" ]; then
    echo "❌ Cannot find SD card boot partition"
    exit 1
fi

BOOT_DEV="/dev/$BOOT_PART"
echo "🔍 Found boot partition: $BOOT_DEV"

# Mount it
MOUNT_POINT="/run/media/$USER/$(lsblk -no LABEL $BOOT_DEV 2>/dev/null || echo 'boot')"
echo "📁 Mounting $BOOT_DEV..."

udisksctl mount -b $BOOT_DEV

# Find actual mount point
ACTUAL_MOUNT=$(mount | grep $BOOT_DEV | awk '{print $3}')
if [ -z "$ACTUAL_MOUNT" ]; then
    echo "❌ Failed to mount boot partition"
    exit 1
fi

echo "✅ Mounted at: $ACTUAL_MOUNT"

CONFIG_FILE="$ACTUAL_MOUNT/config.txt"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ config.txt not found at $CONFIG_FILE"
    exit 1
fi

echo "📝 Backing up original config.txt..."
cp "$CONFIG_FILE" "$CONFIG_FILE.backup"

echo "🔧 Applying emergency HDMI fixes..."

# Create a minimal, highly compatible config
cat > "$CONFIG_FILE" << 'EOF'
# Emergency HDMI Configuration - Maximum Compatibility
# This should work on almost any display

# Use the most compatible video driver
dtoverlay=vc4-fkms-v3d
initramfs initramfs-linux.img followkernel

# Force HDMI output even if no display detected
hdmi_force_hotplug=1
hdmi_drive=2

# Use safe HDMI settings
hdmi_safe=1

# Boost HDMI signal (maximum compatible level)
config_hdmi_boost=4

# Disable overscan (black borders)
disable_overscan=1

# Set a specific resolution that usually works
hdmi_group=2
hdmi_mode=82

# GPU memory
gpu_mem=128

# Enable UART for debugging
enable_uart=1

# Auto-detect cameras and displays
camera_auto_detect=1
display_auto_detect=1

# Pi 4 specific settings
[pi4]
arm_boost=1
EOF

echo "✅ Emergency config applied!"
echo ""
echo "📋 What was changed:"
echo "• Switched to safest video driver (vc4-fkms-v3d)"
echo "• Enabled hdmi_safe=1 (safest HDMI mode)"
echo "• Set specific resolution: 1080p 60Hz"
echo "• Force HDMI output even if no display detected"
echo ""
echo "💾 Original config backed up as config.txt.backup"
echo ""
echo "🚀 Next steps:"
echo "1. Safely eject SD card: udisksctl unmount -b $BOOT_DEV"
echo "2. Insert into Pi and boot"
echo "3. Should see desktop without black screen"
echo ""

# Unmount
echo "🔄 Unmounting SD card..."
udisksctl unmount -b $BOOT_DEV
echo "✅ SD card ready - try booting now!"