# ========================================
# Import Python Modules (Standard Library)
# ========================================
import argparse
import logging
import json
import os
import re
import shutil
import subprocess
import sys
import time
import yaml

# =======
# Classes
# =======
class TestLauncherCls:
    # === Class constructor ===
    def __init__(self, ConfigObj):
        self.ConfigObj = ConfigObj
        self.SetDefaultValues()
        self.TestLauncherLogic()
    # === Method ===
    def CreateRepoSpecificFolder(self, RepoName='RepoName'):
        self.TestReportRepoFolderFullPath = os.path.join(self.TestReportFolderFullPath, RepoName)
        os.mkdir(self.TestReportRepoFolderFullPath)
    # === Method ===
    def CreateTestSpecificFolder(self):
        self.TestReportFolderFullPath = os.path.join(self.ReportsFolderFullPath, 'test_' + self.TestExecId)
        os.mkdir(self.TestReportFolderFullPath)
    # === Method ===
    def ExtractDictFromConfigFile(self):
        # Create file object that yaml.load() will map into a nested Python dictionary
        with open(os.path.join(self.ConfigFolderFullPath, self.ConfigObj.file), mode='r') as ConfigFileObj:
            self.ConfigDict = yaml.load(ConfigFileObj)
    # === Method ===
    def GenerateSummaryReport(self):
        # Create repository-specific test report file (*.txt) out of summary results dictionary
        SummaryReportFullPath = os.path.join(self.TestReportFolderFullPath, 'Summary_Report_' + self.RepoDict['Name'] + '.txt')
        try:
            with open(SummaryReportFullPath, mode='w') as ReportFileObj:
                # Summary dictionary keys are processed according to a customized order
                for DictKey in ['Successful'] + sorted(filter(lambda x: x != 'Successful' and x != 'Other', self.SummaryResultsDict)) + ['Other']:
                    ReportFileObj.write(self.DataSep.join([DictKey, str(self.SummaryResultsDict[DictKey])]) + '\n')
            print('--- Summary report file for repository {Repo} successfully generated ---'.format(Repo=self.RepoDict['Name']))
        except Exception as Error:
            print('--- Exception raised while generating the summary report file for repository {Repo} - Details: ---'.format(\
                Repo=self.RepoDict['Name']))
            print('--- %s ---' % Error)
            print('--- The summary report file might be incomplete or absent ---')
    # === Method ===
    def GetLinuxCmd(self, FileToProcName):
        # A list of strings containing the Linux commmand to be executed is build and returned
        # The Linux command timeout is used to avoid slowing down the analysis of large repositories
        LinuxCmdStrList = ['timeout', str(self.TimeOut) + 'm']
        # Add the full path of the capa tool (standalone binary) and and save the output in JSON format (-j option)
        # Unless a different format is specified in the configuration file, only ELF files will be analysed
        LinuxCmdStrList.extend([self.ConfigDict['CapaTool']['FullPath'], '-j', '-f', self.ConfigDict['CapaTool'].get('Format', 'elf')])
        # The full path of the file to be included is passed as input argument.
        LinuxCmdStrList.extend([os.path.join(self.RepoDict['FullPath'], FileToProcName), '>', \
            os.path.join(self.TestReportRepoFolderFullPath, os.path.splitext(FileToProcName)[0] + '.json')])
        return LinuxCmdStrList
    # === Method ===
    def InitSummaryResultsDict(self):
        # The summary results dict is the data structure that holds the high-level results
        # obtained with a tested repository.
        self.SummaryResultsDict = {'Successful': 0, 'Timed Out': 0, 'Other': 0}
    # === Method ===
    def PerformAnalysis(self):
        # Start analysing each repository specified in the configuration file
        print('--- Total number of repositories: {Num} ---'.format(Num=len(self.ConfigDict['Repositories'])))
        self.CreateTestSpecificFolder()
        for RepoElem in self.ConfigDict['Repositories']:
            self.RepoDict = RepoElem['Repository']
            print()
            print('--- Processing repository {Repo} ---'.format(Repo=self.RepoDict['Name']))
            self.InitSummaryResultsDict()
            self.CreateRepoSpecificFolder(self.RepoDict['Name'])
            # The following cycle processes all the files within the repository being processed
            for FileNum, FileName in enumerate(os.listdir(self.RepoDict['FullPath'])):
                try:
                    print('--- Processing file number: {Num} ---'.format(Num=FileNum + 1))
                    # The following statement is compatible with the subprocess module included
                    # in Python 3.6.9, but it might not work as expected in other version of the
                    # language. More recent versions of the subprocess module process additional
                    # input arguments, e.g., 'text' and 'capture_output', which are not supported
                    # in Python 3.6.9.
                    self.AnalysisExecution = subprocess.run(' '.join(self.GetLinuxCmd(FileName)), shell=True, \
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    print('--- Returned exit code: {Code} ---'.format(Code=self.AnalysisExecution.returncode))
                    if self.AnalysisExecution.returncode == 0:
                        print('--- Analysis successfully completed ---')
                        self.SummaryResultsDict['Successful'] += 1
                    elif self.AnalysisExecution.returncode == 124:
                        print('--- Analysis timed out ---')
                        self.SummaryResultsDict['Timed Out'] += 1
                    elif self.AnalysisExecution.returncode == 255:
                        print('--- Analysis execution ended with an error ---')
                        print('--- Processing standard error... ---')
                        self.ProcessCapaToolLog()
                    else:
                        raise ValueError('--- Unrecognized exit code ---')
                except Exception as Error:
                    print('--- Exception raised - Details: ---')
                    print('--- %s ---' % Error)
                    # When the specific reason for the failed analysis is not identified,
                    # the key 'Other' of the results data structure is used
                    self.SummaryResultsDict['Other'] += 1
            else:
                # This code gets executed when the cycle over the files within a given
                # repository ends without interruptions
                self.GenerateSummaryReport()
        else:
            # This code gets executed when all the repositories have been analysed
             print('--- Analysis ended on: {TimeStamp} ---'.format(TimeStamp=time.ctime()))
    # === Method ===
    def ProcessCapaToolLog(self):
        try:
            # The following regexp is used to process the standard error created
            # by the execution of the Capa tool via shell command. The multiline
            # flag is used to facilitate the extraction of information
            InfoExtractRegExp = re.compile(r'^ERROR:capa:\s(.*)\.$', re.M)
            InfoStrList = InfoExtractRegExp.findall(self.AnalysisExecution.stderr)
            # When no information is extracted, findall returns an empty list and
            # exception is raised (assert)
            assert InfoStrList, '--- No detailed information was extracted from stderr ---'
            # The following code updates the summary results data structure using
            # the first extracted piece of information as dictionary key
            try:
                self.SummaryResultsDict[InfoStrList[0]] += 1
            except KeyError as Error:
                # The dictionary key needs to be initialized
                self.SummaryResultsDict[InfoStrList[0]] = 1
        except AssertionError as Error:
            self.SummaryResultsDict['Other'] += 1
    # === Method ===
    def RunConfigFileConsistencyChecks(self):
        # Perform all the consistency checks on the provided configuration file
        assert os.path.splitext(self.ConfigObj.file)[1] in ('.yml', '.yaml'), 'The specified configuration file is not a YAML file'
        assert os.path.isfile(os.path.join(self.ConfigFolderFullPath, self.ConfigObj.file)), \
            'Configuration file does not exist in folder {FolderName}'.format(FolderName=self.ConfigFolderFullPath)
    # === Method ===
    def SetDefaultValues(self):
        # Data separator (report files)
        self.DataSep = '\t'
        # Test execution identifier for results folder
        TestExecIdRegExp = re.compile(r'(\s|:)')
        self.TestExecId = '_'.join(TestExecIdRegExp.sub('_', time.ctime().replace('  ', ' ')).split('_')[1:-1]).lower()
        # Full path of the folder where this file is stored
        self.ProgramFolderFullPath = os.path.dirname(os.path.realpath(sys.argv[0]))
        # Full path of the folder where the configuration file is stored
        self.ConfigFolderFullPath = os.path.join(self.ProgramFolderFullPath, 'config')
        # Full path of the folder where the report files are stored
        self.ReportsFolderFullPath = os.path.join(self.ProgramFolderFullPath, 'reports')
        # Create generic report folder if it does not exist
        if not os.path.isdir(self.ReportsFolderFullPath): os.mkdir(self.ReportsFolderFullPath)
        # Timeout parameter (minutes)
        self.TimeOut = 5
    # === Method ===
    def TestLauncherLogic(self):
        if self.ConfigObj.remove_results:
            print('--- All results files are about to be deleted ---')
            shutil.rmtree(self.ReportsFolderFullPath, ignore_errors=True)
            os.mkdir(self.ReportsFolderFullPath)
        elif self.ConfigObj.file:
            print('--- Analysis execution ---')
            print('--- Configuration file: {ConfigFile} ---'.format(ConfigFile=self.ConfigObj.file))
            try:
                self.RunConfigFileConsistencyChecks()
                self.ExtractDictFromConfigFile()
                self.PerformAnalysis()
            except Exception as Error:
                print('--- Exception raised - Details: ---')
                print('--- %s ---' % Error)
        elif self.ConfigObj.postprocessing:
            print('--- Postprocessing execution ---')
            print('--- Results folder: {ResultsFolder} ---'.format(ResultsFolder=self.ConfigObj.postprocessing[0]))
            print('--- Postprocessing type: {PostprocessingType} ---'.format(PostprocessingType=self.ConfigObj.postprocessing[1]))
            try:
                ConfigDict = {}
                ConfigDict['ResultsFolderFullPath'] = os.path.join(self.ReportsFolderFullPath, self.ConfigObj.postprocessing[0])
                ConfigDict['PostProcessingType'] = int(self.ConfigObj.postprocessing[1])
                DataPostProcessingObj = capapostprocesslib.DataPostProcessingCls(ConfigDict)
            except Exception as Error:
                print('--- Exception raised - Details: ---')
                print('--- %s ---' % Error)
        elif self.ConfigObj.complete:
            print('--- Analysis and postprocessing execution ---')
            print('--- Configuration file: {ConfigFile} ---'.format(ConfigFile=self.ConfigObj.complete[0]))
            print('--- Postprocessing type: {PostprocessingType} ---'.format(PostprocessingType=self.ConfigObj.complete[1]))
            try:
                # This assignment allows reusing code developed for the analysis-only execution mode
                self.ConfigObj.file = self.ConfigObj.complete[0]
                # Analysis execution
                self.RunConfigFileConsistencyChecks()
                self.ExtractDictFromConfigFile()
                self.PerformAnalysis()
                # Postprocessing execution
                ConfigDict = {}
                ConfigDict['ResultsFolderFullPath'] = self.TestReportFolderFullPath
                ConfigDict['PostProcessingType'] = int(self.ConfigObj.complete[1])
                DataPostProcessingObj = capapostprocesslib.DataPostProcessingCls(ConfigDict)
            except Exception as Error:
                print('--- Exception raised - Details: ---')
                print('--- %s ---' % Error)
        elif self.ConfigObj.merge:
            print('--- Existing test reports merge ---')
            print('--- Results folder: {ResultsFolder} ---'.format(ResultsFolder=self.ConfigObj.merge))
            try:
                ConfigDict = {}
                ConfigDict['ResultsFolderFullPath'] = os.path.join(self.ReportsFolderFullPath, self.ConfigObj.merge)
                ComparePostProcessingReportsObj = capapostprocesslib.ComparePostProcessingReportsCls(ConfigDict)
            except Exception as Error:
                print('--- Exception raised - Details: ---')
                print('--- %s ---' % Error)
        else:
            print('--- The input arguments configuration is inconsistent - Execution interrupted ---')

# =========
# Functions
# =========
def ProcessProgramInputs():
    ParserObj = argparse.ArgumentParser(description='Launches the standalone binary version of the capa tool\
        to analyse multiple files and postprocesses the obtained results. Further information about the \
        postprocessing types is provided in the dedicated module.')
    # Create group of mutually exclusive options
    ModeGroupParserObj = ParserObj.add_mutually_exclusive_group(required=True)
    ModeGroupParserObj.add_argument('-r', '--remove-results', action='store_true', \
        help='Remove results - All results files (*.txt) within the dedicated folder will be removed')
    ModeGroupParserObj.add_argument('-f', '--file', action='store', type=str, metavar='file', \
        help='Analysis execution - All files within the repositories specified in the configuration \
        file will be processed')
    ModeGroupParserObj.add_argument('-p', '--postprocessing', action='store', type=str, nargs=2, \
        metavar=('resultsfolder', 'postprocessingtype'), help='Postprocessing execution - All files \
        within the specified results folder will be processed according to the selected postprocessing type')
    ModeGroupParserObj.add_argument('-c', '--complete', action='store', type=str, nargs=2, \
        metavar=('file', 'postprocessingtype'), help='Complete execution - All files within \
        the repositories specified in the configuration file will be processed. The results will \
        be processed according to the selected postprocessing type')
    ModeGroupParserObj.add_argument('-m', '--merge', action='store', type=str, metavar='resultsfolder', \
        help='Existing test reports merge - Test reports within the specified folder are merged \
        to facilitate comparison of processed repositories. New test report files are created')
    # Return the Namespace object. It contains the parameters passed via command line
    return ParserObj.parse_args()

# ====
# Main
# ====
if __name__ == '__main__':
    print('**************************')
    print('*** Capa Tool Launcher ***')
    print('**************************')
    # Include folder where custom modules are stored in the Python search path
    ModulesFolderName = 'modules'
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), ModulesFolderName))
    # Import custom modules
    try:
        import capapostprocesslib
    except Exception as Error:
        print('--- Exception raised while importing custom modules - Details: ---')
        print('--- %s ---' % Error)
    # Create instance of class TestLauncherCls which implements the program logic
    TestLauncherObj = TestLauncherCls(ProcessProgramInputs())
