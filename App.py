import base64
import datetime
import io
import random
import time
import webbrowser
import spacy
import pafy
import pandas as pd
import plotly.express as px
import pymysql
import json

import sys
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

import smtplib
from email.mime.text import MIMEText

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords  # Importing stopwords from NLTK
nlp = spacy.load("en_core_web_sm")
import streamlit as st
from PIL import Image
from pdfminer3.converter import TextConverter
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfpage import PDFPage
from pyresparser import ResumeParser 
from streamlit_tags import st_tags

from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos

import os
import mimetypes
from docx import Document

def read_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def read_json(file):
    # Assuming the JSON file has a 'text' key containing the resume text
    with open(file, 'r') as json_file:
        data = json.load(json_file)
        text = data.get('text', '')
    return text

def get_resume_text(file):
    mime, encoding = mimetypes.guess_type(file.name)
    if mime and 'pdf' in mime:
        return pdf_reader(file.name)
    elif mime and 'docx' in mime:
        return read_docx(file)
    elif mime and 'json' in mime:
        return read_json(file.name)
    else:
        st.error("Unsupported file format. Please upload a PDF, DOCX, or JSON file.")
        return ""
    
def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title

def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

connection = pymysql.connect(host='127.0.0.1',user='root',password='',db='user_data')
cursor = connection.cursor()

def insert_data(name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp,str(no_of_pages), reco_field, cand_level, skills,recommended_skills,courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

st.set_page_config(
   page_title="Smart Resume Analyzer",
   page_icon='./Logo/logo.png',
)
def run():
    st.title("AI-Driven eRecruitment Automation")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    st.sidebar.markdown('Built at Code Red')
   
    img = Image.open('./Logo/logo.png')
    img = img.resize((250,250))
    st.image(img)
    # st.subheader('**Have any queries ask our assistant**')
    # if st.button("Click Here"):
    #     st.markdown(f"[Click here to visit](https://chatbotbmsit.streamlit.app/)")


    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)



    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(3000) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Shortlisted VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)

    if choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf", "docx", "json"])
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)
                st.header("**Resume Analysis**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >=3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)

                # st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                text='See our skills recommendation',
                    value=resume_data['skills'],key = '1')

                ##  recommendation
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''

                # Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break
                
                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break
                
                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break
                
                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break
                
                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                #
                ## Insert into table
                
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Algorithms' in resume_data['skills']:
                    resume_score = resume_score+10
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have knowledge of Advanced Data Structures</h4>''',unsafe_allow_html=True)
                else:
                    pass
                    # st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Projects' in resume_data['skills']:
                    resume_score = resume_score+10
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have knowledge of Projects Making </h4>''',unsafe_allow_html=True)
                else:
                    pass
                    # st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Internship' or 'Experience' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internship✍ </h4>''',unsafe_allow_html=True)
                else:
                    pass
                    # st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Internship✍.</h4>''',unsafe_allow_html=True)


                if 'Java' in resume_data['skills']:
                    resume_score = resume_score + 10
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have knowledge of Programming Language</h4>''',unsafe_allow_html=True)
                else:
                    pass
                    # st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Certificates.</h4>''',unsafe_allow_html=True)

                if 'SQL' in resume_data['skills']:
                    resume_score = resume_score + 15
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have knowledge of SQL </h4>''',unsafe_allow_html=True)
                else:
                    pass
                    # st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'Machine Learning' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have good Machine Learning solving skills </h4>''',unsafe_allow_html=True)
                else:
                    pass
                    # st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)
                if "AWS" in resume_data['skills']:
                    resume_score = resume_score + 15
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have knowledge of Cloud </h4>''',unsafe_allow_html=True)
                else:
                    pass
                if 'Python' in resume_data['skills']:
                    resume_score = resume_score + 10
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have knowledge of Python </h4>''',unsafe_allow_html=True)
                else:
                    pass
                if 'Projects' in resume_data.get('skills', []):
                    resume_score += 10  # Projects add 10 points
                if 'Figma' in resume_data.get('skills', []):
                    resume_score += 15  # Figma adds 15 points
                if 'Adobe XD' in resume_data.get('skills', []):
                    resume_score += 10  # Adobe XD adds 10 points
                if 'Wireframing' in resume_text or 'Prototyping' in resume_text:
                    resume_score += 15  # Wireframing/Prototyping adds 15 points
                if 'User Research' in resume_text:
                    resume_score += 20  # User Research adds 20 points
                if 'Usability Testing' in resume_text:
                    resume_score += 15  # Usability Testing adds 15 points
                if 'Design Systems' in resume_data.get('skills', []):
                    resume_score += 10  # Design Systems adds 10 points
                if 'UI Design' in resume_text or 'UX Design' in resume_text:
                    resume_score += 15  # UI/UX Design adds 15 points
                if 'Responsive Design' in resume_text:
                    resume_score += 10  # Responsive Design adds 10 points
                if 'Typography' in resume_text:
                    resume_score += 10  # Typography adds 10 points
                    # Define required skills for different job roles

                # Additional Skills and Scores
                if 'Natural Language Processing' in resume_data['skills']:
                    resume_score += 15
                if 'Big Data Technologies' in resume_data['skills']:
                    resume_score += 20
                if 'Data Warehousing' in resume_data['skills']:
                    resume_score += 15
                if 'Cloud Computing' in resume_data['skills']:
                    resume_score += 20
                if 'Data Pipelines' in resume_data['skills']:
                    resume_score += 15
                if 'Statistical Analysis' in resume_data['skills']:
                    resume_score += 10
                if 'Data Governance' in resume_data['skills']:
                    resume_score += 10

                # Web Development
                if 'RESTful APIs' in resume_data['skills']:
                    resume_score += 15
                if 'GraphQL' in resume_data['skills']:
                    resume_score += 15
                if 'Web Security' in resume_data['skills']:
                    resume_score += 20
                if 'DevOps' in resume_data['skills']:
                    resume_score += 20
                if 'CI/CD Pipelines' in resume_data['skills']:
                    resume_score += 15
                if 'Microservices Architecture' in resume_data['skills']:
                    resume_score += 20
                if 'Serverless Architecture' in resume_data['skills']:
                    resume_score += 15

                # Android Development
                if 'Jetpack Compose' in resume_data['skills']:
                    resume_score += 15
                if 'Room Database' in resume_data['skills']:
                    resume_score += 10
                if 'Dagger/Hilt' in resume_data['skills']:
                    resume_score += 15
                if 'Retrofit' in resume_data['skills']:
                    resume_score += 10
                if 'Coroutines' in resume_data['skills']:
                    resume_score += 15
                if 'Firebase Integration' in resume_data['skills']:
                    resume_score += 20
                if 'Material Design' in resume_data['skills']:
                    resume_score += 10

                # iOS Development
                if 'SwiftUI' in resume_data['skills']:
                    resume_score += 15
                if 'Combine Framework' in resume_data['skills']:
                    resume_score += 15
                if 'Core Data' in resume_data['skills']:
                    resume_score += 10
                if 'ARKit' in resume_data['skills']:
                    resume_score += 20
                if 'HealthKit' in resume_data['skills']:
                    resume_score += 15
                if 'Push Notifications' in resume_data['skills']:
                    resume_score += 10
                if 'App Store Deployment' in resume_data['skills']:
                    resume_score += 15

                # UI/UX Design
                if 'User-Centered Design' in resume_data['skills']:
                    resume_score += 20
                if 'Interaction Design' in resume_data['skills']:
                    resume_score += 15
                if 'Information Architecture' in resume_data['skills']:
                    resume_score += 15
                if 'Usability Testing Tools' in resume_data['skills']:
                    resume_score += 20
                if 'Accessibility Design' in resume_data['skills']:
                    resume_score += 20
                if 'Motion Design' in resume_data['skills']:
                    resume_score += 15
                if 'Design Thinking' in resume_data['skills']:
                    resume_score += 20
                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Score: ' + str(score)+'**')
                # st.warning("** Note: This score is calculated based on the content that you have added in your Resume. **")
                st.balloons()
                link_to_be_send = "No"
                if resume_score > 50:
                    link_to_be_send = "Yes"

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                              str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                              str(recommended_skills),  str(link_to_be_send))


                ## Resume writing video
                # st.header("**Bonus Video for Resume Writing Tips💡**")
                # resume_vid = random.choice(resume_videos)
                # res_vid_title = fetch_yt_video(resume_vid)
                # st.subheader("✅ **"+res_vid_title+"**")
                # st.video(resume_vid)

                ## Interview Preparation Video
                # st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
                # interview_vid = random.choice(interview_videos)
                # int_vid_title = fetch_yt_video(interview_vid)
                # st.subheader("✅ **" + int_vid_title + "**")
                # st.video(interview_vid)

                connection.commit()
            else:
                st.error('Something went wrong..')
            
            csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSD13-A4x2xvuCVpuwao0zP2iyfFMf0Ew-aOat50kVPU8x_ycJn50k1p-A8XqT0w7lT6PtdM4K4UCWH/pub?output=csv"

            # Read data into a DataFrame
            def get_scores():
                try:
                    data = pd.read_csv(csv_url)
                    return data
                except Exception as e:
                    st.error(f"Failed to load data: {e}")
                    return pd.DataFrame()

            if resume_score >= 75:
                st.subheader("You are selected! Available for an interview?")
                if st.button("Yes"):
                    form_url = "https://docs.google.com/forms/d/e/1FAIpQLScUwha7oqCWfJOccGclQP22m0xD0jmFuLkVrU4GhnLjpXyyuw/viewform?usp=sf_link"
                    st.markdown(f'<a href="{form_url}" target="_blank">Please complete the online test by clicking here.</a>', unsafe_allow_html=True)
                
                if st.button("No"):
                    st.subheader('Choose the date that you are available for the interview')
                    interview_date1 = st.date_input("Interview Date", value=pd.to_datetime("today"), format="YYYY/MM/DD")
                    email_receiver1 = st.text_input('Please Enter your email ')
                    if st.button("Submit"):
                        # Prepare and send an email here if necessary or process the 'No' response further
                        pass

                email = st.text_input("Enter your email to check your score:")
                if st.button("Check Score"):
                    scores_df = get_scores()
                    user_score = scores_df[scores_df['Email Address'] == email.strip().lower()]  # Assuming email column and input are formatted correctly
                    if not user_score.empty:
                        user_latest_score = user_score['Score'].iloc[-1]
                        st.write(f"Your score is: {user_latest_score}")
                        user_latest_score, max_score = user_latest_score.split('/')
                        if int(user_latest_score) >= 6:
                            st.success("Congratulations! You have successfully passed the test and selected for this job.")
                        else:
                            st.error("Unfortunately, your score does not qualify you for further processing.")
                    else:
                        st.error("No scores found for this email. Please ensure you've entered the correct email and completed the test.")
            else:
                st.error("Sorry, you are not selected for the interview.")


    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'Admin' and ad_password == 'admin@1234':
                st.success("Welcome Admin")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills', 'Shortlisted'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)
                ## Admin Side Data

                x = ["Shortlisted", "Not shortlisted"]
                y = [1,5]

                st.subheader("📈 **AI Score based on the participants details**")
                fig, ax = plt.subplots()
                ax.bar(x, y)
                # Pass the Matplotlib figure to st.pyplot()
                st.pyplot(fig)

                resume_scores = df['Resume Score']
                shortlisted = df['Shortlisted']

                # Plot graph for 'Resume Score'
                st.subheader("📈 **Resume Score Distribution**")
                fig_resume_score, ax_resume_score = plt.subplots()
                ax_resume_score.hist(resume_scores, bins=20, edgecolor='black')
                ax_resume_score.set_xlabel('Resume Score')
                ax_resume_score.set_ylabel('Count')
                ax_resume_score.set_title('Distribution of Resume Scores')
                st.pyplot(fig_resume_score)

                # Plot graph for 'Shortlisted'
                st.subheader("📊 **Shortlisted Distribution**")
                fig_shortlisted, ax_shortlisted = plt.subplots()
                shortlisted_counts = shortlisted.value_counts()
                ax_shortlisted.bar(shortlisted_counts.index, shortlisted_counts.values, color=['red', 'green'])
                ax_shortlisted.set_xlabel('Shortlisted')
                ax_shortlisted.set_ylabel('Count')
                ax_shortlisted.set_title('Distribution of Shortlisted Candidates')
                st.pyplot(fig_shortlisted)

                
                st.text_input("Enter the shortlisted Candidates")

                if st.button("Submit"):
                    st.success(f"Sending mail")
                    

                #Two  lines to make our compiler able to draw:
                # query = 'select * from user_data;'
                # plot_data = pd.read_sql(query, connection)

                # ## Check the column names of the DataFrame
                # print(plot_data.columns)

                # # Assuming 'resume_score' is a numerical column
                # plot_data['resume_score'] = pd.to_numeric(plot_data['resume_score'], errors='coerce')  # Convert to numeric, coerce errors to NaN
                # plot_data['resume_score_bins'] = pd.cut(plot_data['resume_score'], bins=[0, 20, 40, 60, 80, 100], labels=['0-20', '21-40', '41-60', '61-80', '81-100'])

                # labels = plot_data['resume_score_bins'].unique()
                # values = plot_data['resume_score_bins'].value_counts()
                # st.subheader("📈 **Pie-Chart for Resume Score Bins**")
                # fig = px.pie(values=plot_data['resume_score_bins'].value_counts(), names=plot_data['resume_score_bins'].unique(), title='Distribution of Resume Scores in Bins')
                # st.plotly_chart(fig)



                # ### Pie chart for User's👨‍💻 Experienced Level
                # labels = plot_data.User_level.unique()
                # values = plot_data.User_level.value_counts()
                # st.subheader("📈 ** Pie-Chart for User's👨‍💻 Experienced Level**")
                # fig = px.pie(df, values=values, names=labels, title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                # st.plotly_chart(fig)
                
run()