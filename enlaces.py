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
import re
import inspect, os

logger = logging.getLogger("pordedelog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] - %(message)s")

handlerFile = RotatingFileHandler("%s/log/enlaces.log" %(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), maxBytes=5e+6, backupCount=5)
handlerFile.setFormatter(formatter)
handlerFile.setLevel(logging.DEBUG)
logger.addHandler(handlerFile)

handlerFileError = RotatingFileHandler("%s/log/enlacesError.log" %(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), maxBytes=5e+6, backupCount=5)
handlerFileError.setFormatter(formatter)
handlerFileError.setLevel(logging.ERROR)
logger.addHandler(handlerFileError)

handlerConsole = logging.StreamHandler(sys.stdout)
handlerConsole.setFormatter(formatter)
handlerConsole.setLevel(logging.INFO)
logger.addHandler(handlerConsole)



timeout=20

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
        req = session.post(pordede.url_login,headers=pordede.headers, data = pordede.login_data, timeout=timeout)
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
        req = session.post(pordede.url_login,headers=pordede.headers, data = pordede.login_data, timeout=timeout)
        logger.debug( "Login : %s"  %(req.status_code))
        # Try accessing a page that requires you to be logged in
        req = session.get(urlExit,headers=pordede.headers,  timeout=timeout)
        return req;
    except Exception, e:
        logger.error(str(e))


def getSerie(nproc, serie):
    if (serie):
        logger.info("Iniciando %s Procceso para %s" %(nproc, serie))
        x.execute("SELECT tmp.id, tmp.serie, tmp.season, tmp.episode, tmp.actualizacion, enl.id FROM temporadas tmp LEFT JOIN enlaces enl ON ( tmp.id = enl.episode ) WHERE tmp.status =0 AND enl.id IS NULL AND tmp.serie = '%s' ORDER BY tmp.actualizacion" %(serie))        
    else:   
        logger.info("Iniciando %s Procceso "%(nproc)) 
        x.execute("SELECT tmp.id, tmp.serie, tmp.season, tmp.episode, tmp.actualizacion, enl.id FROM temporadas tmp LEFT JOIN enlaces enl ON ( tmp.id = enl.episode ) WHERE tmp.status =0 AND enl.id IS NULL ORDER BY tmp.actualizacion DESC")
    res = x.fetchall()
    count = 0
    fecha_actual = datetime.today();
    for row in res:
        fechaActualizacion = row[4];
        
        logger.info("Procesamos %d de %d" %(count, nproc))
        if (count<nproc):
            #if (fechaActualizacion is None) or (fecha_actual > fechaActualizacion + timedelta(minutes=10)):
                idTemporada = row[0]
                nombreSerie = row[1]
                dSeason=row[2]
                dEpisodio=row[3] 
                logger.info("Buscamos de %s el episodio con id %d, %d, %d" %("http://www.pordede.com%s" %(nombreSerie), idTemporada, dSeason, dEpisodio-1))
                req = session.get("http://www.pordede.com/%s" %(nombreSerie),headers=pordede.headers,  timeout=timeout)
                # Comprobamos que la petición nos devuelve un Status Code = 200
                if req.status_code == 200:
                    # Pasamos el contenido HTML de la web a un objeto BeautifulSoup()
                    html = BeautifulSoup(req.text, "html.parser")
                
                    seasons = html.find_all('div',{'class':'episodes'})
                    if (seasons[0].find('div',{'class':'checkSeason','data-num':'0'}) is None):
                        dSeason=dSeason-1
                    logger.debug(len(seasons))
                    season=seasons[dSeason]
                    # Obtenemos todos los divs donde estan las episodios
                    episodios = season.find_all('div',{'data-model':'episode'})
                    logger.debug( "Numero de Episodios %s" %(len(episodios)))
                    # Recorremos todas las entradas para extraer numero y status
                    episodio=episodios[dEpisodio-1]
                    #logger.debug(episodio)
                    enlace = episodio.find('span',{'class' : 'title'})['href']
                    #logger.debug('Enlace %s' %(enlace))
                    
                    getEnlace(enlace, idTemporada)
                    count=count+1
                    try:
                        x.execute("UPDATE temporadas SET actualizacion='%s' WHERE id='%s'" %(time.strftime('%Y-%m-%d %H:%M:%S'),idTemporada))
                        logger.info( "Update de %s - %s" %(nombreSerie, time.strftime('%Y-%m-%d %H:%M:%S')) )
                        conn.commit()
                    except Exception, e:
                        logger.error( str(e))
                        conn.rollback()
                    
                else:
                    # Si ya no existe la página y me da un 400
                    logger.error( " Error %s" %( req.status_code))
        else:
            break
        
        

    
''' INI : texto a compartir '''

def getEnlace(url,id):

    req = session.get("http://www.pordede.com/%s" %(url),headers=pordede.headers,  timeout=timeout)
     # Comprobamos que la petición nos devuelve un Status Code = 200
    statusCode = req.status_code
    
    if statusCode == 200:
        # Pasamos el contenido HTML de la web a un objeto BeautifulSoup()
        html = BeautifulSoup(req.text, "html.parser")   
        #logger.info(html)
        divContainer = html.find('div',{'class': 'linksContainer online tabContent'})
        #logger.info(divContainer)
        
        links = divContainer.find_all('a',{'data-host':'8', 'data-quality':'1'})
        myLinks = filterAndSort(links)
        if (len(myLinks)>0):            
            logger.debug("Aporte Ordenado %s" %(myLinks[0]['href']))
            
            instancia = enlaces()
            instancia.episode=id
            instancia.type=8
            instancia.link = getEnlace2(myLinks[0]['href'])
            add(instancia)

        links = divContainer.find_all('a',{'data-host':'36', 'data-quality':'1'})
        myLinks = filterAndSort(links)
        if (len(myLinks)>0):      
            logger.debug("Aporte ordenado%s" %(myLinks[0]['href']))
    
            instancia = enlaces()
            instancia.episode=id
            instancia.type=36
            instancia.link = getEnlace2(myLinks[0]['href'])
            add(instancia)
        
    else:
        # Si ya no existe la página y me da un 400
        logger.error( " Error %s" %(statusCode))    

def getEnlace2(enlace):
    req = session.get("http://www.pordede.com/%s" %(enlace),headers=pordede.headers,  timeout=timeout)
    # Comprobamos que la petición nos devuelve un Status Code = 200
    statusCode = req.status_code
    
    if statusCode == 200:
        # Pasamos el contenido HTML de la web a un objeto BeautifulSoup()
        html = BeautifulSoup(req.text, "html.parser")   
        alink = html.find("a",{'class':'episodeText'})
        if (alink is not None):
            logger.debug("alink %s" %(alink['href']))
            return getEnlace3(alink['href'])
        
        
    else:
        # Si ya no existe la página y me da un 400
        logger.error( " Error %s" %(statusCode))        


def getEnlace3(enlace):
    req = session.get("http://www.pordede.com%s" %(enlace),headers=pordede.headers,  timeout=timeout, allow_redirects=False)

    logger.debug(req.headers['Location'])     
    return req.headers['Location']


def add(instancia):
    try:
        logger.info(repr(instancia))
        x.execute("""INSERT INTO enlaces(episode,type,link,actualizacion) VALUES (%d,%d,'%s', '%s' )""" %(instancia.episode,instancia.type, instancia.link, time.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except Exception, e:
        logger.error( str(e))
        conn.rollback()
    
def filterAndSort(links):
    myLinks = []
    logger.debug("myLinks : %d" %(len(myLinks)))
    for link in links:
        divsIdiomas = link.findAll('div',{'class': re.compile('^spanish$')})
        if (len(divsIdiomas)>0):
            sIdioma = divsIdiomas[0].getText().strip()
            if (not sIdioma):
                logger.debug("el valor %d es mayor que 0 : %s" %((int(link['data-value']), (link['data-value']>0))))
                if (int(link['data-value'])>0):
                    logger.debug("Add %s ???" %(link['href']))
                    myLinks.append(link)
        
    myLinks.sort(key=lambda l: l['data-value'], reverse=True)
    logger.debug("Numero de registros encontrados %d" %(len(myLinks)))
    return myLinks    


''' FIN Texto a compartir '''



if __name__ == '__main__':
    if (onlyLogin()):
        nproc=20
        #getSerie(nproc);
        getSerie(nproc, sys.argv[1] if len(sys.argv)>= 2 else None)

        
    
   
    



