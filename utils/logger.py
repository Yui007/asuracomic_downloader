import logging
import colorlog

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a colored logger.
    """
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s:%(reset)s %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    )

    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate logs in parent loggers
    logger.propagate = False

    return logger