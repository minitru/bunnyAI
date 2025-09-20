# Jessica's Crabby Editor - Autostart Setup Guide

This guide provides multiple methods to automatically start Jessica's Crabby Editor after a Linux system reboot.

## Method 1: Systemd Service (Recommended)

### Step 1: Copy the service file
```bash
sudo cp bunny-ai.service /etc/systemd/system/
```

### Step 2: Update the service file
Edit `/etc/systemd/system/bunny-ai.service` and update:
- `User=sean` → `User=your_username`
- `Group=sean` → `Group=your_group`
- `/Users/sean/src/bunnyAI` → `/path/to/your/bunnyAI`

### Step 3: Reload and enable the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable bunny-ai.service
sudo systemctl start bunny-ai.service
```

### Step 4: Check status
```bash
sudo systemctl status bunny-ai.service
```

### Useful commands:
```bash
# Start the service
sudo systemctl start bunny-ai.service

# Stop the service
sudo systemctl stop bunny-ai.service

# Restart the service
sudo systemctl restart bunny-ai.service

# View logs
sudo journalctl -u bunny-ai.service -f

# Disable autostart
sudo systemctl disable bunny-ai.service
```

## Method 2: Crontab @reboot

### Step 1: Edit crontab
```bash
crontab -e
```

### Step 2: Add this line
```bash
@reboot /Users/sean/src/bunnyAI/autostart.sh
```

### Step 3: Check crontab
```bash
crontab -l
```

## Method 3: Startup Script in /etc/rc.local

### Step 1: Make rc.local executable
```bash
sudo chmod +x /etc/rc.local
```

### Step 2: Add to /etc/rc.local
```bash
sudo nano /etc/rc.local
```

Add this line before `exit 0`:
```bash
/Users/sean/src/bunnyAI/startup.sh &
```

## Method 4: Desktop Environment Autostart

### For GNOME/KDE/XFCE:
1. Create desktop file: `~/.config/autostart/bunny-ai.desktop`
2. Add content:
```ini
[Desktop Entry]
Type=Application
Name=Jessica's Crabby Editor
Comment=Literary Analysis AI
Exec=/Users/sean/src/bunnyAI/startup.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

## Environment Setup

### Ensure .env file exists
Create `.env` file in the project directory with:
```bash
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_MAX_TOKENS=3000
OPENROUTER_TEMPERATURE=0.3
```

### Virtual Environment
Ensure the virtual environment is properly set up:
```bash
cd /Users/sean/src/bunnyAI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Testing Autostart

### Test the startup script manually:
```bash
cd /Users/sean/src/bunnyAI
./startup.sh
```

### Test systemd service:
```bash
sudo systemctl start bunny-ai.service
sudo systemctl status bunny-ai.service
```

### Check if service is running:
```bash
curl http://localhost:7777/api/status
```

## Troubleshooting

### Check logs:
- Systemd: `sudo journalctl -u bunny-ai.service -f`
- Crontab: Check `/Users/sean/src/bunnyAI/startup.log`
- Manual: Run `./startup.sh` and check output

### Common issues:
1. **Permission denied**: Check file permissions and user ownership
2. **Virtual environment not found**: Ensure venv directory exists
3. **Port already in use**: Check if another instance is running
4. **Environment variables**: Ensure .env file is properly formatted

### Kill existing processes:
```bash
# Find and kill existing processes
ps aux | grep python | grep bunnyAI
kill -9 <PID>

# Or kill by port
sudo lsof -ti:7777 | xargs kill -9
```

## Security Notes

- The systemd service includes security restrictions
- Consider running as a dedicated user (not root)
- Ensure API keys are properly secured in .env file
- The service binds to 0.0.0.0:7777 - consider firewall rules

## Recommended Approach

For production servers, use **Method 1 (Systemd)** as it provides:
- Automatic restart on failure
- Proper logging
- Security restrictions
- Easy management commands
- Integration with system monitoring
