# Discord.py Local Repository Update Guide

## Overview
This project uses a local clone of discord.py to access unreleased fixes for voice connection issues (WebSocket 4006 error). This guide outlines the best practices for updating and maintaining the local discord.py repository.

## Current Setup
- **Location**: `/Users/sawyer/github/python-bots/discord.py/`
- **Version**: 2.6.0a (includes voice v8 protocol fix)
- **Fix Commit**: `2175bd51c0d0c2817e69a708e507108f3bc902bd`
- **Used by**: All three bots (music, mtg-card-bot, clippy)

## Update Strategy

### Option 1: Safe Update (Recommended)
This approach preserves the current working state while testing updates.

```bash
# 1. Navigate to your main project directory
cd /Users/sawyer/github/python-bots

# 2. Create a backup of current working discord.py
cp -r discord.py discord.py.backup

# 3. Navigate to discord.py directory
cd discord.py

# 4. Fetch latest changes from upstream
git fetch origin

# 5. Check what's new (review commit messages)
git log --oneline HEAD..origin/master | head -20

# 6. Create a new branch for testing
git checkout -b update-test

# 7. Merge latest changes
git merge origin/master

# 8. Return to main project and test
cd ..
uv sync

# 9. Test each bot (with invalid tokens to check imports)
MUSIC_DISCORD_TOKEN="test" uv run --package music-bot python -c "import discord; print(f'Discord.py: {discord.__version__}')"
MTG_DISCORD_TOKEN="test" uv run --package mtg-card-bot python -c "import discord; print(f'Discord.py: {discord.__version__}')"
CLIPPY_DISCORD_TOKEN="test" uv run --package clippy-bot python -c "import discord; print(f'Discord.py: {discord.__version__}')"

# 10a. If tests pass - make update permanent
cd discord.py
git checkout master
git merge update-test
git branch -d update-test

# 10b. If tests fail - rollback
cd discord.py
git checkout master
git branch -D update-test
cd ..
rm -rf discord.py
mv discord.py.backup discord.py
```

### Option 2: Fresh Clone (Clean Slate)
When you want to start completely fresh or if the repository gets corrupted.

```bash
# 1. Navigate to main project directory
cd /Users/sawyer/github/python-bots

# 2. Backup current version (optional)
mv discord.py discord.py.old

# 3. Clone fresh copy
git clone https://github.com/Rapptz/discord.py.git

# 4. Remove git history to prevent submodule issues
cd discord.py
rm -rf .git
cd ..

# 5. Test the new version
uv sync

# Test imports as shown in Option 1 step 9

# 6. If working, remove old backup
rm -rf discord.py.old

# 7. If not working, restore backup
# rm -rf discord.py
# mv discord.py.old discord.py
```

## Version Tracking

### Check Current Discord.py Version
```bash
# Quick version check
python -c "import sys; sys.path.insert(0, 'discord.py'); import discord; print(f'Discord.py: {discord.__version__}')"

# Or check from any bot environment
uv run --package music-bot python -c "import discord; print(f'Discord.py version: {discord.__version__}')"
```

### Verify Voice Fix is Present
```bash
cd discord.py
git log --oneline --grep="voice.*v8\|4006" -5
# Should show: 2175bd51 Fix voice connection issues and upgrade to voice v8
```

### Check for Critical Changes
```bash
cd discord.py
# Check if any breaking changes to voice functionality
git log --oneline --since="1 month ago" -- discord/voice_state.py discord/gateway.py
```

## When to Update

### ✅ **Safe to Update When:**
- Minor bug fixes and improvements
- New features that don't affect voice/audio systems
- Documentation updates
- Type hint improvements

### ⚠️ **Exercise Caution When:**
- Changes to `discord/voice_state.py` or `discord/gateway.py`
- Major version bumps (2.6.x → 2.7.x)
- Breaking changes mentioned in commit messages
- Changes to audio/voice protocol handling

### 🚫 **Avoid Updating When:**
- Official 2.6.0 still not released and you have working voice connections
- Critical production deployment in progress
- Recent voice-related regressions reported in GitHub issues

## Troubleshooting Updates

### If Bots Fail to Import After Update
```bash
# 1. Check discord.py integrity
cd discord.py
python -c "import discord; print('Import successful')"

# 2. Clear UV cache and reinstall
cd ..
uv cache clean
rm -rf .venv
uv sync

# 3. Test minimal import
python -c "
import sys
sys.path.insert(0, 'discord.py')
import discord
print(f'Version: {discord.__version__}')
print('Basic import successful')
"
```

### If Voice Connections Start Failing Again
```bash
# 1. Check if voice fix commit is still present
cd discord.py
git log --oneline --grep="voice.*v8\|4006" -5

# 2. If missing, restore from backup
cd ..
rm -rf discord.py
mv discord.py.backup discord.py

# 3. Or cherry-pick the fix if needed
cd discord.py
git cherry-pick 2175bd51c0d0c2817e69a708e507108f3bc902bd
```

## Automation Script

Create a script to automate safe updates:

```bash
#!/bin/bash
# update_discord_py.sh
set -e

echo "🔄 Updating Discord.py safely..."

# Backup current version
cp -r discord.py discord.py.backup.$(date +%Y%m%d_%H%M%S)

cd discord.py

# Fetch and show changes
git fetch origin
echo "📋 Recent changes:"
git log --oneline HEAD..origin/master | head -10

echo "Continue with update? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Update cancelled"
    exit 0
fi

# Update
git merge origin/master

# Test
cd ..
echo "🧪 Testing imports..."
uv sync
if uv run --package music-bot python -c "import discord; print(f'✅ Discord.py {discord.__version__} working')"; then
    echo "✅ Update successful!"
    rm -rf discord.py.backup.*
else
    echo "❌ Update failed, restoring backup..."
    rm -rf discord.py
    mv discord.py.backup.* discord.py
fi
```

## Migration to Official Release

When discord.py 2.6.0 is officially released to PyPI:

```bash
# 1. Update all bot pyproject.toml files to use PyPI version
# Change from:
"discord.py @ file:///Users/sawyer/github/python-bots/discord.py",
# Back to:
"discord.py>=2.6.0",

# 2. Remove local repository
rm -rf discord.py

# 3. Update dependencies
uv sync

# 4. Test all bots work with official release
```

## Best Practices

1. **Always backup** before updating
2. **Test thoroughly** in development before production
3. **Monitor Discord.py GitHub** for voice-related issues
4. **Keep update notes** in this file for team reference
5. **Verify voice fix presence** after each update
6. **Use semantic versioning** to track your local changes

## Emergency Rollback

If everything breaks:

```bash
# Nuclear option - restore to known working state
rm -rf discord.py .venv
git checkout HEAD -- discord.py  # If you committed a working version
# Or restore from backup
# Or re-clone and remove .git as shown in Option 2
```

Remember: The goal is to maintain voice connection stability while getting security and bug fixes from upstream Discord.py development.