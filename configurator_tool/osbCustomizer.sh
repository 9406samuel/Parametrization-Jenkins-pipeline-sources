#!/bin/bash


WL_HOME="/root/Oracle/Middleware/wlserver_10.3"
OSB_HOME="/root/Oracle/Middleware/Oracle_OSB1"
export JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64"

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
#/root/Oracle/Middleware/oracle_common/common/bin/wlst.sh -i osbCustomizer.py $1
#/root/Oracle/Middleware/Oracle_OSB1/tools/configjar/wlst.sh -i osbCustomizer.py $1
