import os
import asyncio
import yaml
import signal
import sys
from bot.bot import Bot

async def main():
    CONFIG_FILE = "config.yaml"
    OSTYPE = sys.platform

    # Check for config file
    if not os.path.exists(CONFIG_FILE):
        raise OSError(f"{CONFIG_FILE} not found or missing")

    # Read in config file
    with open(CONFIG_FILE, 'r', encoding='UTF-8') as CONFIG_YAML:
        CONFIG = yaml.full_load(CONFIG_YAML)

    # For now, just run the first bot (can be extended later for multiple bots)
    for bot_id, bot_config in enumerate(CONFIG, start=1):
        # Use enumeration as bot's ID
        bot_config.update({'bot_id': bot_id})
        
        bot = Bot(bot_config, OSTYPE)
        
        try:
            print(f"Starting {bot.name}...")
            await bot.start(bot.get_token())
        except KeyboardInterrupt:
            print("Received interrupt signal, shutting down...")
            await bot.close()
        except Exception as e:
            print(f"Bot encountered an error: {e}")
            await bot.close()
            raise
        finally:
            print("Bot shutdown complete.")
        
        break  # Only run first bot for now

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("Interrupt received, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutdown complete.")
