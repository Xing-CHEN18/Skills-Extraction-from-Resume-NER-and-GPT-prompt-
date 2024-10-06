# import modules
import os
import pandas as pd
import openai
from openai import InvalidRequestError
import time
import json
from json import JSONDecodeError
from tqdm import tqdm
# add a progress bar to pandas operations
tqdm.pandas(desc='CVs')

# define the path to the output CSV file
output_csv_file_path = './Output/CVs_Info_Extracted.csv'

# define the path to the output Excel file
output_excel_file_path = './Output/CVs_Info_Extracted.xlsx'

# Define the path for the final JSON file where all CV data will be saved
output_json_file = './Output/All_CVs_Info.json'

# define a class to extract CV information
class CVsInfoExtractor:
    # define a constructor that initializes the class with a DataFrame of CVs
    def __init__(self, cvs_df, openai_api_key):
        self.cvs_df = cvs_df
        self.all_cv_data = []  # List to accumulate data for all CVs
        
        # open a file in read mode and read the contents of the file into a variable
        with open('./Engineered_Prompt/Prompt.txt', 'r') as file:
            self.prompt = file.read()
        
        # Set the OpenAI API key
        openai.api_key = openai_api_key


    # Define internal function to call GPT for CV info extraction
    def _call_gpt_for_cv_info_extraction(self, prompt, cv_content, model, temperature = 0):

        # create a dict of parameters for the ChatCompletion API
        completion_params = {
            'model': model,
            'messages': [{"role": "system", "content": prompt},
                        {"role": "user", "content": cv_content}],
            'temperature': temperature}

        # send a request to the ChatCompletion API and store the response
        response = openai.ChatCompletion.create(**completion_params)
        # if the response contains choices and at least one choice, extract the message content
        if 'choices' in response and len(response.choices) > 0:
            cleaned_response = response['choices'][0]['message']['content']
            try:
                # try to convert the message content to a JSON object
                json_response = json.loads(cleaned_response)
            except JSONDecodeError:
                # if the conversion fails, set the JSON response to None
                json_response = None  
        else:
            # if the response does not contain choices or no choice, set the JSON response to None
            json_response = None
            
        # return the JSON response
        return json_response
    
    

    def _normalize_gpt_json_response(self, CV_Filename, json_response):
        # Extract "Technical Skills" and corresponding proficiency levels
        technical_skills = json_response.get("Technical Skills", [])
        proficiency_technical_skills = json_response.get("Proficiency level of Technical Skills", [])
        
        # Pair each technical skill with its corresponding proficiency
        skills_with_proficiency = [{"Skill": skill, "Proficiency": proficiency}
                                for skill, proficiency in zip(technical_skills, proficiency_technical_skills)]

        # Create a dictionary with the CV filename and the paired skills
        cv_info = {
            "CV_Filename": CV_Filename,
            "Skills": skills_with_proficiency
        }

        # Add the current CV's information to the accumulated data list
        self.all_cv_data.append(cv_info)
        
        # Create a DataFrame with the CV Filename and skills with proficiency (just for consistency with your process)
        df_CV_Info = pd.DataFrame({
            "CV_Filename": [CV_Filename],
            "Skills": [skills_with_proficiency]
        })
        
        return df_CV_Info
    
    # Save all accumulated CVs information to a single JSON file
    def _save_all_cv_info_to_json(self):
        with open(output_json_file, 'w') as json_file:
            json.dump(self.all_cv_data, json_file, indent=4)
    

    # Defines internal function to write the DataFrame into a CSV file
    def _write_response_to_file(self, df):

        # Checks if the output CSV file already exists
        if os.path.isfile(output_csv_file_path):
            # If the file exists, append the DataFrame into the CSV file without writing headers
            df.to_csv(output_csv_file_path, mode='a', index=False, header=False)
        else:
            # If the file doesn't exist, write the DataFrame into a new CSV file
            df.to_csv(output_csv_file_path, mode='w', index=False)


    # Define the internal function _gpt_pipeline
    def _gpt_pipeline(self, row, model = 'gpt-3.5-turbo'):

        # Retrieve the CV Filename and Content from the given row
        CV_Filename = row['CV_Filename']
        CV_Content = row['CV_Content']

        # Sleep for 5 seconds to delay the next operation
        time.sleep(5)
        
        try:
            # Print status message indicating GPT is being called for CV info extraction
            print('Calling GPT For CV Info Extraction...')

            # Call the GPT model for CV information extraction
            json_response = self._call_gpt_for_cv_info_extraction(prompt=self.prompt, cv_content=CV_Content, model=model)

            

            # Handle cases where the response is None
            if json_response is None:
                print(f"No valid response for {CV_Filename}. Skipping...")
                return None
            
            # Print status message indicating normalization of GPT response
            print('Normalizing GPT Response...')

            # Normalize the GPT JSON response
            df = self._normalize_gpt_json_response(CV_Filename, json_response)

            # Print status message indicating that the results are being appended to the CSV file
            print('Appending Results To The CSV File...')

            # Write the normalized response to a file
            self._write_response_to_file(df)
            
            # Print a line for clarity in the output
            print('----------------------------------------------')

            # Return the GPT JSON response
            return json_response

        # Catch an exception when the tokens don't fit in the chosen GPT model
        except InvalidRequestError as e:
            # Print the error that occurred
            print('An Error Occurred:', str(e))

            # Print status message indicating that gpt-4 is being called instead
            print("Tokens don't fit gpt-3.5-turbo, calling gpt-4...")

            # Retry the pipeline with the gpt-4 model
            return self._gpt_pipeline(row, model = 'gpt-4')


    # Define the internal function _write_final_results_to_excel
    def _write_final_results_to_excel(self):
        # Load the CSV file into a pandas DataFrame
        df_to_excel = pd.read_csv(output_csv_file_path)

        # Write the DataFrame to an Excel file
        df_to_excel.to_excel(output_excel_file_path)

        # Return the DataFrame
        return df_to_excel


    # Define the main function extract_cv_info
    def extract_cv_info(self):
        # Print a status message indicating the start of the ResumeGPT Pipeline
        print('---- Excecuting ResumeGPT Pipeline ----')
        print('----------------------------------------------')

        # Apply the _gpt_pipeline function to each row in cvs_df DataFrame
        self.cvs_df['CV_Info_Json'] = self.cvs_df.progress_apply(self._gpt_pipeline, axis=1)

        # Save all the accumulated CVs information to a single JSON file
        self._save_all_cv_info_to_json()

        # Print a status message indicating the completion of the extraction
        print('Extraction Completed!')

        # Print a status message indicating that results are being saved to Excel
        print('Saving Results to Excel...')

        # Write the final results to an Excel file
        final_df = self._write_final_results_to_excel()

        # Return the final DataFrame
        return final_df
