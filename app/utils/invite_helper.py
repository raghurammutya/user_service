import uuid

def generate_invite_link(group_id: int):
    invite_code = uuid.uuid4().hex
    return f"https://your-service.com/invite/{group_id}/{invite_code}"