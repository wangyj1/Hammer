#!/usr/bin/python2.7
#coding:utf-8
import os
import sys
import logging
import globalVar

# from globalVar import mainlogger

from dummy import BASEDIR
from pprint import pprint

from mlogging_class import StreamHandler_MP

# ----------------------------------------------------------------------------------------------------
# 
# ----------------------------------------------------------------------------------------------------
class PluginLoader(object):
	"""docstring for PluginLoader"""
	def __init__(self, pluginpath=None, services = None,outputpath=''):
		super(PluginLoader, self).__init__()
		if pluginpath == None:
			pluginpath = BASEDIR +'/plugins'
		self.path = pluginpath
		# print 'self.path=',self.path

		self.services = services

		self.plugindict = {}
		self.retinfo = []

		# output file
		outputpath = outputpath.replace('://','_')
		outputpath = outputpath.replace('/','')

		self.target = ''
		if services.has_key('ip'):
			self.target = services['ip']
			self.outputfile = BASEDIR + '/output/' + outputpath + '/' + self.target
		elif services.has_key('url'):
			self.target = services['url']
			tmpurl = self.target.replace('://','_')
			tmpurl = tmpurl.replace(':','_')
			tmpurl = tmpurl.replace('/','')
			self.outputfile = BASEDIR + '/output/' + outputpath + '/' + tmpurl
		elif services.has_key('host'):
			self.target = services['host']
			self.outputfile = BASEDIR + '/output/' + outputpath + '/' + self.target
		else:
			self.outputfile = ''

	def _saveRunningInfo(self,info='',isinit=False,isret=False):
		''' '''
		if self.outputfile == '':
			return False
		# output basic iniformation
		if isinit == True:
			# check if path is exists first
			outputpath = os.path.dirname(self.outputfile)
			if os.path.isdir(outputpath) == False:
				# maybe should use os.makedirs
				try:
					os.makedirs(outputpath)
				except:
					pass

			tmp = info
			if self.services.has_key('ip'):
				tmp += '*'*25 + '     scan info     '+ '*'*25 + os.linesep
				tmp += '# this is an ip type scan'  + os.linesep
				tmp += 'ip:\t' + self.services['ip'] + os.linesep

			elif self.services.has_key('url'):
				tmp += '*'*25 + '     scan info     '+ '*'*25 + os.linesep
				tmp += '# this is a http type scan' + os.linesep
				tmp += 'url:\t' + self.services['url'] + os.linesep
			
			elif self.services.has_key('host'):
				tmp += '*'*25 + '     scan info     '+ '*'*25 + os.linesep
				tmp += '# this is an host type scan'  + os.linesep
				tmp += 'host:\t' + self.services['host'] + os.linesep

			tmp += os.linesep
			tmp += '*'*25 + '   scan services   '+ '*'*25 + os.linesep

			info = tmp
			fp = open(self.outputfile,'w')
			fp.write(info)
			fp.close()
			return True
		# output result
		if isret == True:
			tmp = info

			tmp += os.linesep
			tmp += '*'*25 + '    scan result    '+ '*'*25 + os.linesep
			tmp += 'retinfo:\t' + str(self.retinfo) + os.linesep*2
			tmp += 'services:\t' + str(self.services)
			info = tmp

		if info and info != '':
			fp = open(self.outputfile,'a')
			fp.write(info)
			fp.close()

		return True

	def _initSubProcess(self):
		'''
		初始化子进程在globalVar中的全局变量，包括scan_task_dict
		'''# sub porcess information
		pid = os.getpid()
		# parent process information
		ppid = os.getppid()
		# print 'pid=\t',os.getpid()
		tmpdict = {}
		tmpdict['pid'] = pid
		tmpdict['ppid'] = ppid
		tmpdict['target'] = self.services
		try:
			# only sub process scan will invovied in scan_task_dict
			if self.services.has_key('noSubprocess') and self.services['noSubprocess'] == True:
				pass
			else:
				# globalVar.scan_task_dict_lock.acquire()
				# print 'in pluginLoader porcess pid=\t',os.getpid()
				# print 'id(globalVar)=\t',id(globalVar)
				globalVar.scan_task_dict['subtargets'] = tmpdict
				# pprint(globalVar.scan_task_dict)
				# globalVar.scan_task_dict_lock.release()
		except Exception,e:
			# print 'Exception',e
			globalVar.mainlogger.error('Exception:'+str(e))
		
		# log
		# logger = logging.getLogger(self.target)
		# self.logger.setLevel(logging.DEBUG)
		# formatter = logging.Formatter('[%(name)s] - [%(levelname)s] - %(message)s')  
		# ch = logging.StreamHandler()  
		# ch.setFormatter(formatter)
		# self.logger.addHandler(ch)

		globalVar.mainlogger.info('\tSub Scan Start:\t'+self.target)

	def _getPluginInfo(self,pluginfilepath):
		# print '>>>running plugin:',pluginfilepath
		modulepath = pluginfilepath.replace(BASEDIR+'/plugins/','')
		modulepath = modulepath.replace('.py','')
		modulepath = modulepath.replace('.','')
		modulepath = modulepath.replace('/','.')

		importcmd = 'from ' + modulepath + ' import info'
		# importcmd += '\nprint info'
		# exec_code = compile(importcmd,'','exec')
		# importcmd = 'from temp.explugin import Audit'
		# print 'importcmd=',importcmd
		# from Info_Collect.subdomain import Audit,info
		exec(importcmd)
		# print 'info=',info
		return info

	def loadPlugins(self, path=None):
		self._initSubProcess()
		#print '>>>loading plugins'
		
		if path == None:
			path = self.path
		ret = {}
		for root, dis, files in os.walk(path):  
			if len(files) != 0:
				ret[root] =[]
				for eachfile in files:
					if eachfile != '__init__.py' and '.pyc' not in eachfile and eachfile != 'dummy.py' and eachfile.endswith('.py'):
						ret[root].append(eachfile)
		self.plugindict = ret

		self._saveRunningInfo(isinit=True)
		self._saveRunningInfo('>>>loading plugins'+os.linesep)
		self._saveRunningInfo(os.linesep+str(self.plugindict)+os.linesep*2)

	def runEachPlugin(self, pluginfilepath, services=None):
		try:
			# print '>>>running plugin:',pluginfilepath
			self._saveRunningInfo(os.linesep + '>>>running plugin:' + pluginfilepath + os.linesep)
			globalVar.mainlogger.info('[*][*][-] running plugin:'+pluginfilepath)
			# init globalVar
			plugininfo = self._getPluginInfo(pluginfilepath)
			# pprint(plugininfo)
			pluginname = plugininfo['NAME']
			# globalVar.plugin_now_lock.acquire()
			globalVar.plugin_now = pluginname
			# print id(globalVar)
			# pprint(globalVar.plugin_now)
			# globalVar.plugin_now_lock.release()

			if services == None:
				services = dict(self.services)

			modulepath = pluginfilepath.replace(BASEDIR+'/plugins/','')
			modulepath = modulepath.replace('.py','')
			modulepath = modulepath.replace('.','')
			modulepath = modulepath.replace('/','.')
			# print modulepath
			logger = globalVar.mainlogger
			# 如果有Assign函数，则导入
			try:
				importcmd = 'global services,logger' + os.linesep
				importcmd += 'from ' + modulepath + ' import Assign'
				# globalVar.mainlogger.debug('importcmd='+importcmd)
				# print 'importcmd=',importcmd
				exec(importcmd)
				# print 'load Assign success'
				globalVar.mainlogger.debug('load Assign success')
				self._saveRunningInfo('load Assign success'+os.linesep)
			except Exception,e:
				# print 'Exception: Import Assign Failed\t',e
				globalVar.mainlogger.debug('Exception: Import Assign Failed\t:'+str(e))
			# 导入Audit函数 以及 info变量
			try:
				importcmd = 'global services' + os.linesep
				importcmd += 'from ' + modulepath + ' import info,Audit'
				# print 'importcmd=',importcmd
				exec(importcmd)
				# print 'load info and Audit success'
				globalVar.mainlogger.debug('load info and Audit success')
				self._saveRunningInfo('load info and Audit success'+os.linesep)
			except Exception,e:
				# print 'Exception: Import info and Audit Failed\t',e
				globalVar.mainlogger.debug('Exception: Import info and Audit Failed\t:'+str(e))
			# print 'in running plugin'
			# print 'plugin pid=\t',os.getpid()
			# print 'id(globalVar)=\t',id(globalVar)
			# print 'globalVar.scan_task_dict=\t',globalVar.scan_task_dict
			
			retflag = True
			if locals().has_key('Assign'):
				retflag = False
				retflag = Assign(services)

			# print 'retflag=',retflag
			globalVar.mainlogger.debug('retflag='+str(retflag))

			if retflag and locals().has_key('Audit'):
				# MAudit = copy.copy(Audit)
				#print '\tPlugin function Audit loaded'
				ret, output = ({},'')
				try:
					Audit(services)
					# ret,output = Audit(services)
				except Exception,e:
					# print 'Audit Function Exception:\t',e
					globalVar.mainlogger.error('Audit Function Exception:\t'+str(e))

				# services info
				if self.services != services:
					self.services = services
					#print 'services changed:\t', services
					globalVar.mainlogger.warning('services changed to:\t' + str(services))
					self._saveRunningInfo('services changed to:\t' + str(services) + os.linesep)
				
				# if ret and ret != {}:
				# 	#print 'pluginfilepath=\t',pluginfilepath
				# 	ret['type'] = info['NAME']
				# 	# print 'ret=\t',ret
				# 	self.retinfo.append(ret)

				# # outputinfo
				# if output != '' and output != None:
				# 	# globalVar.mainlogger.info(output)
				# 	self._saveRunningInfo(output+os.linesep)

		# 这里不能一定要用 所有的 Exception, 防止插件出现的各种bug
		except Exception,e:
			# print 'Run Plugin Exception:\t',e
			globalVar.mainlogger.error('Run Plugin Exception:\t:'+str(e))
	def runPlugins(self, services=None):
		if services == None:
			services = self.services
		# find auxiliary path and 
		# self._saveRunningInfo(isinit=True)


		# for test
		# path1 = BASEDIR + '/plugins/Info_Collect'
		# path2 = BASEDIR + '/plugins/System'
		# self.plugindict = {path1:['whatweb.py'],path2:['iisshort.py']}

		for path in self.plugindict:
			if path[-12:]=='Info_Collect':
				auxpath = path
				break

		self._saveRunningInfo(os.linesep+'Step 1. Running Auxiliary Plugins'+os.linesep*2)
		# step1: run auxiliary plugins
		if self.services.has_key('alreadyrun') and self.services['alreadyrun'] == True:
			pass
		else:
			for eachfile in self.plugindict[auxpath]:
				self.runEachPlugin(auxpath+'/'+eachfile)

		self._saveRunningInfo(os.linesep+'Step 2. Running Other Plugins'+os.linesep*2)
		# step2: run other plugins
		for path in self.plugindict:
			if path != auxpath:
				for eachfile in self.plugindict[path]:
					self.runEachPlugin(path+'/'+eachfile)

		self._saveRunningInfo(isret=True)

def main():
	# basedir = '/Users/mody/study/Python/Hammer'
	# sys.path.append(basedir)
	# sys.path.append(basedir+'/lib')
	# sys.path.append(basedir+'/plugins')
	services={'url':'http://www.leesec.com','host':'leesec.com'}
	pl = PluginLoader(None,services)
	pl.path = BASEDIR+'/plugins'
	pl.runEachPlugin(BASEDIR+'/plugins/Info_Collect/subdomain.py',services)
	# pl.runEachPlugin(basedir+'/plugins/Sensitive_Info/backupfile.py',services)
	
	# print pl.loadPlugins()
	# pl.runPlugins()
	print pl.retinfo
# ----------------------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------------------
if __name__=='__main__':
	# import multiprocessing
	# p = multiprocessing.Pool()
	# p.apply_async(main)
	# p.close()
	# p.join()
	main()
