# ========================================
# Import Python Modules (Standard Library)
# ========================================
import argparse
import logging
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
    def GenerateReport(self):
        # Create test execution-specific folder if it does not exist
        TestFolderFullPath = os.path.join(self.ReportsFolderFullPath, 'test_' + self.TestExecId)
        if not os.path.isdir(TestFolderFullPath): os.mkdir(TestFolderFullPath)
        try:
            # When a query returns no results, self.ResultsDict will not include a 'data' key
            # and no report file will be generated
            assert ('data' in self.ResultsDict), 'The result dictionary does not include the key: data'
            # Start generation of report file (.txt)
            with open(os.path.join(TestFolderFullPath, os.path.splitext(self.QueryFileName)[0] + '.txt') , mode='w') as ReportFileObj:
                ReportFileObj.write(self.DataSep.join(['File', 'URL']) + '\n')
                for NestedList in self.ResultsDict['data']:
                    for DataDict in (FltDataDict for FltDataDict in NestedList if (('file' in FltDataDict) and ('url' in FltDataDict))):
                        ReportFileObj.write(self.DataSep.join([DataDict['file'], DataDict['url']]) + '\n')
            print('--- Report file successfully generated ---')
        except AssertionError as Error:
            print('--- Exception raised - Details: ---')
            print('--- %s ---' % Error)
            print('--- No report file will be generated ---')
    # === Method ===
    def GetLinuxCmd(self, FileToProcName):
        # A list of strings containing the Linux commmand to be executed is build and returned
        # The Linux command timeout is used to avoid slowing down the analysis of large repositories
        LinuxCmdStrList = ['timeout', self.TimeOut + 'm']
        # Add the full path of the capa tool (standalone binary) and and save the output in JSON format (-j option)
        # Unless a different format is specified in the configuration file, only ELF files will be analysed
        LinuxCmdStrList.extend([self.ConfigDict['CapaTool']['FullPath'], '-j', '-f', self.ConfigDict['CapaTool'].get('Format', 'elf')])
        # The full path of the file to be included is passed as input argument.
        LinuxCmdStrList.extend([os.path.join(self.RepoDict['FullPath'], FileToProcName), '>', \
            os.path.join(self.TestReportRepoFolderFullPath, os.path.splitext(FileToProcName)[0] + '.json')])
        return LinuxCmdStrList
    # === Method ===
    def PerformAnalysis(self):
        # Start analysing each repository specified in the configuration file
        print('--- Total number of repositories: {Num} ---'.format(Num=len(self.ConfigDict['Repositories'])))
        self.CreateTestSpecificFolder()
        for RepoElem in self.ConfigDict['Repositories']:
            self.RepoDict = RepoElem['Repository']
            print()
            print('--- Processing repository {Repo} ---'.format(Repo=self.RepoDict['Name']))
            self.CreateRepoSpecificFolder(self.RepoDict['Name'])
            # The following cycle processes all the files within the repository being processed
            for FileNum, FileName in enumerate(os.listdir(self.RepoDict['FullPath'])):
                try:
                    print('--- Processing file number: {Num} ---'.format(Num=FileNum))
                    # The input argument check=True is used to raise an exception when the return
                    # code of the shell command is not zero. Note that the following statement is
                    # compatible with the subprocess module included in Python 3.6.9, but it might
                    # not work as expected in other version of the language. More recent versions
                    # of the subprocess module process additional input arguments, e.g. 'text' and
                    # 'capture_output', which are not supported in Python 3.6.9.
                    AnalysisExecution = subprocess.run(self.GetLinuxCmd(FileName), stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                        universal_newlines=True, check=True)
                    print(AnalysisExecution.returncode) ## REMOVE AFTER DEBUGGING
                    print('--- Checking contents of generated JSON file... ---')
                    # Checkk whether the dictionary extracted from the JSON file generated by Capa
                    # is empty (unsuccessful analysis)

                    print('--- Analysis successfully completed ---')
                    self.SummaryResultsDict['Success'] += 1
                except Exception as Error:
                    print('--- Exception raised - Details: ---')
                    print('--- %s ---' % Error)
                    # The following code attempts to identify the reason why the analysis has failed



    # === Method ===
    def SetDefaultValues(self):
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
        # Init summary results dictionary
        self.SummaryResultsDict = {'Success': 0, 'Other': 0}
        # Timeout parameter (minutes)
        self.TimeOut = 5
    # === Method ===
    def RunConfigFileConsistencyChecks(self):
        # Perform all the consistency checks on the provided configuration file
        assert os.path.splitext(self.ConfigObj.file)[1] in ('.yml', '.yaml'), 'The specified configuration file is not a YAML file'
        assert os.path.isfile(os.path.join(self.ConfigFolderFullPath, self.ConfigObj.file)), \
            'Configuration file does not exist in folder {FolderName}'.format(FolderName=self.ConfigFolderFullPath)
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
                print(self.ConfigDict) ## REMOVE AFTER DEBUGGING
                self.PerformAnalysis()
            except Exception as Error:
                print('--- Exception raised - Details: ---')
                print('--- %s ---' % Error)
        elif self.ConfigObj.postprocessing:
            print('--- Postprocessing execution ---')
            print('--- Results folder: {ResultsFolder} ---'.format(ResultsFolder=self.ConfigObj.postprocessing[0]))
            print('--- Postprocessing type: {PostprocessingType} ---'.format(PostprocessingType=self.ConfigObj.postprocessing[1]))
        elif self.ConfigObj.complete:
            print('--- Analysis and postprocessing execution ---')
            print('--- Configuration file: {ConfigFile} ---'.format(ConfigFile=self.ConfigObj.complete[0]))
            print('--- Postprocessing type: {PostprocessingType} ---'.format(PostprocessingType=self.ConfigObj.complete[1]))
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
    # # Import custom modules
    # try:
    #     import lgtmreslib
    # except Exception as Error:
    #     print('--- Exception raised while importing custom modules - Details: ---')
    #     print('--- %s ---' % Error)
    # Create instance of class TestLauncherCls which implements the program logic
    TestLauncherObj = TestLauncherCls(ProcessProgramInputs())
