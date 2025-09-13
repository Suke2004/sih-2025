import uuid

def save_uploaded_file(upload_file) -> str:
    file_name = f"temp_{uuid.uuid4().hex}.jpg"
    with open(file_name, "wb") as f:
        f.write(upload_file)
    return file_name
