#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'DavidPerezMillan'

from xml.etree import ElementTree
from clases.properties import bbdd
from clases.properties import playmax
from datetime import datetime, date, time, timedelta
import logging
from logging.handlers import RotatingFileHandler

import requests
import MySQLdb
import time
import sys
import re
import inspect, os


logger = logging.getLogger("try")
logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s - %(name)-12s - [%(levelname)s] - %(message)s")
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')

handlerFile = RotatingFileHandler("%s/log/iota-play-back.log" %(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), maxBytes=5e+6, backupCount=5)
handlerFile.setFormatter(formatter)
handlerFile.setLevel(logging.DEBUG)
logger.addHandler(handlerFile)

handlerFileError = RotatingFileHandler("%s/log/error-iota-play-back.log" %(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), maxBytes=5e+6, backupCount=5)
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
sid = None

def login():
    logger.debug("Start login")
    global sid
    
    params = {"model":"login","apikey":playmax.apikey,"username":playmax.user, "password":playmax.password}
    
    try:
        # Authenticate
        response = session.get("https://playmax.mx/ucp.php", params= params)
        # logger.debug( "Login : %s"  %(response.status_code))
        # logger.debug( "Login : %s"  %(response.text))
        
        data = ElementTree.fromstring(response.content)
        sid=data.find("UserInfo/Sid").text
        
    except Exception as e:
        logger.error(str(e))
        
    logger.debug("End login %s" %(sid))

def capitulos():
    logger.debug("Start capitulos")
    global sid
    
    try:
        params= {"apikey":playmax.apikey,"sid":sid}
        logger.debug(params)

        response = session.get("https://playmax.mx/tusfichas.php", params= params)
        # logger.debug( "Login : %s"  %(response.status_code))
        # logger.info( "Login : %s"  %(response.text))
        
        
        #Capitulos/Slope
        data = ElementTree.fromstring(response.content)
        items = data.findall("Capitulos/Slope/Ficha")
        logger.info("Numero de series para ver %d" %(len(items)))
        for item in items:
            logger.info("Playmax id : %s -- Playmax idCapitulo : %s" %(item.find("Id").text,item.find("IdCapitulo").text))
            idcap = {"ficha":item.find("Id").text,"cid" : item.find("IdCapitulo").text}
            # recuperamos el enlace
            link = getEnlaces(idcap)
            if (link):
                # recuperamos el id de la BBDD 
                id = find4Cap(item)
                logger.info("Buscamos el id: %s" %(id))
                if (id):
                    # grabamos
                    add([id,link])
            
            
    except Exception as e:
        logger.error(str(e))      
  
    logger.debug("End Capitulos")
  
def getEnlaces(idcap):
    logger.debug("Start enlaces : %r" %(idcap))
    global sid
    
    itemResponse = None
    try:
        params= {"apikey":playmax.apikey,"sid":sid}
        params.update(idcap)
        logger.debug(params)
        
        response = session.get("https://playmax.mx/c_enlaces_n.php", params=params)
        # logger.debug( "Login : %s"  %(response.status_code))
        # logger.debug( "Login : %s"  %(response.text))
        
        
        #Capitulos/Slope
        data = ElementTree.fromstring(response.content)
        itemResponse = searchandfilter(data)
        
    except    Exception as e:
        logger.error(str(e))
    
    logger.debug("End enlaces return : %s" %(itemResponse))    
    return itemResponse

def searchandfilter(data):
    logger.debug("Start searchandfilter : %r" %(data))
    global sid
    itemResponse = None
    try:
        items = data.findall("Online/Item")
        for item in items:
            if (item.find("Host").text == "streamcloud" or item.find("Host").text == "powvideo" ):
                if (item.find("Lang").text == "Castellano" and int(item.find("Rating").text)>=0):
                    logger.info("%s -- %s -- %s" %(item.find("Host").text,item.find("Url").text.strip(), item.find("Rating").text))
                    if (itemResponse is None or int(itemResponse.find("Rating").text)<int(item.find("Rating").text)):
                        itemResponse = item
            
    except    Exception as e:
        logger.error(str(e))

    logger.info("End searchandfilter return : %s -- %s" %(itemResponse.find("Url").text.strip(), itemResponse.find("Rating").text))    
    return itemResponse.find("Url").text.strip()

def find4Cap(item):
    logger.debug("Start enlaces : %r" %(item))
    
    indicador = ["%"+item.find("Title").text.replace(" ", "%")+"%"] 
    tempCap = item.find("Capitulo").text.split("X")
    indicador.extend(tempCap)
    idEpisode = None
    
    try:
        x.execute("SELECT id FROM temporadas where serie like '%s' and season = '%s' and episode = '%s'" %(indicador[0],indicador[1],indicador[2]))
        res = x.fetchall()
        idEpisode = res[0][0]
    except    Exception as e:
        logger.error( str(e))
        conn.rollback()
    
    logger.debug("End find4Cap return : %s" %(idEpisode))        
    return idEpisode
    
def add(instancia):
    logger.debug("Start find4Cap : %r" %(instancia))
    logger.debug( time.strftime('%Y-%m-%d %H:%M:%S'))
    try:
        x.execute("""INSERT INTO enlaces(episode,type,link,actualizacion) VALUES (%d,%d,'%s','%s' )""" %(instancia[0],99, instancia[1], time.strftime('%Y-%m-%d %H:%M:%S')))
        logger.info("ADD {} -- {}".format(instancia[1],time.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except    Exception as e:
        logger.error( str(e))
        conn.rollback()
    
        
if __name__ == '__main__':
    logger.info(time.strftime('%Y-%m-%d %H:%M:%S'))
    login()
    capitulos()
    
    
    
'''    

def notificaciones():    
    try:
        params= {"apikey":playmax.apikey,"sid":sid}
        
        response = session.get("https://playmax.mx/c_notificaciones.php", params=params)
        # logger.debug( "Login : %s"  %(response.status_code))
        # logger.info( "Login : %s"  %(response.text))
        
        data = ElementTree.fromstring(response.content)
        items = data.findall("Notifications/Item")
        for item in items:
            logger.info("%s -- %s  -- %s" %(item.find("Title").text,item.find("Text").text, item.find("Viewed").text))
        
    except    Exception as e:
        logger.error(str(e))    

'''    