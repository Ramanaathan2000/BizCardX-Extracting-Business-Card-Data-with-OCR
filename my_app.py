import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
from sqlalchemy import create_engine


def image_to_text(path):

    input_img= Image.open(path)

    #converting image to array format
    image_arr= np.array(input_img)

    reader= easyocr.Reader(['en'])
    text= reader.readtext(image_arr, detail=0)
    return text,input_img


def extracted_text(texts):
    extrd_dict = {"NAME":[],"DESIGNATION":[],"COMPANY_NAME":[],"CONTACT":[],"EMAIL":[],
                  "WEBSITE":[],"ADDRESS":[],"PINCODE":[]}
    extrd_dict["NAME"].append(texts[0])
    extrd_dict["DESIGNATION"].append(texts[1])

    for i in range(2,len(texts)):
        if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):
            extrd_dict["CONTACT"].append(texts[i])

        elif "@" in texts[i] and ".com" in texts[i]:
            small =texts[i].lower()
            extrd_dict["EMAIL"].append(small)

        elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
            small = texts[i].lower()
            extrd_dict["WEBSITE"].append(small)

        elif "Tamil Nadu" in texts[i]  or "TamilNadu" in texts[i] or texts[i].isdigit():
            extrd_dict["PINCODE"].append(texts[i])

        elif re.match(r'^[A-Za-z]',texts[i]):
            extrd_dict["COMPANY_NAME"].append(texts[i])

        else:
            remove_colon = re.sub(r'[,;]', '', texts[i])
            extrd_dict["ADDRESS"].append(remove_colon)

    for key,value in extrd_dict.items():
        if len(value)>0:
            concadenate = ' '.join(value)
            extrd_dict[key] = [concadenate]
        else:
            value = 'NA'
            extrd_dict[key] = [value]

    return extrd_dict


# Streamlit Part

st.set_page_config(layout= "wide")

st.title("EXTRACTING BUSINESS CARD DATA WITH OCR")
st.write("")


with st.sidebar:
  select= option_menu("Main Menu",["ABOUT", "UPLOAD & MODIFY THE DATA OF BUSINESS CARD", "DATA REMOVAL"])

if select == "ABOUT":
  st.markdown("### :violet[**Technologies Used :**] PYTHON,EASY OCR, STREAMLIT, SQL, PANDAS")
  st.write("### :violet[**About :**] Bizcard is a Python application developed to streamline the extraction of essential information from business card images using Optical Character Recognition (OCR) technology. By integrating technologies like Python, EasyOCR, Streamlit, SQL, and Pandas, Bizcard offers a robust solution for automating the tedious task of manually inputting data from business cards.")
  st.write("### :violet[**Features :**] Image Upload: Users can upload business card images through the Streamlit interface.")
  st.write("### :red[**Text Extraction :**] Bizcard employs EasyOCR to extract text from uploaded business card images.")
  st.write("### :red[**Data Processing :**] Extracted text data is processed and structured into relevant fields such as name, designation, company, contact information, etc.")
  st.write("### :red[**Data Storage :**] Processed data is stored in a SQL database for easy access and retrieval.")
  st.write("### :red[**Data Presentation :**] Users can view the extracted information from business cards via the Streamlit interface, allowing for quick verification and review.")

elif select == "UPLOAD & MODIFY THE DATA OF BUSINESS CARD":

  img= st.file_uploader("Upload the Image", type= ["png", "jpg", "jpeg"], label_visibility= "hidden")

  if img is not None:
    st.image(img,width= 300)

    text_image,input_img= image_to_text(img)

    text_dict= extracted_text(text_image)

    if text_dict:
      st.success("TEXT IS EXTRACTED SUCCESSFULLY")

  method= st.radio("Select the Option",["None","Preview","Modify"])

  if method == "None":
    st.write("")

  if method == "Preview":

    df= pd.DataFrame(text_dict)

    #Converting Image to Bytes
    Image_bytes= io.BytesIO()
    input_img.save(Image_bytes,format= "PNG")

    image_data= Image_bytes.getvalue()

    #Creating dictionary
    data= {"Image":[image_data]}
    df_1= pd.DataFrame(data)

    concat_df= pd.concat([df,df_1],axis=1)
    st.image(input_img, width = 350)
    st.dataframe(concat_df)

  
  if method == "Modify":
    col1,col2= st.columns(2)

    df= pd.DataFrame(text_dict)

    #Converting Image to Bytes
    Image_bytes= io.BytesIO()
    input_img.save(Image_bytes,format= "PNG")

    image_data= Image_bytes.getvalue()

    #Creating dictionary
    data= {"Image":[image_data]}
    df_1= pd.DataFrame(data)

    concat_df= pd.concat([df,df_1],axis=1)

    with col1:
      modify_name= st.text_input("Name", text_dict["NAME"][0])
      modify_desig= st.text_input("Designation", text_dict["DESIGNATION"][0])
      modify_company= st.text_input("Company_Name", text_dict["COMPANY_NAME"][0])
      modify_contact= st.text_input("Contact", text_dict["CONTACT"][0])

      concat_df["NAME"] = modify_name
      concat_df["DESIGNATION"] = modify_desig
      concat_df["COMPANY_NAME"] = modify_company
      concat_df["CONTACT"] = modify_contact

    with col2:
      modify_email= st.text_input("Email", text_dict["EMAIL"][0])
      modify_web= st.text_input("Website", text_dict["WEBSITE"][0])
      modify_address= st.text_input("Address", text_dict["ADDRESS"][0])
      modify_pincode= st.text_input("Pincode", text_dict["PINCODE"][0])

      concat_df["EMAIL"] = modify_email
      concat_df["WEBSITE"] = modify_web
      concat_df["ADDRESS"] = modify_address
      concat_df["PINCODE"] = modify_pincode

    col1,col2= st.columns(2)
    with col1:
      button3= st.button("Save",use_container_width= True)

    if button3:
        conn = sqlite3.connect('bizcardx.db')

        table_name = 'bizcard_details'
        columns = concat_df.columns.tolist()

        # Define the table creation query
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS {} (
            NAME varchar(225),
            DESIGNATION varchar(225),
            COMPANY_NAME varchar(225),
            CONTACT varchar(225),
            EMAIL text,
            WEBSITE text,
            ADDRESS text,
            PINCODE varchar(225),
            Image text
        )'''.format(table_name)

        conn.execute(create_table_query)
        conn.commit()

               
        for index, row in concat_df.iterrows():
            insert_query = '''
                    INSERT INTO {} ({})
            VALUES (?,?,?,?,?,?,?,?,?)
            '''.format(table_name, ', '.join(columns))
            values= (row['NAME'], row['DESIGNATION'], row['COMPANY_NAME'], row['CONTACT'],
                    row['EMAIL'], row['WEBSITE'], row['ADDRESS'], row['PINCODE'],row["Image"])

            # Execute the insert query
            conn.execute(insert_query,values)

            # Commit the changes
            conn.commit()

            query = 'SELECT * FROM {}'.format(table_name)

            df_from_sqlite = pd.read_sql_query(query, conn)

            st.dataframe(df_from_sqlite)

            if st.dataframe:
              st.success("Saved Successfully")

if select == "DATA REMOVAL":

  conn = sqlite3.connect('bizcardx.db')
  cursor= conn.cursor()

  col1,col2= st.columns(2)
  with col1:
    cursor.execute("SELECT NAME FROM bizcard_details")
    conn.commit()
    table1= cursor.fetchall()

    names=[]

    for i in table1:
      names.append(i[0])

    name_select= st.selectbox("Select the Name",options= names)
  
  with col2:
    cursor.execute(f"SELECT DESIGNATION FROM bizcard_details WHERE NAME ='{name_select}'")
    conn.commit()
    table2= cursor.fetchall()

    designations= []

    for j in table2:
      designations.append(j[0])

    designation_select= st.selectbox("Select the Designation", options= designations)

  if name_select and designation_select:
    col1,col2,col3= st.columns(3)

    with col1:
      st.write(f"Selected Name : {name_select}")
      st.write("")
      st.write("")

      st.write(f"Selected Designation : {designation_select}")

    with col2:
      st.write("")
      st.write("")
      st.write("")
      st.write("")
      remove= st.button("Delete",use_container_width= True)

      if remove:
        conn.execute(f"DELETE FROM bizcard_details WHERE NAME ='{name_select}' AND DESIGNATION = '{designation_select}'")
        conn.commit()

        st.warning("DELETED")



