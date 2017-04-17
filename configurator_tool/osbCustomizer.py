####################################################################
#
#	Author:                         Tomas (Tome) Frastia
#	Web:                            http://www.TomeCode.com
#	Version:                        1.1.0
#	Description:					
#	Copyright (c):					Tomas (Tome) Frastia | TomeCode.com
#
#	Changelog:
#	1.1.0
#		Customize: 	MQConnection
#					Proxy Service and Business Service with transport: MQ, MQConnection, FTP, FILE, SFTP, EMAIL, SB
#		Bug fixes and improvements
#	1.0.0
#		New customization core
#		Customize: 	authentication for: SSLClientAuthenticationType, CustomTokenAuthenticationType for HTTP/Proxy
#					ProxyServer, AlertDestination, ServiceProvider
#					(Static) ServiceAccount
#					RetryCount and RetryInterval in HTTP/Proxy
#		Enable or disable deployment to OSB
#		Bug fixes
#	0.0.2
#		Bug fixes
#	0.0.2
#		Bug fixes
#	0.0.1
#		Customize: Proxy Service and Business Service with transport: JMS and HTTP
####################################################################


import sys, traceback
import os
import os.path
import time

from javax.xml.namespace import QName

from java.io import ByteArrayInputStream
from java.io import ByteArrayOutputStream
from java.io import FileOutputStream
from java.util.jar import JarInputStream
from java.util.jar import JarOutputStream
from java.util.jar import JarEntry

from com.tomecode.utils import Utils

from com.bea.wli.sb.services import ServiceAccountDocument
from com.bea.wli.sb.services import ServiceDefinition
from com.bea.wli.sb.services import StaticServiceAccount
from com.bea.wli.sb.services import ServiceProviderEntry

from com.bea.wli.sb.transports import EndPointConfiguration
from com.bea.wli.sb.transports import URIType
from com.bea.wli.sb.transports import FilePathType

from com.bea.wli.sb.transports.http import AuthenticationConfigurationType
from com.bea.wli.sb.transports.http import SSLClientAuthenticationType
from com.bea.wli.sb.transports.http import CustomTokenAuthenticationType
from com.bea.wli.sb.transports.http import HttpBasicAuthenticationType
from com.bea.wli.sb.transports.http import HttpEndPointConfiguration
from com.bea.wli.sb.transports.http import HttpInboundPropertiesType
from com.bea.wli.sb.transports.http import HttpOutboundPropertiesType
from com.bea.wli.sb.transports.http import HttpRequestMethodEnum

from com.bea.wli.sb.transports.mq import MQInboundProperties
from com.bea.wli.sb.transports.mq import MQEndPointConfiguration
from com.bea.wli.sb.transports.mq import MQMessageTypeEnum

from com.bea.wli.sb.transports.ftp import FtpEndPointConfiguration
from com.bea.wli.sb.transports.ftp import FtpInboundPropertiesType
from com.bea.wli.sb.transports.ftp import FilePollInfo

from com.bea.wli.sb.transports.file import FileEndPointConfiguration
from com.bea.wli.sb.transports.file import FileInBoundProperties

from com.bea.wli.sb.transports.sftp import SftpEndPointConfiguration

from com.bea.wli.sb.transports.email import EmailEndPointConfiguration

from com.bea.wli.sb.transports.sb import SBEndPointConfiguration

from com.bea.wli.sb.transports.jms import JmsEndPointConfiguration
from com.bea.wli.sb.transports.jms import JmsResponsePatternEnum
from com.bea.wli.sb.transports.jms import JmsMessageTypeEnum

from com.bea.wli.sb.uddi import UDDIRegistryEntry

from com.bea.wli.sb.security.accesscontrol.config import PolicyContainerType
from com.bea.wli.sb.security.accesscontrol.config import ProviderPolicyContainerType

from com.bea.wli.sb.services.security.config import XPathSelectorType

from com.bea.wli.sb.resources.proxyserver.config import ProxyServerDocument
from com.bea.wli.sb.resources.proxyserver.config import ProxyServerParams


from com.bea.wli.sb.services.security.config import XPathSelectorType

from com.bea.wli.sb.util import Refs

from com.bea.wli.sb.resources.config import SmtpServerEntry
from com.bea.wli.sb.resources.config import JndiProviderEntry
from com.bea.wli.sb.resources.config import ServiceAccountUserPassword
from com.bea.wli.sb.resources.config import UserPassword
#from com.bea.wli.sb.resources.config import MqConnectionEntry
#from com.bea.wli.sb.resources.config import MqTcpModeType

from com.bea.wli.sb.management.importexport import ALSBImportOperation
from com.bea.wli.sb.management.configuration import SessionManagementMBean
from com.bea.wli.sb.management.configuration import ServiceConfigurationMBean
from com.bea.wli.sb.management.configuration import ALSBConfigurationMBean
from com.bea.wli.sb.management.query import ProxyServiceQuery

from com.bea.wli.domain.config import OperationalSettings

from com.bea.wli.config.customization import Customization

from com.bea.wli.monitoring.alert import AlertDestination

#===================================================================
LOG_CUST_FILE = ' --> '
LOG_CUST_FUNCTION = '   --> '
LOG_NOT_FOUND_FUNCTION = '   ##> Error Not found: '
#===================================================================

NOT_FOUND_CUSTOMIZATION=[]

#===================================================================
# Jar Entry
#===================================================================
class OsbJarEntry:
	name=''
	directory=False
	data=None
	extension=None
	
	def __init__(self,n,d,b):
		self.name=n
		self.directory=d
		self.data=b
		#get extensio name
		self.extension=os.path.splitext(self.name)[1][1:]
		
	def getName(self):
		return self.name
		
	def getData(self):
		return self.data
	
	def setData(self, d):
		self.data=d
		
	def getExtension(self):
		return self.extension.lower()


def findOsbJarEntry(indexName,osbJarEntries):
	for entry in osbJarEntries:
		if entry.getName()==indexName:
			return entry
		
	return None
	

#===================================================================
# Parse sbconfig file
#===================================================================
def parseOsbJar(data):
	osbJarEntries=[]
	jis = None
	jis = JarInputStream(ByteArrayInputStream(data))

	entry = jis.getNextJarEntry()
	while (entry != None):
		if (entry.isDirectory()):
			osbJarEntries.append(OsbJarEntry(entry.toString(), entry.isDirectory(), None))
		else:
			osbJarEntries.append(OsbJarEntry(entry.toString(), entry.isDirectory(), Utils.readJarEntryToBytes(jis,entry)))
		entry = jis.getNextJarEntry()
	
	jis.close()
	return osbJarEntries

def convertToTuple(values):
	list=[]
	if '<type \'str\'>' in str(type(values)):
		list.append(str(values))
	else:
		for val in values:
			list.append(val)
	return list

	
def isDict(val):
	return ('<type \'dict\'>' in str(type(val)))

def reverseDict(val):
	if val==None:
		return []
	list=val.keys()
	list.reverse()
	return list

#===================================================================
# Generating a new sbconfig file
#===================================================================
def generateNewSBConfig(osbJarEntries):
	baos = ByteArrayOutputStream()
	jos = None
	try:
		jos = JarOutputStream(baos)
		for entry in osbJarEntries:
			jarEntry = JarEntry(entry.getName())
			jos.putNextEntry(jarEntry)
			if entry.getData() != None:
				jos.write(entry.getData(), 0, len(entry.getData()))
			jos.closeEntry()
	except Exception, err:
		print traceback.format_exc()
	jos.close()
	return baos.toByteArray()


#===================================================================
# Read binary file (Sbconfig)
#===================================================================
def readBinaryFile(fileName):
    file = open(fileName, 'rb')
    bytes = file.read()
    return bytes

#===================================================================
# Write binary file (Sbconfig)
#===================================================================
def writeToFile(fName, data):
	fos = FileOutputStream(fName)
	fos.write(data)
	fos.flush()
	fos.close()
	
		
def saveNewSbConfigNoFS(sbFileName,data):		
	index=sbFileName.rfind('.')
	newSbFileName= sbFileName[0:index] + '-' + time.strftime('%Y%m%d_%H%M%S')+'.jar'
	print ' New customizated sbconfig is: ' + newSbFileName
	writeToFile(newSbFileName,data)
	return newSbFileName

#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------



#===================================================================
# Connect to the Admin Server
#===================================================================
def connectToOSB():
	print ' '
	print '------------------------------------'
	print ' --- Connecting to OSB server '
	uri = 't3://' + SB_SERVER['ListenAddress'] + ':' + str(SB_SERVER['ListenPort'])
	try:
		connect(SB_SERVER['Username'],SB_SERVER['Password'],uri)
		domainRuntime()
		return True
	except WLSTException:
		print ' --- No server is running at '+ uri+ ' !\n Deploy cancelled!'
	return False


#===================================================================
# Utility function to load a session MBeans
#===================================================================
def createOSBSession():
	sessionName  = "ScriptSession" + str(System.currentTimeMillis())
	sessionMBean = findService(SessionManagementMBean.NAME, SessionManagementMBean.TYPE)
	sessionMBean.createSession(sessionName)
	print '	..OSB Session Created: ' + sessionName
	return sessionMBean, sessionName

def createImportProject(ALSBConfigurationMBean):
	alsbJarInfo = ALSBConfigurationMBean.getImportJarInfo()
	alsbImportPlan = alsbJarInfo.getDefaultImportPlan()
	#alsbImportPlan.setPassphrase(None)
	alsbImportPlan.setPreserveExistingAccessControlPolicies(False)
	alsbImportPlan.setPreserveExistingCredentials(False)
	alsbImportPlan.setPreserveExistingOperationalValues(False)
	alsbImportPlan.setPreserveExistingEnvValues(False)
	alsbImportPlan.setPreserveExistingSecurityAndPolicyConfig(False)
	return ALSBConfigurationMBean.importUploaded(alsbImportPlan)

def uploadSbCofnigToOSB(ALSBConfigurationMBean, sbConfigJar):
	ALSBConfigurationMBean.uploadJarFile(readBinaryFile(sbConfigJar))
	print '		..Uploaded: ' + sbConfigJar
	importResult= createImportProject(ALSBConfigurationMBean)


def deployToOsb(file):
	
	if 'SB_SERVER' in globals():
		print '	Deploying to OSB: '+ file
		
		try:
			if connectToOSB()== True:
				#create new session
				sessionMBean, sessionName = createOSBSession()
				
				ALSBConfigurationMBean = findService(String("ALSBConfiguration.").concat(sessionName), "com.bea.wli.sb.management.configuration.ALSBConfigurationMBean")

				#simple import without customization
				uploadSbCofnigToOSB(ALSBConfigurationMBean,file)

				print '		..Commiting session, please wait, this can take a while...'
				sessionMBean.activateSession(sessionName, "Import from wlst") 
				print '		..Session was successfully committed!'
				print '	'
		except java.lang.Exception, e:
			print '	Import to OSB: Failed, please see logs...' + '\n	', e
			dumpStack()	
			if sessionMBean != None:
				sessionMBean.discardSession(sessionName)
	else:
		print 'Deployment to OSB is disable'


####	###############################################################################################################################################
####	###############################################################################################################################################
####								
####							Customization functions
####
####	###############################################################################################################################################
####	###############################################################################################################################################

def getJmsEndPointConfiguration(serviceDefinition):
	JmsEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	return JmsEndPointConfiguration


def getCommonOutboundProperties(serviceDefinition):
	endPointConfiguration=serviceDefinition.getEndpointConfig()
	outboundProperties= endPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= endPointConfiguration.addNewOutboundProperties()
	return outboundProperties

def getJmsInboundProperties(serviceDefinition):
	jmsEndPointConfiguration=getJmsEndPointConfiguration(serviceDefinition)
	jmsInboundProperties= jmsEndPointConfiguration.getInboundProperties()
	if jmsInboundProperties == None:
		jmsInboundProperties= jmsEndPointConfiguration.addNewInboundProperties()
	return jmsInboundProperties


def changeEndpointUri(endpoints,serviceDefinition):
	endpointConfiguration = serviceDefinition.getEndpointConfig()
	if len(endpointConfiguration.getURIArray()) >= 1:
		#uris=URIType[0]
		endpointConfiguration.setURIArray([])
		
	for uri in endpoints:
		endpointConfiguration.addNewURI().setValue(uri)
	
def getTransactions(serviceDefinition):
	transactions=serviceDefinition.getCoreEntry().getTransactions()
	if transactions==None:
		return serviceDefinition.getCoreEntry().addNewTransactions()
	return transactions

def getHttpInboundProperties(serviceDefinition):
	httpEndPointConfiguration = getHttpEndPointConfiguration(serviceDefinition)
	httpInboundProperties= httpEndPointConfiguration.getInboundProperties()
	if httpInboundProperties == None:
		httpInboundProperties= httpEndPointConfiguration.addNewInboundProperties()
	return httpInboundProperties

def getHttpOutboundProperties(serviceDefinition):
	httpEndPointConfiguration = getHttpEndPointConfiguration(serviceDefinition)
	outboundProperties= httpEndPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= httpEndPointConfiguration.addNewOutboundProperties()
	return outboundProperties

def getHttpEndPointConfiguration(serviceDefinition):
	HttpEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	return HttpEndPointConfiguration

def findKeyPairForServiceProvider(serviceProviderEntry, prupose):
	if serviceProviderEntry.getCredentials()!=None:
		keyPairArray=serviceProviderEntry.getCredentials().getKeyPairArray()
		if keyPairArray!= None:
			for keyPair in keyPairArray:
				if prupose in keyPair.getPurpose():
					return keyPair
	
	return None


def getMqOutboundProperties(serviceDefinition):
	MQEndPointConfiguration = serviceDefinition.getEndpointConfig().getProviderSpecific()
	outboundProperties= MQEndPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= MQEndPointConfiguration.addNewOutboundProperties()
	return outboundProperties


def getFtpOutboundProperties(serviceDefinition):
	FtpEndPointConfiguration = serviceDefinition.getEndpointConfig().getProviderSpecific()
	outboundProperties= FtpEndPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= FtpEndPointConfiguration.addNewOutboundProperties()
	return outboundProperties


def getFtpPrefixSufix(outboundProperties):
	if outboundProperties.getDestinationFileName()==None:
		outboundProperties.addNewDestinationFileName()
	if outboundProperties.getDestinationFileName().getPrefixSuffix()==None:
		outboundProperties.getDestinationFileName().addNewPrefixSuffix()
	return outboundProperties.getDestinationFileName().getPrefixSuffix()

def getFileOutboundProperties(serviceDefinition):
	FileEndPointConfiguration = serviceDefinition.getEndpointConfig().getProviderSpecific()
	outboundProperties= FileEndPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= FileEndPointConfiguration.addNewOutboundProperties()
	return outboundProperties


def getMqInboundProperties(serviceDefinition):
	MQEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	inboundProperties=MQEndPointConfiguration.selectChildren(QName("http://www.bea.com/wli/sb/transports/mq", "inbound-properties"))[0]
	mqInboundProperties = MQInboundProperties.Factory.parse(inboundProperties.toString())
	return inboundProperties, mqInboundProperties

def getFtpInboundProperties(serviceDefinition):
	FtpEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	inboundProperties=FtpEndPointConfiguration.selectChildren(QName("http://www.bea.com/wli/sb/transports/ftp", "inbound-properties"))[0]
	ftpInboundProperties = FtpInboundPropertiesType.Factory.parse(inboundProperties.toString())
	return inboundProperties, ftpInboundProperties


def getFileInboundProperties(serviceDefinition):
	FileEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	inboundProperties=FileEndPointConfiguration.selectChildren(QName("http://www.bea.com/wli/sb/transports/file", "inbound-properties"))[0]
	fileInBoundProperties = FileInBoundProperties.Factory.parse(inboundProperties.toString())
	return inboundProperties, fileInBoundProperties

def getSftpInboundProperties(serviceDefinition):
	SftpEndPointConfiguration = serviceDefinition.getEndpointConfig().getProviderSpecific()
	inboundProperties= SftpEndPointConfiguration.getInboundProperties()
	if inboundProperties == None:
		inboundProperties= SftpEndPointConfiguration.addNewInboundProperties()
	return inboundProperties

def getSftpOutboundProperties(serviceDefinition):
	SftpEndPointConfiguration = serviceDefinition.getEndpointConfig().getProviderSpecific()
	outboundProperties= SftpEndPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= SftpEndPointConfiguration.addNewOutboundProperties()
	return outboundProperties

def getEmailEndPointConfiguration(serviceDefinition):
	EmailEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	return EmailEndPointConfiguration

def getEmailInboundProperties(serviceDefinition):
	EmailEndPointConfiguration = getEmailEndPointConfiguration(serviceDefinition)
	inboundProperties= EmailEndPointConfiguration.getInboundProperties()
	if inboundProperties == None:
		inboundProperties= EmailEndPointConfiguration.addNewInboundProperties()
	return inboundProperties

def getEmailOutboundProperties(serviceDefinition):
	EmailEndPointConfiguration = getEmailEndPointConfiguration(serviceDefinition)
	outboundProperties= EmailEndPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= EmailEndPointConfiguration.addNewOutboundProperties()
	return outboundProperties

def getSBEndPointConfiguration(serviceDefinition):
	SBEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	return SBEndPointConfiguration

def getSbInboundProperties(serviceDefinition):
	SBEndPointConfiguration = getSBEndPointConfiguration(serviceDefinition)
	inboundProperties= SBEndPointConfiguration.getInboundProperties()
	if inboundProperties == None:
		inboundProperties= SBEndPointConfiguration.addNewInboundProperties()
	return inboundProperties

def getSbOutboundProperties(serviceDefinition):
	SBEndPointConfiguration = getSBEndPointConfiguration(serviceDefinition)
	outboundProperties= SBEndPointConfiguration.getOutboundProperties()
	if outboundProperties == None:
		outboundProperties= SBEndPointConfiguration.addNewOutboundProperties()
	return outboundProperties

#===================================================================
# Create a policy expression
#===================================================================
def createPolicyExpression(policyConfig):
	expression = ''
	provider =''
		
	if 'Provider' in reverseDict(policyConfig):
		print LOG_CUST_FILE+ 'Policy: Provider'
		provider=policyConfig['Provider']
	if 'Users' in policyConfig:
		print LOG_CUST_FILE+ 'Policy: Users'
		for user in convertToTuple(policyConfig['Users']):
			expression += '| Usr('+ str(user) + ')'
	
	if 'Groups' in policyConfig:
		print LOG_CUST_FILE+ 'Policy: Groups'
		for group in convertToTuple(policyConfig['Groups']):
			expression += '| Grp('+ str(group) + ')'
	
	if 'Roles' in policyConfig:
		print LOG_CUST_FILE+ 'Policy: Roles'
		for role in convertToTuple(policyConfig['Roles']):
			expression += '| Rol('+ str(role) + ')'


	expression=expression.strip()
	if expression.startswith('|'):
		expression=expression[2:len(expression)]	
	return expression,provider
	
#===================================================================
# Setup policy expression in service
#===================================================================
def setupPolicyExpression(serviceDefinition, policyExpression, provider):
			
	if len(policyExpression.strip())!=0 and len(provider.strip())!=0:
		security = getSecurityFromServiceDefinition(serviceDefinition)

		accessControlPolicyBindingType = security.getAccessControlPolicies()
		if accessControlPolicyBindingType==None:
			accessControlPolicyBindingType = security.addNewAccessControlPolicies()

		transportLevelPolicy = accessControlPolicyBindingType.getTransportLevelPolicy()
		if accessControlPolicyBindingType.getTransportLevelPolicy() == None:
			transportLevelPolicy = accessControlPolicyBindingType.addNewTransportLevelPolicy()


			policyContainerType = ProviderPolicyContainerType.Factory.newInstance()
			policy = policyContainerType.addNewPolicy()
			policy.setProviderId(provider)
			policy.setPolicyExpression(policyExpression)

			transportLevelPolicy.set(policyContainerType)
		else:
			policyContainerType = transportLevelPolicy
			policyContainerType.getPolicyArray()[0].setProviderId(provider)
			policyContainerType.getPolicyArray()[0].setPolicyExpression(policyExpression)

def getSecurityFromServiceDefinition(serviceDefinition):
	security = serviceDefinition.getCoreEntry().getSecurity()
	if security == None:
		security = serviceDefinition.getCoreEntry().addNewSecurity()
	return security

def prepareCustomTokenAuthentication(security):
	customTokenAuthentication=security.getCustomTokenAuthentication()
	if customTokenAuthentication==None:
		#customTokenAuthentication.unsetCustomTokenAuthentication()
		customTokenAuthentication=security.addNewCustomTokenAuthentication()
	return customTokenAuthentication

####	###############################################################################################################################################
####	###############################################################################################################################################
####								
####							Customization Start
####
####	###############################################################################################################################################
####	###############################################################################################################################################


#===================================================================
#	Customize:	Global Operation Settings
#===================================================================

def globaloperationalsettings_operations_monitoring(entry, val):
	entry.setMonitoring(val)

def globaloperationalsettings_operations_slaalerting(entry, val):
	entry.setSlaAlerting(val)

def globaloperationalsettings_operations_pipelinealerting(entry, val):
	entry.setPipelineAlerting(val)

def globaloperationalsettings_operations_resultcaching(entry, val):
	entry.setResultCaching(val)

def globaloperationalsettings_operations_reporting(entry, val):
	entry.setReporting(val)
	
def globaloperationalsettings_operations_logging(entry, val):
	entry.setLogging(val)

#===================================================================
#	Customize:	Service Account: Static
#===================================================================

def serviceaccount_serviceaccount_description(entry, val):
	serviceAccount = entry.getServiceAccount()
	serviceAccount.setDescription(val)

def serviceaccount_serviceaccount_password(entry, val):
	serviceAccountUserPassword = entry.getServiceAccount().getStaticAccount()
	serviceAccountUserPassword.setPassword(val)
	
def serviceaccount_serviceaccount_username(entry, val):
	serviceAccountUserPassword = entry.getServiceAccount().getStaticAccount()
	serviceAccountUserPassword.setUsername(val)
	
#===================================================================
#	Customize:	UDDI
#===================================================================

def uddi_uddiregistry_loadtmodels(entry, val):
	entry.setLoadtModels(val)

def  uddi_uddiregistry_autoimport(entry, val):
	entry.setAutoImport(val)

def  uddi_uddiregistry_password(entry, val):
	entry.setPassword(val)

def uddi_uddiregistry_publishurl(entry, val):
	entry.setPublishUrl(val)

def uddi_uddiregistry_subscriptionurl(entry, val):
	entry.setSubscriptionUrl(val)
	
def uddi_uddiregistry_username(entry, val):
	entry.setUsername(val)

def uddi_uddiregistry_securityurl(entry, val):
	entry.setSecurityUrl(val)
	
def uddi_uddiregistry_url(entry, val):
	entry.setUrl(val)
	
def uddi_uddiregistry_description(entry, val):
	entry.setDescription(val)

#===================================================================
#	Customize:	JNDI
#===================================================================

def jndi_foreignjndiprovider_cachevalues(entry, val):
	entry.setCacheValues(val)

def jndi_foreignjndiprovider_requesttimeout(entry, val):
	entry.setRequestTimeout(val)
	
def jndi_foreignjndiprovider_providerurl(entry, val):
	entry.setProviderUrl(val)

def jndi_foreignjndiprovider_username(entry, val):
	entry.getUserPassword().setUsername(val)

def jndi_foreignjndiprovider_password(entry, val):
	entry.getUserPassword().setPassword(val)

def jndi_foreignjndiprovider_description(entry, val):
	entry.setDescription(val)
	

#===================================================================
#	Customize:	SMTP
#===================================================================

def smtp_smtpserver_description(entry, val):
	entry.setDescription(val)

def smtp_smtpserver_isdefault(entry, val):
	entry.setIsDefault(val)

def smtp_smtpserver_portnumber(entry, val):
	entry.setPortNumber(val)

def smtp_smtpserver_serverurl(entry, val):
	entry.setServerURL(val)
	
def smtp_smtpserver_username(entry, val):
	entry.setUsername(val)
	
def smtp_smtpserver_password(entry, val):
	entry.setPassword(val)

#===================================================================
#	Customize:	Proxy Server
#===================================================================

def proxyserver_proxyserver_description(entry, val):
	entry.getProxyServer().setDescription(val)

def proxyserver_proxyserver_username(entry, val):
	entry.getProxyServer().setUsername(val)

def proxyserver_proxyserver_password(entry, val):
	entry.getProxyServer().setPassword(val)

def proxyserver_proxyserver_servertable(entry, val):
	entry.getProxyServer().getServerTable().setServerArray(None)
	list=[]
	for v in val:
		param  = ProxyServerParams.Factory.newInstance()
		param.setHost(v)
		params=val[v]
		for p in params:
			if p =='Port':
				param.setPort(params[p])
				print LOG_CUST_FUNCTION + 'Port'
			elif p =='SslPort':
				param.setSslPort(params[p])
				print LOG_CUST_FUNCTION + 'SslPort'
			else:
				print 'Property is not supported'
				
		list.append(param)
	entry.getProxyServer().getServerTable().setServerArray(list)


#===================================================================
#	Customize:	Proxy Service: LOCAL
#===================================================================

def local_proxyservice_sametxforresponse(entry, val):
	getTransactions(entry).setSameTxForResponse(val)

def local_proxyservice_description(entry, val):
	entry.getCoreEntry().setDescription(val)

def local_proxyservice_isrequired(entry, val):
	getTransactions(entry).setIsRequired(val)

#===================================================================	
#	Customize:	Proxy Service: Transport Type: HTTP
#===================================================================

def http_proxyservice_description(entry, val):
	entry.getCoreEntry().setDescription(val)

def http_proxyservice_retrycount(entry, val):
	getCommonOutboundProperties(entry).setRetryCount(val)
	
def http_proxyservice_retryinterval(entry, val):
	getCommonOutboundProperties(entry).setRetryInterval(val)
	
def http_proxyservice_usehttps(entry, val):
	getHttpInboundProperties(entry).setUseHttps(val)

def http_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def http_proxyservice_requestencoding(entry, val):
	getHttpEndPointConfiguration(entry).setRequestEncoding(val)

def http_proxyservice_responseencoding(entry, val):
	getHttpEndPointConfiguration(entry).setResponseEncoding(val)

def http_proxyservice_dispatchpolicy(entry, val):
	getHttpEndPointConfiguration(entry).setDispatchPolicy(val)

def http_proxyservice_isrequired(entry, val):
	getTransactions(entry).setIsRequired(val)

def http_proxyservice_sametxforresponse(entry, val):
	getTransactions(entry).setSameTxForResponse(val)
	
def http_proxyservice_policy(entry, val):
	policyExpression, provider=createPolicyExpression(val)
	setupPolicyExpression(entry, policyExpression, provider)

def http_proxyservice_authentication(entry, val):
	return True

def http_proxyservice_authentication_basicauthentication(entry, val):
	getHttpInboundProperties(entry).setClientAuthentication(HttpBasicAuthenticationType.Factory.newInstance())

def http_proxyservice_authentication_customtokenauthentication(entry, val):
	httpInboundProperties= getHttpInboundProperties(entry)					
	customTokenAuthenticationType = CustomTokenAuthenticationType.Factory.newInstance()
	
	for v in val:
		if 'TokenType' in v:
			customTokenAuthenticationType.setTokenType(val[v])
		elif 'HeaderName' in v:
			customTokenAuthenticationType.setHeaderName(val[v])
	httpInboundProperties.setClientAuthentication(customTokenAuthenticationType)

def http_proxyservice_authentication_sslclientauthentication(entry, val):
	getHttpInboundProperties(entry).setClientAuthentication(SSLClientAuthenticationType.Factory.newInstance())

def http_proxyservice_authentication_none(entry, val):
	getHttpInboundProperties(entry).setClientAuthentication(None)

def http_proxyservice_security(entry, val):
	return True
	
def http_proxyservice_security_customauthentication(entry, val):
	return True
	
def http_proxyservice_security_customauthentication_contextproperties(entry, val):
	security=getSecurityFromServiceDefinition(entry)
	customTokenAuthentication=prepareCustomTokenAuthentication(security)
	
	userDefinedContext=customTokenAuthentication.getUserDefinedContext()
	if userDefinedContext!=None:
		customTokenAuthentication.unsetUserDefinedContext()
	userDefinedContext=customTokenAuthentication.addNewUserDefinedContext()

	for v in val:
		property=userDefinedContext.addNewProperty()
		property.setName(v)
		valueSelector=property.addNewValueSelector()
		valueSelector.setVariable('header')
		valueSelector.setXpath(val[v])
		print '		--> set ContextProperty: ' + v

def http_proxyservice_security_customauthentication_authenticationtype(entry, val):
	return True

def http_proxyservice_security_customauthentication_authenticationtype_none(entry, val):
	return 'TODO: not implemented'
	
def http_paroxyservice_security_customauthentication_authenticationtype_customusernameandpassword(entry, val):
	security=getSecurityFromServiceDefinition(entry)
	customTokenAuthentication=prepareCustomTokenAuthentication(security)

	usernamePassword=customTokenAuthentication.getUsernamePassword()
	if usernamePassword==None:
		usernamePassword=customTokenAuthentication.addNewUsernamePassword()

	passwordSelector=usernamePassword.getPasswordSelector()
	if passwordSelector==None:
		passwordSelector=usernamePassword.addNewPasswordSelector()

	usernameSelector=usernamePassword.getUsernameSelector()
	if usernameSelector==None:
		usernameSelector=usernamePassword.addNewUsernameSelector()

	usernameSelector.setVariable('header')
	usernameSelector.setXpath(val['UsernameXpath'])

	passwordSelector.setVariable('header')
	passwordSelector.setXpath(val['PasswordXpath'])

def http_proxyservice_security_customauthentication_authenticationtype_customtoken(entry, val):
	security=getSecurityFromServiceDefinition(entry)
	customTokenAuthentication=prepareCustomTokenAuthentication(security)

	customToken=customTokenAuthentication.getCustomToken()
	if customToken==None:
		customToken=customTokenAuthentication.addNewCustomToken()

	tokenSelector=customToken.getTokenSelector()
	if tokenSelector==None:
		customToken.setTokenSelector(XPathSelectorType.Factory.newInstance())
		tokenSelector=customToken.getTokenSelector()	

	tokenSelector.setVariable('header')
	tokenSelector.setXpath(val['Xpath'])

def http_proxyservice_security_customauthentication_authenticationtype_customusernameandpassword(entry, val):
	security=getSecurityFromServiceDefinition(entry)
	customTokenAuthentication=prepareCustomTokenAuthentication(security)
	#customTokenAuthentication.unsetCustomToken()

	usernamePassword=customTokenAuthentication.getUsernamePassword()
	if usernamePassword==None:
		usernamePassword=customTokenAuthentication.addNewUsernamePassword()

	passwordSelector=usernamePassword.getPasswordSelector()
	if passwordSelector==None:
		passwordSelector=usernamePassword.addNewPasswordSelector()								

	usernameSelector=usernamePassword.getUsernameSelector()
	if usernameSelector==None:
		usernameSelector=usernamePassword.addNewUsernameSelector()

	usernameSelector.setVariable('header')
	usernameSelector.setXpath(val['UsernameXpath'])

	passwordSelector.setVariable('header')
	passwordSelector.setXpath(val['PasswordXpath'])	

	
#===================================================================	
#	Customize:	Proxy Service: Transport Type: JMS
#===================================================================

def jms_proxyservice_retrycount(entry, val):
	getJmsInboundProperties(entry).setRetryCount(val)

def jms_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def jms_proxyservice_dispatchpolicy(entry, val):
	getJmsEndPointConfiguration(entry).setDispatchPolicy(val)

def jms_proxyservice_requestencoding(entry, val):
	getJmsEndPointConfiguration(entry).setRequestEncoding(val)

def jms_proxyservice_jnditimeout(entry, val):
	getJmsEndPointConfiguration(entry).setJndiTimeout(val)

def jms_proxyservice_usessl(entry, val):
	getJmsEndPointConfiguration(entry).setIsSecure(val)

def jms_proxyservice_isxarequired(entry, val):
	getJmsInboundProperties(entry).setXARequired(val)

def jms_proxyservice_errordestination(entry, val):
	getJmsInboundProperties(entry).setErrorDestination(val)

def jms_proxyservice_messageselector(entry, val):
	getJmsInboundProperties(entry).setMessageSelector(val)

def jms_proxyservice_retryinterval(entry, val):
	getJmsInboundProperties(entry).setRetryInterval(val)

def jms_proxyservice_isresponserequired(entry, val):
	getJmsInboundProperties(entry).setResponseRequired(val)

def jms_proxyservice_isrequired(entry, val):
	getTransactions(entry).setIsRequired(val)

def jms_proxyservice_sametxforresponse(entry, val):
	getTransactions(entry).setSameTxForResponse(val)
	
def jms_proxyservice_destinationtypequeue(entry, val):
	lookupCustomizationFunction(sys._getframe().f_code.co_name, val, entry)

def jms_proxyservice_destinationtypequeue_responsepattern(entry, val):
	if val == 'JMS_CORRELATION_ID':
		getJmsInboundProperties(entry).setResponsePattern(JmsResponsePatternEnum.JMS_CORRELATION_ID)
	else:
		getJmsInboundProperties(entry).setResponsePattern(JmsResponsePatternEnum.JMS_MESSAGE_ID)

def jms_proxyservice_destinationtypequeue_responseuri(entry, val):
	getJmsInboundProperties(entry).setResponseURI(val)

def jms_proxyservice_destinationtypequeue_responseencoding(entry, val):
	getJmsEndPointConfiguration(entry).setResponseEncoding(val)

def jms_proxyservice_destinationtypequeue_responsemessagetype(entry, val):
	if val == 'BYTES':
		getJmsInboundProperties(entry).setResponseMessageType(JmsMessageTypeEnum.BYTES)
	else:
		getJmsInboundProperties(entry).setResponseMessageType(JmsMessageTypeEnum.TEXT)

def jms_proxyservice_description(entry, val):
	entry.getCoreEntry().setDescription(val)
	
def jms_proxyservice_policy(entry, val):
	policyExpression, provider=createPolicyExpression(val)
	setupPolicyExpression(entry, policyExpression, provider)

#===================================================================	
#	Customize:	BusinessService: Transport Type: HTTP
#===================================================================

def http_businessservice_description(entry, val):
	entry.getCoreEntry().setDescription(val)	

def http_businessservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def http_businessservice_readtimeout(entry, val):
	getHttpOutboundProperties(entry).setTimeout(val)
	
def http_businessservice_requestencoding(entry, val):
	getHttpEndPointConfiguration(entry).setRequestEncoding(val)

def http_businessservice_responseencoding(entry, val):
	getHttpEndPointConfiguration(entry).setResponseEncoding(val)

def http_businessservice_connectiontimeout(entry, val):
	getHttpOutboundProperties(entry).setConnectionTimeout(val)
	
#===================================================================	
#	Customize:	Alert Destination
#===================================================================

def alertdestination_alertdestination_description(entry, val):
	entry.setDescription(val)

def alertdestination_alertdestination_alertlogging(entry, val):
	entry.setAlertToConsole(val)

def alertdestination_alertdestination_reporting(entry, val):
	entry.setAlertToReportingDataSet(val)

def alertdestination_alertdestination_snmptrap(entry, val):
	entry.setAlertToSNMP(val)
	
#===================================================================	
#	Cutomize:	Service Provider
#===================================================================

def serviceprovider_serviceprovider_description(entry, val):
	entry.setDescription(val)

def serviceprovider_serviceprovider_ssl(entry, val):
	return True

def serviceprovider_serviceprovider_encryption(entry, val):
	return True

def serviceprovider_serviceprovider_digitalsignature(entry, val):
	return True

def serviceprovider_serviceprovider_ssl_alias(entry, val):
	serviceprovider_serviceprovider_by_prupose(entry, val, 'SSL', 'Alias')

def serviceprovider_serviceprovider_ssl_password(entry, val):
	serviceprovider_serviceprovider_by_prupose(entry, val, 'SSL', 'Password')
	
def serviceprovider_serviceprovider_encryption_alias(entry, val):
	serviceprovider_serviceprovider_by_prupose(entry, val, 'Encryption', 'Alias')

def serviceprovider_serviceprovider_encryption_password(entry, val):
	serviceprovider_serviceprovider_by_prupose(entry, val, 'Encryption', 'Password')

def serviceprovider_serviceprovider_digitalsignature_alias(entry, val):
	serviceprovider_serviceprovider_by_prupose(entry, val, 'DigitalSignature', 'Password')

def serviceprovider_serviceprovider_digitalsignature_password(entry, val):
	serviceprovider_serviceprovider_by_prupose(entry, val, 'DigitalSignature', 'Password')

def serviceprovider_serviceprovider_by_prupose(entry, val, prupose, attr):
	keyPair=findKeyPairForServiceProvider(entry,prupose)
	if keyPair !=None:
		if 'Password' in attr:
			keyPair.setPassword(val)
		elif 'Alias' in attr:
			keyPair.setAlias(val)
		else:
			print LOG_CUST_FILE+ 'Warning: '+val+' property is not supported'
	
#===================================================================
#	Customize:	MQConnection
#===================================================================

def mqconnection_mqconnection_xaenabled(entry, val):
	entry.setMqXaEnabled(val)
	
def mqconnection_mqconnection_mqconnectionmaxwait(entry, val):
	entry.setMqConnMaxWait(val)
	
def mqconnection_mqconnection_mqconnectionpoolsize(entry, val):
	entry.setMqConnPoolSize(val)

def mqconnection_mqconnection_mqconnectiontimeout(entry, val):
	entry.setMqConnTimeout(val)
	
def mqconnection_mqconnection_mqversion(entry, val):
	entry.setMqVersion(val)

#===================================================================
#	Customize:	MQConnection 	-	 Connection Type:BindingsMode
#===================================================================

def mqconnection_mqconnection_bindingmode(entry, val):
	return True

def mqconnection_mqconnection_bindingmode_mqqueuemanagername(entry, val):
	entry.getBindingsMode().setQueueManagerName(val)
	
def mqconnection_mqconnection_tcpmode(entry, val):
	return True

#===================================================================
#	Customize:	MQConnection 	-	 Connection Type:TcpMode
#===================================================================

def mqconnection_mqconnection_tcpmode_mqqueuemanagername(entry, val):
	entry.getTcpMode().setQueueManagerName(val)
	
def mqconnection_mqconnection_tcpmode_mqqueuemanagerchannelname(entry, val):
	entry.getTcpMode().setQueueManagerChannelName(val)

def mqconnection_mqconnection_tcpmode_mqportnumber(entry, val):
	entry.getTcpMode().setPort(val)

def mqconnection_mqconnection_tcpmode_mqhostname(entry, val):
	entry.getTcpMode().setHost(val)

def mqconnection_mqconnection_tcpmode_queuemanagerccsid(entry, val):
	entry.getTcpMode().setQueueManagerCcsid(val)

#===================================================================	
#	Customize:	BusinessService: Transport Type: MQ
#===================================================================

def mq_businessservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def mq_businessservice_retrycount(entry, val):
	getCommonOutboundProperties(entry).setRetryCount(val)
	
def mq_businessservice_retryinterval(entry, val):
	getCommonOutboundProperties(entry).setRetryInterval(val)

def mq_businessservice_messagetype(entry, val):
	if 'Bytes' ==val:
		getMqOutboundProperties(entry).setMessageType(MQMessageTypeEnum.BYTES)
	elif 'Text' ==val:
		getMqOutboundProperties(entry).setMessageType(MQMessageTypeEnum.TEXT)
	else:
		print LOG_CUST_FILE+ 'Warning: '+val+' property is not supported for message type'

			
def mq_businessservice_responsetimeout(entry, val):
	getMqOutboundProperties(entry).setResponseTimeout(val)

def mq_businessservice_autogeneratecorrelationvalue(entry, val):
	getMqOutboundProperties(entry).setAutoGenCorrelationValue(val)

def mq_businessservice_mqresponseuri(entry,val):
	getMqOutboundProperties(entry).setResponseURI(val)

def mq_businessservice_pollinginterval(entry, val):
	getMqOutboundProperties(entry).setPollingInterval(val)

def mq_businessservice_processrfh2headers(entry, val):
	getMqOutboundProperties(entry).setProcessRfh2(val)


#===================================================================	
#	Customize:	ProxyService: Transport Type: MQ
#===================================================================

def mq_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def mq_proxyservice_mqresponseuri(entry, val):
	inboundProperties, mqInboundProperties=getMqInboundProperties(entry)
	mqInboundProperties.setResponseURI(val)	
	inboundProperties.set(mqInboundProperties)

def mq_proxyservice_responsemessagetype(entry, val):
	inboundProperties, mqInboundProperties=getMqInboundProperties(entry)
	if 'Bytes' ==val:
		mqInboundProperties.setResponseMessageType(MQMessageTypeEnum.BYTES)
	elif 'Text' ==val:
		mqInboundProperties.setResponseMessageType(MQMessageTypeEnum.TEXT)
	print LOG_CUST_FILE+ 'Warning: '+val+' property is not supported for message type'
	inboundProperties.set(mqInboundProperties)

def mq_proxyservice_retrycount(entry, val):
	inboundProperties, mqInboundProperties=getMqInboundProperties(entry)
	mqInboundProperties.setRetryCount(val)	
	inboundProperties.set(mqInboundProperties)

def mq_proxyservice_pollinginterval(entry, val):
	inboundProperties, mqInboundProperties=getMqInboundProperties(entry)
	mqInboundProperties.setPollingInterval(val)	
	inboundProperties.set(mqInboundProperties)

#===================================================================	
#	Customize:	ProxyService: Transport Type: FTP
#===================================================================

def ftp_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def ftp_proxyservice_readlimit(entry, val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	ftpInboundProperties.setReadLimit(val)
	inboundProperties.set(ftpInboundProperties)

def ftp_proxyservice_directstreaming(entry, val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	ftpInboundProperties.setDirectStreaming(val)
	inboundProperties.set(ftpInboundProperties)

def ftp_proxyservice_timeout(entry,val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	ftpInboundProperties.setTimeout(val)
	inboundProperties.set(ftpInboundProperties)

def getFtpInboundProperties(serviceDefinition):
	FtpEndPointConfiguration=serviceDefinition.getEndpointConfig().getProviderSpecific()
	inboundProperties=FtpEndPointConfiguration.selectChildren(QName("http://www.bea.com/wli/sb/transports/ftp", "inbound-properties"))[0]
	ftpInboundProperties = FtpInboundPropertiesType.Factory.parse(inboundProperties.toString())
	return inboundProperties, ftpInboundProperties

def ftp_proxyservice_recursivescan(entry, val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	ftpInboundProperties.setRecursiveScan(val)
	inboundProperties.set(ftpInboundProperties)

def ftp_proxyservice_downloaddirectory(entry, val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	filePath=FilePathType.Factory.newInstance()
	filePath.setValue(val)
	ftpInboundProperties.setDownloadDirectory(filePath)
	inboundProperties.set(ftpInboundProperties)

def ftp_proxyservice_pollinginterval(entry, val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	pollInfo=FilePollInfo.Factory.newInstance()
	pollInfo.setIntervalMilliseconds(val)
	ftpInboundProperties.setPollInfo(pollInfo)
	inboundProperties.set(ftpInboundProperties)

def ftp_proxyservice_passbyreference(entry, val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	ftpInboundProperties.setDirectStreaming(val)
	inboundProperties.set(ftpInboundProperties)

def ftp_proxyservice_filemask(entry, val):
	inboundProperties, ftpInboundProperties=getFtpInboundProperties(entry)
	ftpInboundProperties.setFileMask(val)
	inboundProperties.set(ftpInboundProperties)

#===================================================================	
#	Customize:	BusinessService: Transport Type: FTP
#===================================================================

def ftp_businessservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def ftp_businessservice_timeout(entry, val):
	getFtpOutboundProperties(entry).setTimeout(val)

def ftp_businessservice_prefix(entry, val):
	getFtpPrefixSufix(getFtpOutboundProperties(entry)).setPrefix(val)

def ftp_businessservice_suffix(entry, val):
	getFtpPrefixSufix(getFtpOutboundProperties(entry)).setSuffix(val)

def ftp_businessservice_retrycount(entry, val):
	getCommonOutboundProperties(entry).setRetryCount(val)

def ftp_businessservice_retryinterval(entry, val):
	getCommonOutboundProperties(entry).setRetryInterval(val)


def file_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def file_proxyservice_sortbyarrival(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	fileInBoundProperties.setSortByArrival(val)
	inboundProperties.set(fileInBoundProperties)

def file_proxyservice_readlimit(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	fileInBoundProperties.setReadLimit(val)
	inboundProperties.set(fileInBoundProperties)

def file_proxyservice_stagedir(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	if fileInBoundProperties.getStageDir()==None:
		fileInBoundProperties.addNewStageDir()
	fileInBoundProperties.getStageDir().setValue(val)
	inboundProperties.set(fileInBoundProperties)

def file_proxyservice_scansubdirectories(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	fileInBoundProperties.setScanSubDirectories(val)
	inboundProperties.set(fileInBoundProperties)

def file_proxyservice_archivedir(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	if fileInBoundProperties.getArchiveDir()==None:
		fileInBoundProperties.addNewArchiveDir()
	fileInBoundProperties.getArchiveDir().setValue(val)
	inboundProperties.set(fileInBoundProperties)

def file_proxyservice_errordir(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	if fileInBoundProperties.getErrorDir()==None:
		fileInBoundProperties.addNewErrorDir()
	fileInBoundProperties.getErrorDir().setValue(val)
	inboundProperties.set(fileInBoundProperties)

def file_proxyservice_pollinginterval(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	fileInBoundProperties.setPollingInterval(val)
	inboundProperties.set(fileInBoundProperties)

def file_proxyservice_filemask(entry, val):
	inboundProperties, fileInBoundProperties=getFileInboundProperties(entry)
	fileInBoundProperties.setFileMask(val)
	inboundProperties.set(fileInBoundProperties)

#===================================================================	
#	Customize:	BusinessService: Transport Type: FTP
#===================================================================

def file_businessservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def file_businessservice_suffix(entry, val):
	getFileOutboundProperties(entry).setSuffix(val)

def file_businessservice_prefix(entry, val):
	getFileOutboundProperties(entry).setPrefix(val)

def file_businessservice_retrycount(entry, val):
	getCommonOutboundProperties(entry).setRetryCount(val)

def file_businessservice_retryinterval(entry, val):
	getCommonOutboundProperties(entry).setRetryInterval(val)

#===================================================================	
#	Customize:	ProxyService: Transport Type: SFTP
#===================================================================

def sftp_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def sftp_proxyservice_retrycount(entry, val):
	getSftpInboundProperties(entry).setRetryCount(val)	
def sftp_proxyservice_sortbyarrival(entry, val):
	getSftpInboundProperties(entry).setSortByArrival(val)

def sftp_proxyservice_readlimit(entry, val):
	getSftpInboundProperties(entry).setReadLimit(val)

def sftp_proxyservice_directstreaming(entry, val):
	getSftpInboundProperties(entry).setDirectStreaming(val)

def sftp_proxyservice_archivedir(entry, val):
	if getSftpInboundProperties(entry).getArchiveDirectory()==None:
		getSftpInboundProperties(entry).addNewArchiveDirectory()
	getSftpInboundProperties(entry).getArchiveDirectory().setValue(val)

def sftp_proxyservice_timeout(entry, val):
	getSftpInboundProperties(entry).setTimeout(val)

def sftp_proxyservice_errordir(entry, val):
	if getSftpInboundProperties(entry).getErrorDirectory()==None:
		getSftpInboundProperties(entry).addNewErrorDirectory()
	getSftpInboundProperties(entry).getErrorDirectory().setValue(val)

def sftp_proxyservice_recursivescan(entry, val):
	getSftpInboundProperties(entry).setRecursiveScan(val)

def sftp_proxyservice_pollinginterval(entry, val):
	if getSftpInboundProperties(entry).getPollInfo()==None:
		getSftpInboundProperties(entry).addNewPollInfo()
	getSftpInboundProperties(entry).getPollInfo().setIntervalMilliseconds(val)

def sftp_proxyservice_filemask(entry , val):
	getSftpInboundProperties(entry).setFileMask(val)

def sftp_proxyservice_downloaddir(entry , val):
	if getSftpInboundProperties(entry).getDownloadDirectory()==None:
		getSftpInboundProperties(entry).addNewDownloadDirectory()
	getSftpInboundProperties(entry).getDownloadDirectory().setValue(val)

#===================================================================	
#	Customize:	BusinessService: Transport Type: SFTP
#===================================================================

def sftp_businessservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def sftp_businessservice_prefix(entry, val):
	getFtpPrefixSufix(getSftpOutboundProperties(entry)).setPrefix(val)

def sftp_businessservice_suffix(entry, val):
	getFtpPrefixSufix(getSftpOutboundProperties(entry)).setSuffix(val)

def sftp_businessservice_retrycount(entry, val):
	getCommonOutboundProperties(entry).setRetryCount(val)

def sftp_businessservice_retryinterval(entry, val):
	getCommonOutboundProperties(entry).setRetryInterval(val)

#===================================================================	
#	Customize:	ProxyService: Transport Type: EMAIL
#===================================================================

def email_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def email_proxyservice_ssluse(entry, val):
	getEmailEndPointConfiguration(entry).setUseSsl(val)

def email_proxyservice_readlimit(entry, val):
	getEmailInboundProperties(entry).setReadLimit(val)

def email_proxyservice_passbyreference(entry, val):
	getEmailInboundProperties(entry).setPassByReference(val)

def email_proxyservice_pollinginterval(entry, val):
	getEmailInboundProperties(entry).setPollingInterval(val)

def email_proxyservice_imapmovefolder(entry, val):
	getEmailInboundProperties(entry).setImapMoveFolder(val)

def email_proxyservice_archivedir(entry, val):
	if getEmailInboundProperties(entry).getArchiveDirectory()==None:
		getEmailInboundProperties(entry).addNewArchiveDirectory()
	getEmailInboundProperties(entry).getArchiveDirectory().setValue(val)

def email_proxyservice_errordir(entry, val):
	if getEmailInboundProperties(entry).getErrorDirectory()==None:
		getEmailInboundProperties(entry).addNewErrorDirectory()
	getEmailInboundProperties(entry).getErrorDirectory().setValue(val)

def email_proxyservice_downloaddir(entry, val):
	if getEmailInboundProperties(entry).getDownloadDirectory()==None:
		getEmailInboundProperties(entry).addNewDownloadDirectory()
	getEmailInboundProperties(entry).getDownloadDirectory().setValue(val)

#===================================================================	
#	Customize:	BusinessService: Transport Type: EMAIL
#===================================================================

def email_businessservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def email_businessservice_ssluse(entry, val):
	getEmailEndPointConfiguration(entry).setUseSsl(val)

def email_businessservice_retrycount(entry, val):
	getCommonOutboundProperties(entry).setRetryCount(val)

def email_businessservice_retryinterval(entry, val):
	getCommonOutboundProperties(entry).setRetryInterval(val)

def email_businessservice_connectiontimeout(entry, val):
	getEmailOutboundProperties(entry).setConnectionTimeout(val)

def email_businessservice_fromaddress(entry, val):
	getEmailOutboundProperties(entry).setFromAddress(val)

def email_businessservice_fromname(entry, val):
	getEmailOutboundProperties(entry).setFromName(val)

def email_businessservice_replytoaddress(entry, val):
	getEmailOutboundProperties(entry).setReplyToAddress(val)

def email_businessservice_replyname(entry, val):
	getEmailOutboundProperties(entry).setReplyToName(val)

def email_businessservice_sockettimeout(entry, val):
	getEmailOutboundProperties(entry).setTimeout(val)


#===================================================================	
#	Customize:	ProxyService: Transport Type: SB
#===================================================================

def sb_proxyservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def sb_proxyservice_ssluse(entry, val):
	getSbInboundProperties(entry).setUseSsl(val)

#===================================================================	
#	Customize:	BusinessService: Transport Type: SB
#===================================================================
def sb_businessservice_endpointuri(entry, val):
	changeEndpointUri(convertToTuple(val),entry)

def sb_businessservice_timeout(entry, val):
	getSbOutboundProperties(entry).setTimeout(val)

def sb_businessservice_retrycount(entry, val):
	getCommonOutboundProperties(entry).setRetryCount(val)

def sb_businessservice_retryapplicationerrors(entry, val):
	getCommonOutboundProperties(entry).setRetryApplicationErrors(val)

def sb_businessservice_retryinterval(entry, val):
	getCommonOutboundProperties(entry).setRetryInterval(val)

####	###############################################################################################################################################
####	###############################################################################################################################################
####								
####							Customization End
####
####	###############################################################################################################################################
####	###############################################################################################################################################


####	###############################################################################################################################################

def loadEntryFactory(jarEntry):
	if jarEntry.getExtension()=='proxyservice' or jarEntry.getExtension()=='businessservice':
		return ServiceDefinition.Factory.parse(ByteArrayInputStream(jarEntry.getData()))
	elif jarEntry.getExtension()=='serviceaccount':
		return ServiceAccountDocument.Factory.parse(ByteArrayInputStream(jarEntry.getData()))
	elif jarEntry.getExtension()=='Operations'.lower():
		return OperationalSettings.Factory.parse(ByteArrayInputStream(jarEntry.getData()))
	elif jarEntry.getExtension()=='UDDIRegistry'.lower():
		return UDDIRegistryEntry.Factory.parse(ByteArrayInputStream(jarEntry.getData()))
	elif jarEntry.getExtension()=='ForeignJNDIProvider'.lower():
		return JndiProviderEntry.Factory.parse(ByteArrayInputStream(jarEntry.getData()))
	elif jarEntry.getExtension()=='SMTPServer'.lower():
		return SmtpServerEntry.Factory.parse(ByteArrayInputStream(jarEntry.getData()))
	elif jarEntry.getExtension()=='ProxyServer'.lower():
		return ProxyServerDocument.Factory.parse(ByteArrayInputStream(jarEntry.getData()))	
	elif jarEntry.getExtension()=='AlertDestination'.lower():
		return AlertDestination.Factory.parse(ByteArrayInputStream(jarEntry.getData()))	
	elif jarEntry.getExtension()=='ServiceProvider'.lower():
		return ServiceProviderEntry.Factory.parse(ByteArrayInputStream(jarEntry.getData()))	
	elif jarEntry.getExtension()=='MQConnection'.lower():
		return MqConnectionEntry.Factory.parse(ByteArrayInputStream(jarEntry.getData()))	
	else:
		return None

####	###############################################################################################################################################

def lookupCustomizationFunction(functionName, parent, entry):
	for setFunction in reverseDict(parent):
		impleSetFunction= (functionName + '_' + setFunction).lower()
		
		#print 'CustFunct: ' + impleSetFunction
		print LOG_CUST_FUNCTION + setFunction
		
		#if the customization function return True than exists another customization function
		if impleSetFunction in globals():			
			if (globals()[impleSetFunction](entry, parent[setFunction])):
				if isDict(parent[setFunction]):
					lookupCustomizationFunction(impleSetFunction, parent[setFunction],entry)
		else:
			print LOG_NOT_FOUND_FUNCTION + impleSetFunction
			NOT_FOUND_CUSTOMIZATION.append(impleSetFunction)


def customizeSbConfigFile(customizationFile,path):
	osbJarEntries=parseOsbJar(readBinaryFile(path))
	
	print 'Customize the following files:'

	#customize services by transport type...	
	for customizationType in reverseDict(customizationFile):
		#print '--> '+ customizationType
		customizationEntries=customizationFile[customizationType]

		for custEntryFile in reverseDict(customizationEntries):
			#find sbconfigEntry		
			jarEntry=findOsbJarEntry(custEntryFile,osbJarEntries)
				
			if jarEntry==None:
				print LOG_CUST_FILE + 'Not found Entry: ' + custEntryFile
			else:
				print LOG_CUST_FILE + jarEntry.getName()
				sbentry=loadEntryFactory(jarEntry)
				if sbentry!=None:
					#
					execFunctionName = customizationType.lower().strip()+'_'+jarEntry.getExtension().lower().strip()
					#execute customization
					lookupCustomizationFunction(execFunctionName,customizationEntries[custEntryFile],sbentry)
					#update jar entry
					jarEntry.setData(sbentry.toString().encode('utf-8'))
				else:
					print LOG_CUST_FUNCTION + 'Customization is not supported!'
	
	if len(NOT_FOUND_CUSTOMIZATION)!=0:
		print ' '
		print '------------------------------------'
		print 'Not found customization functions:'
		for notFoundFunct in NOT_FOUND_CUSTOMIZATION:
			print '	'+ notFoundFunct
		print '------------------------------------'
		print ' '
	#generate new SB Config
	return osbJarEntries
	

def executeCustomization():
	if 'SB_CUSTOMIZATOR' in globals():
		for sbFileName in SB_CUSTOMIZATOR:
			print ' '
			print '------------------------------------'
			print ' Customize Config: '+str(sbFileName)
			sbFile=SB_CUSTOMIZATOR[sbFileName]
			#customize 
			path=str(sbFileName)
			path= os.path.abspath(path)
			if os.path.isfile(path) and os.path.exists(path):
				osbJarEntries= customizeSbConfigFile(sbFile,sbFileName)
				
				#generate new sbconfig file
				data=generateNewSBConfig(osbJarEntries)
				#deploy
				return saveNewSbConfigNoFS(sbFileName,data)
			else:
				print LOG_CUST_FILE+' Error: ' + path + ' SB Config file not found'
	else:
		print LOG_CUST_FILE+' Not found customization config: SB_CUSTOMIZATOR'

try:
	print '################################################################################'
	print ''
	print '		OSB-Config-WLST-Configurator (TomeCode.com)'
	print '	'
	print '	'
	print '	'
	
	if len(sys.argv)!=2:
		print '	Not found OSB Customization file!'
		print '	Execute: ./osbCustomizer.(sh/cmd) osbCustomizer.properties'
		print '	'
		print '	'
		exit()

	f=sys.argv[1]
	
	print ' Load customization file: '  + f
	f = os.path.abspath(f)
	exec open(str(f),'r')

	deployFile=executeCustomization()
	deployToOsb(deployFile)

except Exception, err:
	print ' Failed Execute customization file: '+ f 
	traceback.print_exc()
	#or
	print sys.exc_info()[0]


exit()
