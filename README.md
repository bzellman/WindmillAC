# WindmillAC Home Assistant Integration

This integration creates a climate entity to connect your Windmill AC units into Home Assistant, allowing you to control temperature, fan speed, and other settings directly from your Home Assistant dashboard.

> **Note**: This is not an official integration. It is not associated, maintained, supported, or endorsed by Windmill. Windmill is a young company, their tech might change, and this integration might break. Use at your own risk.

## Prerequisites

- Home Assistant installed and running
- A Windmill AC unit with access to the [Windmill Air Dashboard](https://dashboard.windmillair.com)
- HACS (Home Assistant Community Store) installed

## Step 1: Install HACS (if you haven't already)

HACS is the Home Assistant Community Store that allows you to easily install custom integrations like this one.

**If you already have HACS installed, skip to Step 2.**

1. **Install HACS** by following the official installation guide: [HACS Installation](https://hacs.xyz/docs/use/download/download/)
2. **Restart Home Assistant** after HACS installation
3. **Configure HACS** by going to Settings → Devices & Services → Add Integration → HACS
4. Follow the GitHub authentication process when prompted

## Step 2: Add This Repository to HACS

1. Open Home Assistant and navigate to **HACS** (usually in the sidebar)
2. Click on **Integrations**
3. Click the **three dots menu** (⋮) in the top right corner
4. Select **Custom repositories**
5. In the dialog that opens:
   - **Repository URL**: `https://github.com/bzellman/WindmillAC`
   - **Category**: Select "Integration"
6. Click **Add**

## Step 3: Install the WindmillAC Integration

1. In HACS → Integrations, search for "WindmillAC"
2. Click on the **WindmillAC** integration
3. Click **Download**
4. **Restart Home Assistant** (this is important!)

## Step 4: Add the Integration to Home Assistant

Installing the repository through HACS doesn't automatically add it to your Home Assistant configuration.

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration** (+ button in bottom right)
3. Search for "WindmillAC" 
4. Click on **WindmillAC** when it appears
5. You'll be prompted to configure the integration

## Step 5: Configure Your Windmill AC Device

To complete the setup, you'll need your device's Auth Token:

1. **Get your Auth Token**:
   - Go to the [Windmill Air Dashboard](https://dashboard.windmillair.com)
   - Navigate to the **"Devices"** tab
   - Your Auth Token should be visible there

2. **Complete the integration setup**:
   - Enter your Auth Token when prompted in the integration configuration
   - Give your device a friendly name (optional)
   - Click **Submit**

## Step 6: Verify Installation

After successful configuration:

1. Go to **Settings** → **Devices & Services**
2. You should see your Windmill AC listed under the WindmillAC integration
3. Your AC should now appear as a climate entity in Home Assistant
4. You can find it in **Settings** → **Devices & Services** → **Entities** or add it to your dashboard

## Troubleshooting

**Integration doesn't appear in Add Integration menu:**
- Make sure you restarted Home Assistant after downloading from HACS
- Check that the repository was properly added to HACS

**Can't copy Auth Token:**
If clicking on the Auth Token doesn't copy it (like it says it will) try one of the following:
- Opening developer tools and finding the value of your token in plain text using the inspect element tool
- Go to the windmill phone app, About>Send Logs. Email yourself the log file. Search for 'deviceToken' in the log file.
- Use an OCR copy tool like the one in Windows PowerToys (it might mistake zero for O or 1 for L so double check)

**Climate entity not responding:**
- Verify your Auth Token is correct
- Check that your Windmill AC is online and connected to Wi-Fi
- Try reloading the integration: Settings → Devices & Services → WindmillAC → three dots → Reload

**Error Failed to get pin value for V1**

This might occur if something wasn't right the first time you added the device. Try adding a second device (step 5 above) and then if that works, delete the one throwing the error afterward. 

## Support & Contributing

This is a community-maintained integration (v1). The developer welcomes community support, feedback, and contributions. For issues or feature requests, please use the [GitHub Issues](https://github.com/bzellman/WindmillAC/issues) page.

## Disclaimer
## Notes / Changelog

2024-09: Replaced deprecated Home Assistant call `async_forward_entry_setups` with the recommended `async_setup_platforms` in `__init__.py` (see HA June 2024 dev blog).


I do my best to maintain this integration but offer no guarantee or warranty for your hardware, software, or devices. The integration may break if Windmill changes their API or technology stack.
