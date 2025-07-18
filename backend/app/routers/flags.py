from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
from ..database import get_db, get_db_type

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
            if get_db_type() == "postgres":
                cursor.execute("DELETE FROM user_flags WHERE email = %s", (email,))
            else:
                cursor.execute("DELETE FROM user_flags WHERE email = ?", (email,))
            
            # Insert new flags
            for flag in flags:
                if get_db_type() == "postgres":
                    cursor.execute("""
                        INSERT INTO user_flags (email, flag_name, flag_description, flag_color, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        email,
                        flag.get("name", ""),
                        flag.get("description", ""),
                        flag.get("color", "#000000"),
                        flag.get("isActive", False)
                    ))
                else:
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
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT flag_name, flag_description, flag_color, is_active
                    FROM user_flags 
                    WHERE email = %s
                    ORDER BY flag_name
                """, (email,))
            else:
                cursor.execute("""
                    SELECT flag_name, flag_description, flag_color, is_active
                    FROM user_flags 
                    WHERE email = ?
                    ORDER BY flag_name
                """, (email,))
            
            rows = cursor.fetchall()
            
            flags = []
            for row in rows:
                if hasattr(row, 'keys'):  # PostgreSQL with RealDictCursor
                    flags.append({
                        "id": row["flag_name"].lower().replace(" ", "_"),
                        "name": row["flag_name"],
                        "description": row["flag_description"],
                        "color": row["flag_color"],
                        "isActive": bool(row["is_active"])
                    })
                else:  # SQLite with regular cursor
                    flags.append({
                        "id": row[0].lower().replace(" ", "_"),
                        "name": row[0],
                        "description": row[1],
                        "color": row[2],
                        "isActive": bool(row[3])
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
            if get_db_type() == "postgres":
                cursor.execute("DELETE FROM user_flags WHERE email = %s", (email,))
            else:
                cursor.execute("DELETE FROM user_flags WHERE email = ?", (email,))
            db.commit()
        
        return {"message": "User flags cleared successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 