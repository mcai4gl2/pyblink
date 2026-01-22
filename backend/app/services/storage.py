"""Storage service for saving and loading playgrounds."""

import json
import logging
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent.parent / "data" / "playgrounds"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Retention period (30 days)
RETENTION_DAYS = 30


def generate_id(length: int = 8) -> str:
    """Generate a random alphanumeric ID.
    
    Args:
        length: Length of the ID (default: 8)
        
    Returns:
        Random alphanumeric string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def save_playground(
    schema: str,
    input_format: str,
    input_data: str,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> Tuple[str, str]:
    """Save a playground to file.
    
    Args:
        schema: Blink schema definition
        input_format: Input format name
        input_data: Input message data
        title: Optional title
        description: Optional description
        
    Returns:
        Tuple of (playground_id, file_path)
        
    Raises:
        IOError: If file save fails
    """
    # Generate unique ID
    playground_id = generate_id()
    
    # Ensure uniqueness (very unlikely collision, but check anyway)
    max_attempts = 10
    for _ in range(max_attempts):
        file_path = STORAGE_DIR / f"{playground_id}.json"
        if not file_path.exists():
            break
        playground_id = generate_id()
    else:
        raise IOError("Failed to generate unique playground ID")
    
    # Create playground data
    playground_data = {
        "id": playground_id,
        "schema": schema,
        "input_format": input_format,
        "input_data": input_data,
        "title": title,
        "description": description,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Save to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(playground_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved playground {playground_id} to {file_path}")
        return playground_id, str(file_path)
        
    except Exception as e:
        logger.error(f"Failed to save playground {playground_id}: {e}")
        raise IOError(f"Failed to save playground: {str(e)}")


def load_playground(playground_id: str) -> Optional[Dict[str, Any]]:
    """Load a playground from file.
    
    Args:
        playground_id: Playground ID
        
    Returns:
        Playground data dictionary, or None if not found
        
    Raises:
        IOError: If file read fails
    """
    file_path = STORAGE_DIR / f"{playground_id}.json"
    
    if not file_path.exists():
        logger.warning(f"Playground {playground_id} not found")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            playground_data = json.load(f)
        
        logger.info(f"Loaded playground {playground_id}")
        return playground_data
        
    except Exception as e:
        logger.error(f"Failed to load playground {playground_id}: {e}")
        raise IOError(f"Failed to load playground: {str(e)}")


def cleanup_old_playgrounds() -> Tuple[int, int]:
    """Delete playgrounds older than RETENTION_DAYS.
    
    Returns:
        Tuple of (deleted_count, error_count)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    deleted_count = 0
    error_count = 0
    
    logger.info(f"Starting playground cleanup (retention: {RETENTION_DAYS} days)")
    
    for file_path in STORAGE_DIR.glob("*.json"):
        try:
            # Load playground to check creation date
            with open(file_path, 'r', encoding='utf-8') as f:
                playground_data = json.load(f)
            
            created_at_str = playground_data.get("created_at")
            if not created_at_str:
                logger.warning(f"No created_at in {file_path.name}, skipping")
                continue
            
            created_at = datetime.fromisoformat(created_at_str)
            
            # Delete if older than cutoff
            if created_at < cutoff_date:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Deleted old playground: {file_path.name} (created: {created_at_str})")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing {file_path.name}: {e}")
    
    logger.info(f"Cleanup complete: deleted {deleted_count}, errors {error_count}")
    return deleted_count, error_count


def get_playground_count() -> int:
    """Get the total number of saved playgrounds.
    
    Returns:
        Number of playground files
    """
    return len(list(STORAGE_DIR.glob("*.json")))
