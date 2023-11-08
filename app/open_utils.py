import streamlit as st
import boto3
import random

bucket_key = st.secrets["client_bucket"]['BUCKET_idkey']
bucket_secret = st.secrets["client_bucket"]['BUCKET_secretkey']
bucket_url = st.secrets["client_bucket"]['BUCKET_url']
bucket_name = st.secrets["client_bucket"]['BUCKET_name']

#LOCAT
username_input_text = ["Käyttäjätunnus","Username"]
password_input_text = ["Salasana","Password"]
incorrect_warning = ["😕 Käyttäjä tai tunnus on väärin","😕 User not known or password incorrect"]

#simple auth
def check_password(lin=0):
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input(username_input_text[lin], on_change=password_entered, key="username")
        st.text_input(password_input_text[lin], type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(username_input_text[lin], on_change=password_entered, key="username")
        st.text_input(password_input_text[lin], type="password", on_change=password_entered, key="password")
        st.error(incorrect_warning[lin])
        return False
    else:
        # Password correct.
        return True


def get_random_image_url_from_collection(bucket_folder):
    
    #use bucket..
    s3_client = boto3.client('s3', endpoint_url=f"https://{bucket_url}",
                                aws_access_key_id=bucket_key,
                                aws_secret_access_key=bucket_secret)

    # Add a trailing slash if not present
    if not bucket_folder.endswith('/'):
        bucket_folder += '/'
        
    # List objects in a specified folder by using the prefix parameter
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=bucket_folder)
    
    # Retrieve only the keys from the contents that are not folders (i.e., do not end with "/")
    image_keys = [content['Key'] for content in response.get('Contents', []) if not content['Key'].endswith('/')]
    
    # Choose a random key from the list
    if not image_keys:
        return None  # or a default image key
    
    selected_image_key = random.choice(image_keys)
    
    # Construct the full URL for the background image
    image_url = f"https://{bucket_name}.{bucket_url}/{selected_image_key}"
    
    return image_url
        




