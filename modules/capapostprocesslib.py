# ========================================
# Import Python Modules (Standard Library)
# ========================================
import csv
import inspect
import json
import os
import re

# =======
# Classes
# =======
class ComparePostProcessingReportsCls:
    # === Class constructor ===
    def __init__(self, ConfigDict):
        self.ResultsFolderFullPath = ConfigDict['ResultsFolderFullPath']
        self.RunConsistencyChecks()
        self.SetDefaultValues()
        self.CompareReports()
    # === Method ===
    def CompareReports(self):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        for FileNameStart in self.FileNameStartList:
            print()
            if FileNameStart == 'Postprocessing_Type_2':
                # Customized processing needed due to the structure of the reports
                # being processed. Temporary files are created to facilitate the
                # processing and then deleted when they are no longer necessary
                self.CreateTempFiles(FileNameStart)
                self.CreateDataDictionary(self.GenTempFileCommonString)
                self.CreateReport(FileNameStart)
                self.DeleteTempFiles()
            else:
                self.CreateDataDictionary(FileNameStart)
                self.CreateReport(FileNameStart)
    # === Method ===
    def CreateDataDictionary(self, FileNameStart):
        # This method creates a nested dictionary that stores all the information
        # extracted from the files identified via the input parameter string
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        self.DataDict = {}
        for FileName in sorted(Elem for Elem in os.listdir(self.ResultsFolderFullPath) if \
            (os.path.isfile(os.path.join(self.ResultsFolderFullPath, Elem)) and Elem.startswith(FileNameStart))):
            print('--- File being processed: {Name} --- '.format(Name=FileName))
            with open(os.path.join(self.ResultsFolderFullPath, FileName), mode='r') as CSVFileObj:
                # Create CSV reader object
                CSVReaderObj = csv.reader(CSVFileObj, delimiter='\t')
                self.DataDict[FileName] = dict(RowList for RowList in CSVReaderObj)
    # === Method ===
    def CreateReport(self, FileNameStart):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        # The extracted information will be stored in a CSV file
        with open(os.path.join(self.ResultsFolderFullPath, '_'.join([FileNameStart, self.GenReportCommonString + '.csv']) ), \
            mode='w') as ReportFileObj:
            FieldNames = ['Description'] + sorted(self.DataDict)
            CSVWriterObj = csv.DictWriter(ReportFileObj, fieldnames=FieldNames)
            CSVWriterObj.writeheader()
            # The following cycle writes into the generated CSV file line by line
            for Description in self.GetDescriptions(FileNameStart):
                RowDict = {'Description': Description}
                RowDict.update(dict({(FileName, self.DataDict[FileName][Description] if (Description in self.DataDict[FileName]) else 0) \
                    for FileName in sorted(self.DataDict)}))
                CSVWriterObj.writerow(RowDict)
    # === Method ===
    def CreateTempFiles(self, FileNameStart):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        # A regexp is used in this method to extract repository names from file names
        ExtractRepoNameRegExp = re.compile(FileNameStart + '_(\w+)\.txt', re.I)
        # Processing of all the required report files
        for FileName in sorted(Elem for Elem in os.listdir(self.ResultsFolderFullPath) if \
            (os.path.isfile(os.path.join(self.ResultsFolderFullPath, Elem)) and Elem.startswith(FileNameStart))):
            print('--- File being processed: {Name} --- '.format(Name=FileName))
            with open(os.path.join(self.ResultsFolderFullPath, FileName), mode='r') as ReportFileObj:
                CSVReaderObj = csv.DictReader(ReportFileObj, delimiter='\t')
                for LineNum, RowDict in enumerate(CSVReaderObj):
                    # When the first line of the file is processed, a temporary dictionary is initialized
                    if LineNum == 0: TempDict = dict((Key, 0) for Key in RowDict.keys() if Key != 'Sample')
                    # Update the temporary dictionary by incrementing its values
                    for Key in TempDict: TempDict[Key] += int(RowDict[Key])
                else:
                    # When this branch gets executed (i.e., end of previous for cycle) the
                    # temporary dictionary contains keys that identify capabilities (strings)
                    # and values that specify the total number of occurrences in the repository.
                    # This information is saved in temporary files with names that depend on
                    # the processed repository.
                    TempFileName = '_'.join([self.GenTempFileCommonString, ExtractRepoNameRegExp.match(FileName).group(1) + '.txt'])
                    with open(os.path.join(self.ResultsFolderFullPath, TempFileName), mode='w') as TempFileObj:
                        CSVWriterObj = csv.writer(TempFileObj, delimiter='\t')
                        for Key in sorted(TempDict):
                            CSVWriterObj.writerow([Key, TempDict[Key]])
    # === Method ===
    def DeleteTempFiles(self):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        for FileName in (Elem for Elem in os.listdir(self.ResultsFolderFullPath) if \
            (os.path.isfile(os.path.join(self.ResultsFolderFullPath, Elem)) and Elem.startswith(self.GenTempFileCommonString))):
            try:
                os.remove(os.path.join(self.ResultsFolderFullPath, FileName))
            except Exception as Error:
                print('--- Exception raised while deleting the temporary file {TempFile} - Details: ---'.format(TempFile=FileName))
                print('--- %s ---' % Error)
    # === Method ===
    def GetDescriptions(self, FileNameStart):
        # This method extracts all the descriptions present in the first columns
        # of the processed files. In one case, a dedicated sorting order is used
        DescriptionsSet = {Key for FileSpecificDict in self.DataDict.values() for Key in FileSpecificDict}
        if FileNameStart == 'Summary_Report':
            return ['Successful'] + sorted(DescriptionsSet - {'Successful', 'Other'}) + ['Other']
        else:
            return sorted(DescriptionsSet)
    # === Method ===
    def RunConsistencyChecks(self):
        # Check if the results folder specified as input exists
        assert os.path.isdir(self.ResultsFolderFullPath), 'The specified result folder does not exist'
    # === Method ===
    def SetDefaultValues(self):
        # The class finds the files that have to be compared (within the results
        # folder) by using strings that identify the initial part of their names
        self.FileNameStartList = ['Summary_Report', 'Postprocessing_Type_1', 'Postprocessing_Type_2']
        # String added to the names of the report files generated by this class
        self.GenReportCommonString = 'All_Repositories'
        # String used to identify the temporary files created by this class
        self.GenTempFileCommonString = 'Temp_File'

# ========================================
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
                    self.ResultsDict[self.FileName] = [JSONFileResultsDict['rules'][RuleKey]['meta']['namespace']]
    # === Method ===
    def GenerateReportType1(self):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        with open(os.path.join(self.ResultsFolderFullPath, self.GetReportFileName()), mode='w') as ReportFileObj:
            for HighLevelCapability in sorted(self.ResultsDict):
                ReportFileObj.write(self.DataSep.join([HighLevelCapability, str(self.ResultsDict[HighLevelCapability])]) + '\n')
    # === Method ===
    def GenerateReportType2(self):
        print('--- Method {Name} - Start ---'.format(Name=inspect.stack()[0][3]))
        with open(os.path.join(self.ResultsFolderFullPath, self.GetReportFileName()), mode='w') as ReportFileObj:
            # A set comprehension is used to retrieve all the extracted capabilities.
            ExtractedCapabilityList = sorted({Capability for CapabilityList in self.ResultsDict.values() for Capability in CapabilityList})
            ReportFileObj.write(self.DataSep.join(['Sample'] + ExtractedCapabilityList) + '\n')
            for ProcFileName in sorted(self.ResultsDict):
                ReportFileObj.write(self.DataSep.join([ProcFileName] + \
                    [str(1 if (Capability in self.ResultsDict[ProcFileName]) else 0) for Capability in ExtractedCapabilityList]) + '\n')
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
                    with open(os.path.join(self.RepoFolderFullPath, self.FileName), mode='r') as JSONFileObj:
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
        self.RepoFoldersFullPathList = sorted([os.path.join(self.ResultsFolderFullPath, Elem) for Elem in \
            os.listdir(self.ResultsFolderFullPath) if os.path.isdir(os.path.join(self.ResultsFolderFullPath, Elem))])
        # Check if the specified results folder includes repo-specific folders
        assert self.RepoFoldersFullPathList, 'The specified result folder does not contain repository-specific folders'
