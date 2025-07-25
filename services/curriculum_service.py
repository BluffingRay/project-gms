from database_client import supabase


def get_all_curriculum_subjects():
    response = supabase.table('curriculum_subjects').select("*").execute()
    return response.data


def add_curriculum_subject(data):
    return supabase.table('curriculum_subjects').insert(data).execute()


def delete_curriculum_subject(subject_id):
    return supabase.table('curriculum_subjects').delete().eq('id', subject_id).execute()

def update_curriculum_subject(data):
    subject_id = data.pop("id", None)
    if not subject_id:
        raise ValueError("Subject ID is required for update.")

    # Update the row with matching id
    response = supabase.table('curriculum_subjects') \
                      .update(data) \
                      .eq('id', subject_id) \
                      .execute()

    return response