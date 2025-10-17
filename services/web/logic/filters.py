from datetime import date, datetime, timedelta
from typing import List, Dict

def parse_date_safe(dstr: str | None):
    try:
        return datetime.strptime(dstr, "%Y-%m-%d").date() if dstr else None
    except Exception:
        return None

def matches_search(t: Dict, q: str) -> bool:
    if not q:
        return True
    q = q.lower().strip()
    return q in (t.get("name","").lower()) or q in (t.get("description","") or "").lower()

def apply_filter(tasks: List[Dict], view: str) -> List[Dict]:
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)

    out = []
    for t in tasks:
        d = parse_date_safe(t.get("date"))
        state = (t.get("state") or "PENDENTE").upper()

        if view == "Todas":
            pass
        elif view == "Hoje" and d != today:
            continue
        elif view == "Esta semana":
            if d is None or not (start_week <= d <= end_week):
                continue
        elif view == "Concluídas" and state != "CONCLUIDA":
            continue
        elif view == "Em andamento" and state != "ANDAMENTO":
            continue
        elif view == "Pendentes" and state != "PENDENTE":
            continue

        out.append(t)
    return out

def apply_sort(tasks: List[Dict], sort_by: str) -> List[Dict]:
    if sort_by == "Data (asc)":
        return sorted(tasks, key=lambda t: (parse_date_safe(t.get("date")) or date.max, t.get("name","").lower()))
    if sort_by == "Data (desc)":
        return sorted(tasks, key=lambda t: (parse_date_safe(t.get("date")) or date.min, t.get("name","").lower()), reverse=True)
    if sort_by == "Nome A→Z":
        return sorted(tasks, key=lambda t: t.get("name","").lower())
    if sort_by == "Nome Z→A":
        return sorted(tasks, key=lambda t: t.get("name","").lower(), reverse=True)
    return tasks
