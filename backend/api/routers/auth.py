from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..database import supabase

router = APIRouter()


# Pydantic model for request validation
class AuthRequest(BaseModel):
    email: str
    password: str


# Signup Route
@router.post("/signup")
async def signup(request: AuthRequest):
    try:
        # Attempt to sign up the user using Supabase authentication
        auth_response = supabase.auth.sign_up(
            {"email": request.email, "password": request.password}
        )

        if auth_response.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")

        # Return success message along with the access token
        access_token = auth_response.session.access_token
        return JSONResponse(content={"access_token": access_token}, status_code=201)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Login Route
@router.post("/login")
async def login(request: AuthRequest):
    try:
        # Attempt to sign in the user using Supabase authentication
        auth_response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )

        if auth_response.user is None:
            raise HTTPException(status_code=400, detail="Login failed")

        # Return success message along with the access token
        access_token = auth_response.session.access_token
        return JSONResponse(content={"access_token": access_token}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Logout Route
@router.post("/logout")
async def logout():
    try:
        # Sign out the user from Supabase (invalidates the session)
        supabase.auth.sign_out()
        return JSONResponse(
            content={"message": "Logged out successfully"}, status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
