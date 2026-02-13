import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def paginate_list(items: List, page: int, per_page: int = 20) -> Dict:
    """
    Ro'yxatni sahifalarga bo'lish
    
    Args:
        items: Sahifalanadigan ro'yxat
        page: Joriy sahifa (1-based)
        per_page: Har bir sahifadagi elementlar soni
    
    Returns:
        Dict: {
            'items': joriy sahifadagi elementlar,
            'total_pages': umumiy sahifalar soni,
            'current_page': joriy sahifa,
            'has_next': keyingi sahifa bormi,
            'has_previous': oldingi sahifa bormi
        }
    """
    start = (page - 1) * per_page
    end = start + per_page
    
    total_pages = (len(items) + per_page - 1) // per_page
    
    return {
        'items': items[start:end],
        'total_pages': total_pages,
        'current_page': page,
        'has_next': end < len(items),
        'has_previous': page > 1
    }


def group_by_category(movies: List[Dict]) -> Dict[str, List]:
    """
    Kinolar ro'yxatini kategoriya bo'yicha guruhlash
    
    Args:
        movies: Kinolar ro'yxati
    
    Returns:
        Dict: Kategoriya bo'yicha guruhlangan kinolar
    """
    grouped = {}
    
    for movie in movies:
        category = movie.get('category', 'unknown')
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(movie)
    
    return grouped


def format_number(num: int) -> str:
    """Sonni formatlash (1000 -> 1,000)"""
    return f"{num:,}"


def get_time_ago(timestamp) -> str:
    """
    Vaqtni "necha vaqt oldin" formatida qaytarish
    
    Args:
        timestamp: datetime obyekti
    
    Returns:
        str: Masalan: "5 daqiqa oldin", "2 soat oldin"
    """
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} yil oldin"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} oy oldin"
    elif diff.days > 7:
        weeks = diff.days // 7
        return f"{weeks} hafta oldin"
    elif diff.days > 0:
        return f"{diff.days} kun oldin"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} soat oldin"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} daqiqa oldin"
    else:
        return "hozirgina"


def split_message(text: str, max_length: int = 4096) -> List[str]:
    """
    Uzun xabarni qismlarga bo'lish (Telegram limiti 4096)
    
    Args:
        text: Bo'linadigan matn
        max_length: Har bir qismning maksimal uzunligi
    
    Returns:
        List[str]: Qismlarga bo'lingan matnlar
    """
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 <= max_length:
            current_part += line + '\n'
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = line + '\n'
    
    if current_part:
        parts.append(current_part.strip())
    
    return parts


def build_menu(buttons: List, n_cols: int = 2) -> List:
    """
    Tugmalarni matritsa shaklida joylashtirish
    
    Args:
        buttons: InlineKeyboardButton lar ro'yxati
        n_cols: Har bir qatordagi tugmalar soni
    
    Returns:
        List: Qatorlarga bo'lingan tugmalar
    """
    menu = []
    for i in range(0, len(buttons), n_cols):
        menu.append(buttons[i:i + n_cols])
    return menu


def safe_int(value: Any, default: int = 0) -> int:
    """
    Xavfsiz int o'girish
    
    Args:
        value: O'giriladigan qiymat
        default: Xatolik bo'lganda qaytariladigan qiymat
    
    Returns:
        int: O'girilgan son yoki default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def extract_code_from_callback(data: str, prefix: str) -> int:
    """
    Callback data dan kodni ajratib olish
    
    Args:
        data: Callback data (masalan: "part_123_2")
        prefix: Prefix (masalan: "part_")
    
    Returns:
        int: Kod (123)
    """
    try:
        parts = data.split('_')
        if len(parts) >= 2 and parts[0] == prefix.replace('_', ''):
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return 0


def extract_part_from_callback(data: str) -> tuple:
    """
    Callback data dan kod va qismni ajratib olish
    
    Args:
        data: Callback data (masalan: "part_123_2")
    
    Returns:
        tuple: (code, part) - (123, 2)
    """
    try:
        parts = data.split('_')
        if len(parts) == 3 and parts[0] == "part":
            code = int(parts[1])
            part = int(parts[2])
            return code, part
    except (ValueError, IndexError):
        pass
    return 0, 0
