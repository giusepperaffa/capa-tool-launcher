# ========================================
# Import Python Modules (Standard Library)
# ========================================
import argparse
import logging
import os
import re
import shutil
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
        # self.LogFileSetUp()
        self.TestLauncherLogic()
    # === Method ===
    def ExtractAccessTokenFromFile(self):
        # A regular expression is used to remove all newline characters
        NewLineRegExp = re.compile(r'\n')
        with open(os.path.join(self.ConfigFolderFullPath, self.AccessTokenFileName), mode='r') as AccessTokenFileObj:
            self.AccessToken = NewLineRegExp.sub('', AccessTokenFileObj.read())
    # === Method ===
    def ExtractDictFromConfigFile(self):
        assert os.path.splitext(self.ConfigObj.file)[1] in ('.yml', '.yaml'), \
            '--- Inconsistency detected - The specified configuration file is not a YAML file ---'
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
    # # === Method ===
    # def LogFileSetUp(self):
    #     # The log file basename will be modified by concatenating the test execution id
    #     LogFileBaseName = 'queries_exec_times'
    #     logging.basicConfig(filename=LogFileBaseName + '_' + self.TestExecId + '.log', filemode='w',\
    #         level=logging.INFO, format='%(message)s')
    #     logging.info(self.DataSep.join(['Query', 'Time(s)']))
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
        # # LGTM projects used in self-test mode
        # self.SelfTestConfigDict = {'LGTMProjectURLs': {}}
        # self.SelfTestConfigDict['LGTMProjectURLs']['ApplicationCode'] = 'https://lgtm.com/projects/g/giusepperaffa/si-tool-application-self-test/'
        # self.SelfTestConfigDict['LGTMProjectURLs']['InfrastructureCode'] = 'https://lgtm.com/projects/g/giusepperaffa/si-tool-infrastructure-self-test/'
        # # Timeout parameter (minutes)
        self.TimeOut = 5
        # # Wait times (seconds)
        # self.WaitTime = 20
        # self.WaitTimeAfterException = 120
    # === Method ===
    def SubmitQueries(self, LGTMProjectURL):
        # Create instance of LGTM API interface class
        LGTMAPIConfigDict = {'LGTMProjectURL': LGTMProjectURL, 'AccessToken': self.AccessToken}
        self.LGTMAPIInterfaceObj = lgtmreslib.LGTMAPIInterfaceCls(LGTMAPIConfigDict)
        # The status coe will be returned as an integer
        StatusCode, ProjectId = self.LGTMAPIInterfaceObj.GetProjectId()
        print('--- LGTM Project Id: %s ---' % ProjectId)
        if (StatusCode == 200) and (ProjectId is not None):
            for QueryFileName in os.listdir(os.path.join(self.QueryFolderFullPath, self.ConfigObj.target)):
                try:
                    print()
                    self.QueryFileName = QueryFileName
                    print('--- Submitting query: %s ---' % self.QueryFileName)
                    QueryStartTime = time.time()
                    # Submit query via interface object
                    StatusCode, QueryId = self.LGTMAPIInterfaceObj.SubmitQuery(os.path.join(self.QueryFolderFullPath,\
                        self.ConfigObj.target, self.QueryFileName))
                    print('--- Query Id: %s ---' % QueryId)
                    assert (StatusCode == 202), '--- Query submission unsuccessful ---'
                    # Get the number of pending queries
                    StatusCode, NumOfPendingQueries = self.LGTMAPIInterfaceObj.GetQueryJobStatus()
                    # Wait until there is no pending query or a timeout
                    QueryExecutionStartTime = time.time()
                    while (NumOfPendingQueries != 0) and (time.time() - QueryExecutionStartTime <= self.TimeOut):
                        print('--- Waiting until end of query execution... ---')
                        time.sleep(self.WaitTime)
                        StatusCode, NumOfPendingQueries = self.LGTMAPIInterfaceObj.GetQueryJobStatus()
                    print('--- Number of pending queries: %s ---' % NumOfPendingQueries)
                    assert (StatusCode == 200) and (NumOfPendingQueries == 0), '--- Problem detected during the execution of the query ---'
                    # Get query results summary
                    StatusCode, ResultsSummary = self.LGTMAPIInterfaceObj.GetResultsSummary()
                    print('--- Results summary: %s ---' % ResultsSummary)
                    assert (StatusCode == 200) and (ResultsSummary == 'success'), '--- Problem detected in the results summary ---'
                    # Get query results
                    StatusCode, self.ResultsDict = self.LGTMAPIInterfaceObj.GetQueryJobResults()
                    QueryEndTime = time.time()
                    logging.info(self.DataSep.join([QueryFileName, str(QueryEndTime - QueryStartTime)]))
                    # Generate report containing query results
                    self.GenerateReport()
                except Exception as Error:
                    print('--- Exception raised - Details: ---')
                    print('--- %s ---' % Error)
                    print('--- Waiting before submitting new query... ---')
                    time.sleep(self.WaitTimeAfterException)
        else:
            print('--- HTTP request unsuccessful - No project id retrieved ---')
            print('--- No query will be submitted ---')
    # === Method ===
    def TestLauncherLogic(self):
        if self.ConfigObj.remove_results:
            print('--- All results files are about to be deleted ---')
            shutil.rmtree(self.ReportsFolderFullPath, ignore_errors=True)
            os.mkdir(self.ReportsFolderFullPath)
        elif self.ConfigObj.file:
            print('--- Analysis execution ---')
            print('--- Configuration file: {ConfigFile} ---'.format(ConfigFile=self.ConfigObj.file))
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

def RemoveFilesFromFolder(FolderFullPath, FileExtension):
    for Elem in (FltFile for FltFile in os.listdir(FolderFullPath) if FltFile.endswith(FileExtension)):
        print('--- File {name} is about to be deleted ---'.format(name=Elem))
        os.remove(os.path.join(FolderFullPath, Elem))

def YamlToDictConverter(YamlFolderFullPath, PyFolderFullPath):
    """
    YamlFolderFullPath: Full path of the folder where all the .yml files to be converted are stored
    PyFolderFullPath: Full path of the folder where all the generated .py files are stored
    """
    for FileName in (FltFileName for FltFileName in os.listdir(YamlFolderFullPath) if os.path.splitext(FltFileName)[1] in ('.yml', '.yaml')):
        print('--- Processing file: %s ---' % FileName)
        # Create file object that yaml.load() will map into a nested Python dictionary
        with open(os.path.join(YamlFolderFullPath, FileName), mode='r') as YamlFileObj:
            InfrastructureDict = yaml.load(YamlFileObj)
        # Create .py file containing a comment and an assignment statement with the obtained dictionary
        with open(os.path.join(PyFolderFullPath, os.path.splitext(FileName)[0] + '.py'), mode='w') as PyFileObj:
            CommentString = 'Infrastructure Dictionary'
            PyFileObj.write('\n'.join(['# ' + ('=' * len(CommentString)), '# ' + CommentString, '# ' + ('=' * len(CommentString))]) + '\n')
            PyFileObj.write('InfrastructureDict = ' + str(InfrastructureDict))

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
