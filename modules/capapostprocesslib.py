# ========================================
# Import Python Modules (Standard Library)
# ========================================
import inspect
import json
import os

# =======
# Classes
# =======
class DataPostProcessingCls:
    # === Class constructor ===
    def __init__(self, ConfigDict):
        self.PostProcessingType = ConfigDict['PostProcessingType']
        self.ResultsFolderFullPath = ConfigDict['ResultsFolderFullPath']
        self.RunConsistencyChecks()
        self.SetDefaultValues()
        self.ExecutePostProcessing()
    # === Method ===
    def ExtractInfoFromJSONFile1(self, JSONFileResultsDict):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        # Code developed after analysing the structure of the capa-generated JSON file
        for RuleKey in JSONFileResultsDict['rules']:
            if 'namespace' in JSONFileResultsDict['rules'][RuleKey]['meta']:
                try:
                    self.ResultsDict[JSONFileResultsDict['rules'][RuleKey]['meta']['namespace'].split('/')[0]] += 1
                except KeyError as Error:
                    self.ResultsDict[JSONFileResultsDict['rules'][RuleKey]['meta']['namespace'].split('/')[0]] = 1
    # === Method ===
    def ExtractInfoFromJSONFile2(self, JSONFileResultsDict):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        # Code developed after analysing the structure of the capa-generated JSON file
        for RuleKey in JSONFileResultsDict['rules']:
            if 'namespace' in JSONFileResultsDict['rules'][RuleKey]['meta']:
                try:
                    self.ResultsDict[self.FileName].append(JSONFileResultsDict['rules'][RuleKey]['meta']['namespace'])
                except KeyError as Error:
                    self.ResultsDict[self.FileName] = (JSONFileResultsDict['rules'][RuleKey]['meta']['namespace'])
    # === Method ===
    def GenerateReportType1(self):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        with open(os.path.join(self.ResultsFolderFullPath, self.GetReportFileName()), mode='w') as ReportFileObj:
            for HighLevelCapability in sorted(self.ResultsDict):
                ReportFileObj.write(self.DataSep.join[HighLevelCapability, self.ResultsDict[HighLevelCapability]] + '\n')
    # === Method ===
    def GenerateReportType2(self):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        with open(os.path.join(self.ResultsFolderFullPath, self.GetReportFileName()), mode='w') as ReportFileObj:
            # A set comprehension is used to retrieve all the extracted capabilities.
            ExtractedCapabilityList = sorted({Capability for CapabilityList in self.ResultsDict.values() for Capability in CapabilityList})
            for ProcFileName in sorted(self.ResultsDict):
                ReportFileObj.write(self.DataSep.join([ProcFileName] + \
                    [(1 if (Capability in self.ResultsDict[ProcFileName]) else 0) for Capability in ExtractedCapabilityList]) + '\n')
    # === Method ===
    def GetReportFileName(self):
        return '_'.join(['Postprocessing', 'Type', str(self.PostProcessingType), os.path.basename(self.RepoFolderFullPath) + '.txt'])
    # === Method ===
    def ExecutePostProcessing(self):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        # Processing the results obtained for each tested repository
        for self.RepoFolderFullPath in self.RepoFoldersFullPathList:
            print()
            print('--- Processing results files in folder: {FullPath} ---'.format(FullPath=self.RepoFolderFullPath))
            # Initialize the data structure where the extracted results will be stored
            self.ResultsDict = {}
            # Processing the results for a given repository
            for self.FileName in os.listdir(self.RepoFolderFullPath):
                try:
                    print('--- The file {Name} is about to be processed ---'.format(Name=self.FileName))
                    with open(os.path.join(), mode='r') as JSONFileObj:
                        try:
                            getattr(self, 'ExtractInfoFromJSONFile' + str(self.PostProcessingType))(json.load(JSONFileObj))
                        except Exception as Error:
                            print('--- Exception raised - Details: ---')
                            print('--- %s ---' % Error)
                except json.decoder.JSONDecodeError as Error:
                    print('--- Exception raised while mapping the JSON file into a dictionary - Details: ---')
                    print('--- %s ---' % Error)
                except Exception as Error:
                    print('--- Exception raised - Details: ---')
                    print('--- %s ---' % Error)
            else:
                # The code in this branch gets executed when the for cycle ends without interruptions
                getattr(self, 'GenerateReportType' + str(self.PostProcessingType))()
    # === Method ===
    def RunConsistencyChecks(self):
        # Check if the postprocessing type specified as input argument is an integer
        assert isinstance(self.PostProcessingType, int), 'The specified postprocessing type is not an integer'
        # Check if the postprocessing type specified as input argument is supported
        assert self.PostProcessingType in (1, 2), 'The specified postprocessing type is not supported'
        # Check if the results folder specified as input exists
        assert os.path.isdir(self.ResultsFolderFullPath), 'The specified result folder does not exist'
    # === Method ===
    def SetDefaultValues(self):
        # Data separator (report files)
        self.DataSep = '\t'
        # List containing the full paths of all the repo-specific folders within
        # the results folder passed to the class constructor as input argument
        self.RepoFoldersFullPathList = [Elem for Elem in os.list(self.ResultsFolderFullPath) \
            if os.path.isdir(os.path.join(self.ResultsFolderFullPath, Elem))]
        # Check if the specified results folder includes repo-specific folders
        assert self.RepoFoldersFullPathList, 'The specified result folder does not contain repository-specific folders'
