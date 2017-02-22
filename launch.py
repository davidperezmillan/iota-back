#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'DavidPerezMillan'


from bs4 import BeautifulSoup
from clases.enlaces import enlaces
from clases.temporadas import temporadas
from clases.properties import bbdd
from clases.properties import pordede
import enlaces
from datetime import datetime, date, time, timedelta
import logging
from logging.handlers import RotatingFileHandler
import requests
import MySQLdb
import time
import sys
import re

loggerTime = logging.getLogger("timer")
loggerTime.setLevel(logging.INFO)
formatterTime = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] - %(message)s")

handlerLoggerTimeFile = RotatingFileHandler("log/time.log", maxBytes=5e+6, backupCount=5)
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


def getSerie(nombreSerie):

    req = session.get("http://www.pordede.com/%s" %(nombreSerie),headers=pordede.headers,  timeout=5)
    

    # Comprobamos que la petición nos devuelve un Status Code = 200
    statusCode = req.status_code
    
    if statusCode == 200:

        instancia = temporadas()
        instancia.serie=nombreSerie
        
        # Pasamos el contenido HTML de la web a un objeto BeautifulSoup()
        html = BeautifulSoup(req.text, "html.parser")
        
        seasons = html.find_all('div',{'class':'episodes'})
        for season in seasons:
            numeroTemporada = season.find('div',{'class':'checkSeason'})['data-num'] 
            instancia.season=int(numeroTemporada)
            logger.debug( "Temporada %s" %(numeroTemporada))

            # Obtenemos todos los divs donde estan las episodios
            episodios = season.find_all('div',{'data-model':'episode'})
            logger.debug( "Numero de Episodios %s" %(len(episodios)))
            
            # Recorremos todas las entradas para extraer numero y status
            for episodio in episodios:
                #logger.debug( episodio)
                # ALTER TABLE `temporadas` ADD `title` VARCHAR( 255 ) NOT NULL AFTER `episode` ;
                title = episodio.find('span',{'class':'title'}).getText().replace("'", "")
                logger.debug('title %s' %(title))
                if episodio.find('span',{'class':'number'}):
                    numero = episodio.find('span',{'class':'number'}).getText()
                else:
                    numero = 0

                if episodio.find('div',{'class':'action active'}):
                    status = 1
                else:
                    status = 0
                logger.debug( "NUMERO  : %s  --- %r" %(numero, status))
                instancia.episode=int(numero)
                instancia.title = title
                instancia.status=status
                #logger.debug(repr(instancia))
                
                try:
                    x.execute("INSERT INTO temporadas (serie,season,episode, title, status, actualizacion) VALUES ('%s',%d,%d,'%s',%d,'%s');" %(instancia.serie, instancia.season, instancia.episode, instancia.title, instancia.status, time.strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                except Exception, e:
                    if e[0]==1062: # registro duplicado, realizamos un update
                        try:
                            logger.debug("Realiamos un UPDATE")
                            x.execute("UPDATE temporadas SET status=%d, actualizacion='%s', title='%s' WHERE serie='%s'and season=%d and episode=%d" %(instancia.status, time.strftime('%Y-%m-%d %H:%M:%S'), instancia.title, instancia.serie, instancia.season, instancia.episode))
                            conn.commit()
                        except Exception, e:
                            logger.error( str(e))
                            conn.rollback()
                        
                    else:    
                        logger.error( str(e))
                        conn.rollback()
                
                '''
                if (instancia.status==0): ## solo si no la hemos visto, para agilizar el proceso
                    try:
                        x.execute("SELECT * FROM temporadas where serie = '%s' and season=%d and episode = %d" %(instancia.serie, instancia.season, instancia.episode))
                        res = x.fetchall()
                        idEpisode = res[0][0]
                        enlaces.getEnlace(episodio.find('span',{'class' : 'title'})['href'],idEpisode);
                    except Exception, e:
                        logger.error( str(e))
                        conn.rollback()
                '''
                
                logger.debug( "-------" )
    
    
        # modificamos cuando se ha actualizado
        
        try:
            x.execute("UPDATE series SET actualizacion='%s' WHERE serie='%s'" %(time.strftime('%Y-%m-%d %H:%M:%S'),instancia.serie))
            logger.debug( "Final de %s - %s" %(instancia.serie, time.strftime('%Y-%m-%d %H:%M:%S')) )
            conn.commit()
        except Exception, e:
            logger.error( str(e))
            conn.rollback()
           
    else:
        # Si ya no existe la página y me da un 400
        logger.error( " Error %s" %(statusCode))

'''


def getEnlace(url,id):

    req = session.get("http://www.pordede.com/%s" %(url),headers=pordede.headers,  timeout=5)
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
            logger.debug(myLinks[0]['href'])
            
            instancia = enlaces()
            instancia.episode=id
            instancia.type=8
            instancia.link = getEnlace2(myLinks[0]['href'])
            add(instancia)

        links = divContainer.find_all('a',{'data-host':'36', 'data-quality':'1'})
       
        mylinks = filterAndSort(links)
        if (len(myLinks)>0):      
            logger.debug(myLinks[0]['href'])
    
            instancia = enlaces()
            instancia.episode=id
            instancia.type=36
            instancia.link = getEnlace2(myLinks[0]['href'])
            add(instancia)
        
    else:
        # Si ya no existe la página y me da un 400
        logger.error( " Error %s" %(statusCode))    

def getEnlace2(enlace):
    req = session.get("http://www.pordede.com/%s" %(enlace),headers=pordede.headers,  timeout=5)
    # Comprobamos que la petición nos devuelve un Status Code = 200
    statusCode = req.status_code
    
    if statusCode == 200:
        # Pasamos el contenido HTML de la web a un objeto BeautifulSoup()
        html = BeautifulSoup(req.text, "html.parser")   
        alink = html.find("a",{'class':'episodeText'})
        if (alink is not None):
            logger.debug(alink['href'])
            return getEnlace3(alink['href'])
        
        
    else:
        # Si ya no existe la página y me da un 400
        logger.error( " Error %s" %(statusCode))        


def getEnlace3(enlace):
    logger.debug(enlace)
    req = session.get("http://www.pordede.com%s" %(enlace),headers=pordede.headers,  timeout=5, allow_redirects=False)

    logger.debug(req.headers['Location'])     
    return req.headers['Location']


def add(instancia):
    try:
        x.execute("INSERT INTO enlaces(episode,type,link) VALUES (%d,%d,'%s')" %(instancia.episode,instancia.type, instancia.link))
        conn.commit()
    except Exception, e:
        logger.error( str(e))
        conn.rollback()
    
def filterAndSort(links):
    myLinks = []
    for link in links:
        divsIdioma = link.findAll('div',{'class': re.compile('^spanish$')})
        if (len(divsIdioma)>0):
            for idioma in divsIdioma:
                sIdioma = idioma.getText().strip()
                if (not sIdioma):
                    myLinks.append(link)
        
    myLinks.sort(key=lambda link: link['data-value'], reverse=True)
    logger.debug("Numero de registros encontrados %d" %(len(myLinks)))
    return myLinks    

'''


def getSeries():
    
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
                x.execute("INSERT INTO series (serie,ruta) VALUES ('%s','%s');" %(entrada['href'],entrada['href']))
                conn.commit()
            except Exception, e:
                logger.error( str(e))
                conn.rollback()
            

    else:
        # Si ya no existe la página y me da un 400
        logger.error( " Error %s" %(statusCode))

def proccess(nproc, serie):
    if (serie):
        logger.info("Iniciando %s Procceso para %s"%(nproc, serie))
        x.execute("SELECT serie,actualizacion from series WHERE serie = '%s' ORDER BY actualizacion" %(serie))
        
    else:    
        logger.info("Iniciando %s Procceso "%(nproc))
         # Use all the SQL you like
        x.execute("SELECT serie,actualizacion from series ORDER BY actualizacion")
        
    #  logger.debug( all the first cell of all the rows
    fecha_actual = datetime.today();
    count = 0
    for row in x.fetchall():
        logger.info("Procesamos %d de %d" %(count, nproc))
        fechaActualizacion = row[1];
        
        if (count<nproc):
            #if (fechaActualizacion is None) or (fecha_actual > fechaActualizacion + timedelta(minutes=10)):
                logger.info( "Lanzamos proceso %d para la Serie %s a %s" %(count, row[0], fecha_actual))
                getSerie(row[0])
                count=count+1
                #x.execute("UPDATE series SET actualizacion='%s' WHERE serie='%s'" %(fecha_actual,row[0])) */
                #conn.commit()
        else:
            break
    conn.close()






if __name__ == '__main__':
    loggerTime.info("Inicio")
    if (onlyLogin()):
        #getSeries()
        proccess(10, sys.argv[1] if len(sys.argv)>= 2 else None);
    loggerTime.info("Fin")

        
   
    


