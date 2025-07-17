from supabase import create_client, Client
import streamlit as st
import bcrypt

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Hash password before saving
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Verify password on login
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_account(user_id, password, fullname):
    existing = supabase.table("users").select("id").eq("id", user_id).execute().data
    if existing:
        return False, "ID already exists."
    hashed_pw = hash_password(password)
    supabase.table("users").insert({
        "id": user_id,
        "fullname": fullname,
        "password": hashed_pw
    }).execute()
    return True, "Account created successfully."

def verify_login(user_id, password):
    result = supabase.table("users").select("*").eq("id", user_id).execute().data

    if not result:
        return None
    
    user = result[0]

    if check_password(password, user["password"]):
        return user
    
    return None
