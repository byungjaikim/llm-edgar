import logging

def setup_logger(log_file_path):
    # Create a logger object
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)

    # Create a file handler with the specified log file path
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger