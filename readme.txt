Autor: Samuel Antonio Cabezas Tibaquicha
Fecha: Enero de 2017


INTEGRACION CONTINUA Y PARAMETRIZACION 

DESCRIPCIÓN GENERAL:
Teniendo en cuenta algunas herramientas que se emplean en la empresa mas el requerimiento de la PoC, el escenario a simular es el siguiente:

Se desea hacer una modificación/actualización de algunos parametros(end points, ports...) de un proyecto de bus basado en el OSB 11g y su posterior despliegue sobre una instancia de bus. Para lograr y complementar este objetivo, existen unos pasos previos donde se emplean los archivos fuentes del proyecto, maven, jenkins y una herramienta para hacer la modificación/actualización mencionada.

En general, lo que se va a hacer es usar los archivos fuente del proyecto de bus, maven y el plugin maven-antrun para generar un archivo .jar del proyecto, despues emplear la herramienta OSB-COnfig-WSLT Configurator que usa el .jar, le modifica los parametros del proyecto acorde a lo que se especifique en un archivo de propiedades, genera un nuevo .jar con los cambios y finalmente lo despliega en una instancia del OSB 11g. El rol de jenkins es ejecutar un trabajo que integre todo lo anterior en un solo proceso.

A continuacion se describe cada una de las carpetas existentes:
	* Calculator application: contiene el archivo .war de la aplicacion a consumirse desde el proyecto de bus.
	* CalculatorConsumption OSB project: contiene los archivos fuente del proyecto de bus "CalculatorConsumption".
	* generated jar: el .jar generado se almacenará en esta carpeta.
	* OSB-Config-WLST-Configurator tool: herramienta para modificar los parametros de un proyecto de bus.

Comando para ejecutar la instalacion del bus 11g dentro del contenedor: 
su - weblogic -c /root/Oracle/Middleware/install_osb.sh
#############################################################################
En construcción:

Se invoca a traves de maven y el plugin maven-antrun, la herramienta "configjar" introducida en la PS6 del OSB 11g, la cual elimina la dependencia con el OEPE para generar el archivo .jar de cualquier proyecto de bus...


