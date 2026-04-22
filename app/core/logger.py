from loguru import logger
import sys

# Remove default logger
logger.remove()

# Console logging
logger.add(
    sys.stdout,
    format="{time} | {level} | {message}",
    level="INFO"
)

# File logging (creates logs/app.log automatically)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)