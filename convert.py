import json
import uuid
import time
import os
from datetime import datetime

# Constants
DEFAULT_MODEL = "openai/chatgpt-4o-latest"
USER_ID = str(uuid.uuid4())
IMPORTED_TRACKING_FILE = "~/chatgpt/imported.json"

def load_imported_conversations():
    """Load the list of already imported conversations."""
    if os.path.exists(IMPORTED_TRACKING_FILE):
        try:
            with open(IMPORTED_TRACKING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_imported_conversation(conv_id, title):
    """Save a conversation as imported."""
    imported = load_imported_conversations()
    imported[conv_id] = {
        "title": title,
        "imported_date": datetime.now().isoformat()
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(IMPORTED_TRACKING_FILE), exist_ok=True)
    
    with open(IMPORTED_TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(imported, f, indent=2)

def convert_chatgpt_to_openwebui(chatgpt_data):
    openwebui_chats = []
    imported_convs = load_imported_conversations()

    for conv_index, conv in enumerate(chatgpt_data):
        # Check if conversation was already imported
        conv_id = conv.get("id")
        if conv_id and conv_id in imported_convs:
            print(f"[SKIP] Conversation '{conv.get('title', 'Untitled')}' already imported on {imported_convs[conv_id]['imported_date']}")
            continue
            
        mapping = conv.get("mapping", {})
        if not mapping:
            continue

        messages_dict = {}
        messages_list = []
        current_id = conv.get("current_node")

        created_at = int(conv.get("create_time") or time.time())
        updated_at = int(conv.get("update_time") or created_at)
        root_timestamp = int(created_at * 1000)

        # Track parent/child relationships
        parent_child_map = {}

        for node_id, node_data in mapping.items():
            msg = node_data.get("message")
            if not msg:
                continue

            role = msg["author"]["role"]
            msg_id = msg["id"]
            parent_id = node_data.get("parent")
            children_ids = node_data.get("children", [])

            # Flatten content safely
            raw_parts = msg.get("content", {}).get("parts", [])
            parts = [p if isinstance(p, str) else json.dumps(p, ensure_ascii=False) for p in raw_parts]
            content = "\n".join(parts).strip()

            if not content:
                continue

            timestamp = int(msg.get("create_time") or time.time())

            message_obj = {
                "id": msg_id,
                "parentId": parent_id,
                "childrenIds": children_ids,
                "role": role,
                "content": content,
                "timestamp": timestamp
            }

            if role == "assistant":
                message_obj.update({
                    "model": DEFAULT_MODEL,
                    "modelName": DEFAULT_MODEL,
                    "modelIdx": 0,
                    "userContext": None,
                    "lastSentence": content.split("\n")[-1] if "\n" in content else content,
                    "done": True,
                    "context": None,
                    "info": {
                        "total_duration": 0,
                        "load_duration": 0,
                        "prompt_eval_count": 0,
                        "prompt_eval_duration": 0,
                        "eval_count": 0,
                        "eval_duration": 0
                    }
                })
            else:
                message_obj["models"] = [DEFAULT_MODEL]

            messages_dict[msg_id] = message_obj
            messages_list.append(message_obj)

        # Sort messages by timestamp to get proper chronological order
        messages_list.sort(key=lambda x: x["timestamp"])
        
        # Rebuild parent-child relationships properly
        valid_msg_ids = {m["id"] for m in messages_list}
        
        # Clear all children arrays first
        for msg in messages_list:
            msg["childrenIds"] = []
        
        # Rebuild parent-child relationships in chronological order
        for i, msg in enumerate(messages_list):
            if i == 0:
                # First message is always root
                msg["parentId"] = None
            else:
                # Link to previous message
                prev_msg = messages_list[i-1]
                msg["parentId"] = prev_msg["id"]
                prev_msg["childrenIds"].append(msg["id"])
        
        root_message = messages_list[0] if messages_list else None

        if not root_message:
            print(f"[WARN] Skipping conversation {conv_index} — no valid root user message found.")
            print(f"Message sample:")
            for m in messages_list:
                print(f"- role: {m['role']}, parentId: {m['parentId']}, content: {m['content'][:60]}")
            continue

        chat_title = conv.get("title") or "Chat"
        last_msg_id = messages_list[-1]["id"] if messages_list else None

        chat_entry = {
            "id": str(uuid.uuid4()),
            "user_id": USER_ID,
            "title": chat_title,
            "chat": {
                "id": "",  # Required for Open-WebUI
                "title": chat_title,
                "models": [DEFAULT_MODEL],
                "params": {},
                "history": {
                    "messages": messages_dict,
                    "currentId": last_msg_id
                },
                "messages": messages_list,
                "tags": [],
                "timestamp": root_timestamp,
                "files": []
            },
            "updated_at": updated_at,
            "created_at": created_at,
            "share_id": None,
            "archived": False,
            "pinned": False,
            "meta": {},
            "folder_id": None,
        }

        openwebui_chats.append(chat_entry)
        
        # Mark conversation as imported
        if conv_id:
            save_imported_conversation(conv_id, chat_title)
            print(f"[IMPORTED] '{chat_title}' - marked as imported")

    return openwebui_chats

# --- File I/O ---
def main():
    input_file = "~/chatgpt/chatgpt-export.json"
    output_file = "~/chatgpt/converted-for-open-webui.json"

    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        chatgpt_data = json.load(f)

    converted = convert_chatgpt_to_openwebui(chatgpt_data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(converted, f, indent=2)

    print(f"[DONE] Converted {len(converted)} conversations → {output_file}")

if __name__ == "__main__":
    main()
