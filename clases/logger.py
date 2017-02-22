class logger:


    loggerTime = logging.getLogger("timer")
    loggerTime.setLevel(logging.INFO)
    formatterTime = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] - %(message)s")
    
    handlerLoggerTimeFile = RotatingFileHandler("%s/log/time.log" %(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), maxBytes=5e+6, backupCount=5)
    handlerLoggerTimeFile.setFormatter(formatterTime)
    #handlerLoggerTime.setLevel(logging.DEBUG)
    loggerTime.addHandler(handlerLoggerTimeFile)
    
    handlerloggerTimeConsole = logging.StreamHandler(sys.stdout)
    handlerloggerTimeConsole.setFormatter(formatterTime)
    #handlerloggerTimeConsole.setLevel(logging.INFO)
    loggerTime.addHandler(handlerloggerTimeConsole)
    
    
    
    logger = logging.getLogger("launch")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] - %(message)s")
    
    handlerFile = RotatingFileHandler("log/pordede.log", maxBytes=5e+6, backupCount=5)
    handlerFile.setFormatter(formatter)
    handlerFile.setLevel(logging.DEBUG)
    logger.addHandler(handlerFile)
    
    handlerFileError = RotatingFileHandler("log/pordedeError.log", maxBytes=5e+6, backupCount=5)
    handlerFileError.setFormatter(formatter)
    handlerFileError.setLevel(logging.ERROR)
    logger.addHandler(handlerFileError)
    
    handlerConsole = logging.StreamHandler(sys.stdout)
    handlerConsole.setFormatter(formatter)
    handlerConsole.setLevel(logging.INFO)
    logger.addHandler(handlerConsole)