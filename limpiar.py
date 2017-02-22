#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'DavidPerezMillan'


from bs4 import BeautifulSoup
from clases.enlaces import enlaces
from clases.temporadas import temporadas
from clases.properties import bbdd
from clases.properties import pordede
from datetime import datetime, date, time, timedelta
import logging
from logging.handlers import RotatingFileHandler
import requests
import MySQLdb
import time
import sys
import inspect, os

logger = logging.getLogger("pordedelog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] - %(message)s")

handlerFile = RotatingFileHandler("%s/log/limpiar.log"  %(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), maxBytes=5e+6, backupCount=5)
handlerFile.setFormatter(formatter)
handlerFile.setLevel(logging.DEBUG)
logger.addHandler(handlerFile)

handlerFileError = RotatingFileHandler("%s/log/limpiarError.log"  %(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), maxBytes=5e+6, backupCount=5)
handlerFileError.setFormatter(formatter)
handlerFileError.setLevel(logging.ERROR)
logger.addHandler(handlerFileError)

handlerConsole = logging.StreamHandler(sys.stdout)
handlerConsole.setFormatter(formatter)
handlerConsole.setLevel(logging.INFO)
logger.addHandler(handlerConsole)


# configuracion BBDD
conn = MySQLdb.connect(host=bbdd.host,
                  user=bbdd.user,
                  passwd=bbdd.passwd,
                  db=bbdd.db)
x = conn.cursor()




#Variables de uso
session = requests.Session()


def onlyLogin():
    logger.debug("Hacemos onlylogin")
    try:
        # Authenticate
        req = session.post(pordede.url_login,headers=pordede.headers, data = pordede.login_data, timeout=5)
        logger.debug( "Login : %s"  %(req.status_code))
        # Try accessing a page that requires you to be logged in
        return req;
    except Exception, e:
        logger.error(str(e))
        return

def login(urlExit):
    try:
        session = requests.Session() 
    
        # Authenticate
        req = session.post(pordede.url_login,headers=pordede.headers, data = pordede.login_data, timeout=5)
        logger.debug( "Login : %s"  %(req.status_code))
        # Try accessing a page that requires you to be logged in
        req = session.get(urlExit,headers=pordede.headers,  timeout=10)
        return req;
    except Exception, e:
        logger.error(str(e))


def limpiar():
    
    
    borrarSeries()
    recuperarSeries()
    borrarEnlacesVistos()
 
 
def borrarSeries():
    try:
        x.execute("TRUNCATE TABLE series ")
        conn.commit()
        logger.info("Borrado de Series")
    except Exception, e:
        logger.error( str(e))
        conn.rollback()
   
def recuperarSeries():   
    req = session.get("http://www.pordede.com/series/following",headers=pordede.headers,  timeout=10)
    
    # Comprobamos que la petición nos devuelve un Status Code = 200
    statusCode = req.status_code
    
    # logger.debug( req.text
    
    if statusCode == 200:

        # Pasamos el contenido HTML de la web a un objeto BeautifulSoup()
        html = BeautifulSoup(req.text, "html.parser")

        
        # Obtenemos todos los divs donde estan las entradas
        entradas = html.find_all('a',{'class':'defaultLink extended'})

        # Recorremos todas las entradas para extraer el título, autor y fecha
        for entrada in entradas:
            logger.debug( entrada['href'])
            try:
                x.execute("""INSERT INTO series (serie,ruta) VALUES ('%s','%s');""" %(entrada['href'],entrada['href']))
                conn.commit()
                logger.info("Insertando %s " %(entrada['href']))
            except Exception, e:
                logger.error( str(e))
                conn.rollback()
            

    else:
        # Si ya no existe la página y me da un 400
        logger.error( " Error %s" %(statusCode))

def borrarEnlacesVistos():
    logger.debug("Borramos los enlaces vistos")
    
    try:
        x.execute("DELETE eml FROM enlaces eml LEFT JOIN temporadas tmp ON ( eml.episode = tmp.id ) WHERE tmp.status <>0")
        conn.commit()
        logger.info("Borrado de Enlaces")
    except Exception, e:
        logger.error( str(e))
        conn.rollback()
    
    

if __name__ == '__main__':
    if (onlyLogin()):
        limpiar()
        
    
   
    


