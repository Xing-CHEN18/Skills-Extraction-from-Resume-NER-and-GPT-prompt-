# Import modules:
# 1. CVsReader from the OCR_Reader module which is used for reading CVs
# 2. CVsInfoExtractor from the ChatGPT_Pipeline module which is used for extracting specific information from the CVs
from OCR_Reader import CVsReader
from ChatGPT_Pipeline import CVsInfoExtractor
import sys

# Fetching command line arguments
cvs_directory_path_arg, openai_api_key_arg = sys.argv[1], sys.argv[2]

# The cvs_directory_path argument, which represents the directory where the CV files are located.
cvs_reader = CVsReader(cvs_directory_path = cvs_directory_path_arg)

# Use the read_cv method of the CVsReader instance to read all CVs in the specified directory.
# The result is a dataframe where each row corresponds to a different CV's file name and content.
cvs_content_df = cvs_reader.read_cv()
"""
# Print a message indicating the start of the CV content cleaning process
print('Cleaning CVs Content...')

# Print the first 100 characters of the content for each CV for debugging purposes
print("Sample content from each CV:")
for index, row in cvs_content_df.iterrows():
    print(f"CV Filename: {row['CV_Filename']}")
    print(f"Content Preview: {row['CV_Content'][:100]}...")
"""
# Create an instance of CVsInfoExtractor.
# It takes as an argument the dataframe returned by the read_cv method of the CVsReader instance and the desired positions in a list.
cvs_info_extractor = CVsInfoExtractor(cvs_df = cvs_content_df, openai_api_key = openai_api_key_arg)

# Use the extract_cv_info method of the CVsInfoExtractor instance to extract the desired information from the CVs.
# This method presumably returns a list of dataframes, each dataframe corresponding to the extracted information from each CV.
extract_cv_info_dfs = cvs_info_extractor.extract_cv_info()