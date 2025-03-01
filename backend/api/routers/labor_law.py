from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import supabase
from uuid import uuid4
from datetime import datetime

router = APIRouter()


class MessageInput(BaseModel):
    message: str
    id: str = None


# Create a new chat or continue an existing one
@router.post("/generate-answer")
async def generate_answer(msg: MessageInput):
    user_message = msg.message.lower()
    conversation_id = msg.id or str(
        uuid4()
    )  # Use provided conversation ID or create new one

    current_time = datetime.now().isoformat()

    # If no conversation_id is provided, create a new chat
    if not msg.id:
        # Create a new chat entry
        try:
            chat_response = (
                supabase.table("chats")
                .insert(
                    {
                        "id": conversation_id,
                        "title": "Labor Law Inquiry",
                        "last_updated": current_time,
                    }
                )
                .execute()
            )

            if not chat_response.data:
                raise HTTPException(status_code=400, detail="Failed to create chat")
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error creating chat: {str(e)}"
            )

    # Insert the user message into the chat_messages table
    try:
        user_message_response = (
            supabase.table("chat_messages")
            .insert(
                {
                    "message": msg.message,
                    "sender": "user",
                    "chat_id": conversation_id,
                    "timestamp": current_time,
                }
            )
            .execute()
        )

        if not user_message_response.data:
            raise HTTPException(status_code=400, detail="Failed to store user message")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error storing user message: {str(e)}"
        )

    # Generate the system's response
    if "labor" in user_message and "law" in user_message:
        answer = "Labor laws in Thailand regulate the rights of workers, including wages, working hours, and benefits."
    else:
        answer = "Please provide more details about your question regarding labor laws."

    # Insert the system's response into the chat_messages table
    try:
        system_response = (
            supabase.table("chat_messages")
            .insert(
                {
                    "message": answer,
                    "sender": "system",
                    "chat_id": conversation_id,
                    "timestamp": current_time,
                }
            )
            .execute()
        )

        if not system_response.data:
            raise HTTPException(
                status_code=400, detail="Failed to store system message"
            )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error storing system message: {str(e)}"
        )

    # Update the chat's last_updated timestamp
    try:
        supabase.table("chats").update({"last_updated": current_time}).eq(
            "id", conversation_id
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating chat: {str(e)}")

    # Return the generated answer
    return {"answer": answer, "conversationId": conversation_id}


@router.get("/chats")
async def get_chats():
    try:
        # Fetch chats ordered by last_updated
        chats_response = (
            supabase.table("chats")
            .select("*")
            .order("last_updated", desc=True)
            .execute()
        )

        return {"chats": chats_response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching chats: {str(e)}")


@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    try:
        # Fetch chat messages for the given chat_id
        chat_messages_response = (
            supabase.table("chat_messages")
            .select("*")
            .eq("chat_id", chat_id)
            .order("timestamp", desc=False)
            .execute()
        )

        return {"messages": chat_messages_response.data}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error fetching chat messages: {str(e)}"
        )


@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: str):
    try:
        # Delete chat and chat_messages for the given chat_id
        chats = supabase.table("chats").delete().eq("id", chat_id).execute()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting chat: {str(e)}")

    return {"message": "Chat deleted successfully"}