from database_client import supabase


def get_all_programs():
    response = supabase.table("programs").select("*").execute()
    if response.data:
        return response.data
    return []


def add_program(program_name, description=""):
    # Optional: Check first if it exists
    existing = supabase.table("programs").select("*").eq("program_name", program_name).execute()
    if existing.data:
        raise ValueError(f"Program '{program_name}' already exists.")
    
    response = supabase.table("programs").insert({
        "program_name": program_name,
        "description": description
    }).execute()
    return response.data


def delete_program(program_id):
    response = supabase.table("programs").delete().eq("programid", program_id).execute()
    return response.data
