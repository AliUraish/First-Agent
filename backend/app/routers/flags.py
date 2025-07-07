from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
from ..database import get_db

router = APIRouter(prefix="/flags", tags=["flags"])

@router.post("/save")
async def save_user_flags(flags_data: Dict[str, Any]):
    """Save user's flag configurations"""
    try:
        email = flags_data.get("email")
        flags = flags_data.get("flags", [])
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        with get_db() as db:
            cursor = db.cursor()
            
            # Clear existing flags for this user
            cursor.execute("DELETE FROM user_flags WHERE email = ?", (email,))
            
            # Insert new flags
            for flag in flags:
                cursor.execute("""
                    INSERT INTO user_flags (email, flag_name, flag_description, flag_color, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    email,
                    flag.get("name", ""),
                    flag.get("description", ""),
                    flag.get("color", "#000000"),
                    flag.get("isActive", False)
                ))
            
            db.commit()
        
        return {"message": "Flags saved successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/load/{email}")
async def load_user_flags(email: str):
    """Load user's saved flag configurations"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute("""
                SELECT flag_name, flag_description, flag_color, is_active
                FROM user_flags 
                WHERE email = ?
                ORDER BY flag_name
            """, (email,))
            
            rows = cursor.fetchall()
            
            flags = []
            for row in rows:
                flags.append({
                    "id": row["flag_name"].lower().replace(" ", "_"),
                    "name": row["flag_name"],
                    "description": row["flag_description"],
                    "color": row["flag_color"],
                    "isActive": bool(row["is_active"])
                })
            
            return {"flags": flags}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear/{email}")
async def clear_user_flags(email: str):
    """Clear all flags for a user (for testing/reset purposes)"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM user_flags WHERE email = ?", (email,))
            db.commit()
        
        return {"message": "User flags cleared successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 