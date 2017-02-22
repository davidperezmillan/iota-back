<h3>class/properties.py</h3>
Para que funcione correctamente hay que añadir manualmente este archivo <b>class/properties.py</b> y rellenarlo:
<pre> 
  class bbdd:

      host=""
      user=""
      passwd=""
      db=""

  class pordede:

      user = ""
      password = ""

      url_login = "http://www.pordede.com/site/login"
      login_data = {'LoginForm[username]': user,'LoginForm[password]': password,}
      urlBase = "http://pordede.com/index.php"
      headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36', "Referer":"http://www.pordede.com"}
</pre>    
    
