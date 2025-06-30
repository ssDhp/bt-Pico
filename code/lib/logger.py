import time

class Logger:
    LOG_INFO = 1 << 0
    LOG_WARNING = 1 << 1
    LOG_ERROR = 1 << 2
    LOG_ALL = LOG_INFO | LOG_WARNING | LOG_ERROR

    def __init__(self, log_level: int, log_file_path: str = "") -> None:
        self._log_level = log_level
        self._log_file_path = log_file_path
        if (self._log_file_path != ""):
            self._log_file = open(log_file_path, "w")

    def info(self,*args, **kwargs) -> None:
        self._print("[INFO]", *args, **kwargs)

    def warning(self,*args, **kwargs) -> None:
        self._print("[WARNING]", *args, **kwargs)
        
    def error(self,*args, **kwargs) -> None: 
        self._print("[ERROR]", *args, **kwargs)

    def _print(self,*args, **kwargs) -> None:
        args_string = [str(arg) for arg in args]
        log_string = f"{time.time()} " + f"{kwargs.get('sep', ' ')}".join(args_string) + '\n'
        if self._log_file_path != "":
            self._log_file.write(log_string)
            self._log_file.flush()
        print(*args, **kwargs)


if __name__ == "__main__":
    test_logger = Logger(Logger.LOG_ALL, log_file_path="./test_log.txt")
    test_logger.info("This a Info message.")
    test_logger.warning("This a Warning message.")
    test_logger.error("This a Error message.")