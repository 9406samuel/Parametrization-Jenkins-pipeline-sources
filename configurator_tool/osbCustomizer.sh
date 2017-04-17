#!/bin/bash


WL_HOME="../osb_11G_dependencies/wlserver_10.3"
OSB_HOME="../osb_11G_dependencies/Oracle_OSB1"
export JAVA_HOME="../osb_11G_dependencies/jrockit-jdk1.6.0_37-R28.2.5-4.1.0"

export PATH=${JAVA_HOME}/bin:$PATH
export CLASSPATH=${WL_HOME}/server/lib/weblogic.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/sb-kernel-common.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/sb-kernel-resources.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/sb-kernel-api.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/sb-kernel-impl.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/sb-kernel-wls.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/sb-transports-main.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/sb-transports-http-wls.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/modules/*:$CLASSPATH
export CLASSPATH=${OSB_HOME}/modules/*:$CLASSPATH
export CLASSPATH=${OSB_HOME}/modules/features/*:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/transports/mq_transport.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/transports/mqconnection.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/transports/ftp_transport.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/transports/file_transport.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/transports/sftp_transport.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/transports/emailtransport.jar:$CLASSPATH
export CLASSPATH=${OSB_HOME}/lib/transports/sb_transport.jar:$CLASSPATH
export CLASSPATH=./*.jar:$CLASSPATH

echo $CLASSPATH
echo $PATH
java -version
java weblogic.WLST -i osbCustomizer.py $1
