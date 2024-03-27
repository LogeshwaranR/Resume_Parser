import streamlit as st
import PyPDF2
from openai import OpenAI
import json
import pandas as pd
from pandas import json_normalize
from io import BytesIO
import datetime
import os

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page].extract_text()  # Use indexing instead of calling
    return text

def dataframe_to_excel(df):
    excel_data = BytesIO()
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    excel_data.seek(0)
    return excel_data

def main():
    st.title("Resume Parser")
    st.write("Upload multiple PDF files and extract data from each file")

    uploaded_files = st.file_uploader("Upload PDF files", accept_multiple_files=True)

    check = []
    if uploaded_files:
        text_list = []
        for file in uploaded_files:
            text = extract_text_from_pdf(file)
            text_list.append(text)
            if len(text) > 0:
                check.append([file.name,True])
            else:
                check.append([file.name,False])
    for i in range(len(check)):
        if check[i][1]:
            st.write(f"<span style='color:green'>{check[i][0]} Extracted Successfully", "\n", unsafe_allow_html=True)
        else:
            st.write(f"<span style='color:red'>{check[i][0]} Failed to Extract</span>", "\n", unsafe_allow_html=True)

    fields = st.text_input("Fields Required", value="Name, Age, Email, Education")
    but_status = st.button("Process")
    data = pd.DataFrame()
    if but_status and uploaded_files:
        API_KEY = os.getenv('API_KEY')
        with st.spinner('Processing...'):
            for text in text_list:
                client = OpenAI(api_key = API_KEY)
                today = datetime.date.today()
                prompt = "I am a HR professional in a multinational company. I need to process resumes of job applicants for a job opening in my company."+ text +"I need to extract the following information from the resume:" + fields + ". If date of birth and age not given, just put 'not mentioned'. For age take the date of birth and today's date: "+ str(today) +". I need only the previously mentioned fields in JSON format. Dont include any other fields other than the previously mentioned."
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": '{"format": "json"}'},
                        {"role": "user", "content": prompt}
                    ]
                )
                obj = completion.choices[0].message.content
                json_in = str(obj)
                lis = json.loads(json_in)
                nobj = lis
                if len(lis) == 1:
                    for i in lis:
                        nobj = lis[i]
                json_in = json_in.replace("'", '"')
                df = json_normalize(nobj)
                data = data.append(df)
        excel_data = dataframe_to_excel(data)
        st.download_button(label='Download Excel', data=excel_data, file_name='data.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == "__main__":
    main()
