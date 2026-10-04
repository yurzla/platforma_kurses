import os, json, time, requests
import re
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Токен: user-token, полученный через Authorization Code
# Можно вписать строкой или задать через переменную окружения
# ─────────────────────────────────────────────────────────────
TOKEN = os.environ.get("access_token")
# ─────────────────────────────────────────────────────────────
# Список курсов
# ─────────────────────────────────────────────────────────────
kurses = [
    'https://stepik.org/course/67/',
    'https://stepik.org/course/100707/',
    'https://stepik.org/course/63085/',
    'https://stepik.org/course/266048/',
    'https://stepik.org/course/268534/',
    'https://stepik.org/course/292537/',
    'https://stepik.org/course/264409/',
    'https://stepik.org/course/182715/',
    'https://stepik.org/course/210768/',
    'https://stepik.org/course/209247/',
    'https://stepik.org/course/187230/',
    'https://stepik.org/course/129/',
    'https://stepik.org/course/287409/',
    'https://stepik.org/course/293290/',
    'https://stepik.org/course/215591/',
    'https://stepik.org/course/244364/',
    'https://stepik.org/course/240191/'
]

COURSE_IDS = [int(re.search(r'(\d+)/?$', url).group(1)) for url in kurses]

BASE = "https://stepik.org/api"
HEAD = {"Authorization": f"Bearer {TOKEN}"}
OUT = "stepik_dump"
os.makedirs(OUT, exist_ok=True)


def get(path, **params):
    """GET с автопагинацией. Возвращает список объектов."""
    url = f"{BASE}/{path}"
    results = []
    while url:
        try:
            r = requests.get(url, headers=HEAD, params=params, timeout=30)
        except requests.RequestException as e:
            print(f"  ! {path}: сеть упала ({e})")
            return results

        if r.status_code != 200:
            print(f"  ! {path} -> {r.status_code}: {r.text[:200]}")
            return results

        data = r.json()
        key = path.split("/")[0]
        results.extend(data.get(key, []))
        url = data.get("meta", {}).get("next")
        params = None  # next уже содержит query-строку
        time.sleep(0.2)  # щадим API

    return results


def dump_course(cid):
    print(f"\n=== Курс {cid} ===")

    course = get(f"courses/{cid}")
    if not course:
        print("  курс не найден или закрыт")
        return
    course = course[0]
    print(f"  {course.get('title')}")

    sections = get("sections", course=cid)
    units    = get("units", course=cid)

    # lesson_id -> section_id
    lesson_to_section = {}
    for u in units:
        lesson_to_section[u["lesson"]] = u["section"]

    lesson_ids = list(lesson_to_section.keys())

    result = {
        "course": course,
        "sections": sections,
        "units": units,
        "lessons": {},
        "steps": {},
    }

    for lid in lesson_ids:
        # метаданные урока
        l = get(f"lessons/{lid}")
        if l:
            result["lessons"][lid] = l[0]

        # шаги урока
        steps = get("steps", lesson=lid)
        for s in steps:
            result["steps"][s["id"]] = s

    # сохраняем
    path = os.path.join(OUT, f"course_{cid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  → {path}  (уроков: {len(lesson_ids)}, шагов: {len(result['steps'])})")


if __name__ == "__main__":
    if not TOKEN or TOKEN == "ВСТАВЬТЕ_СЮДА_ВАШ_ACCESS_TOKEN":
        raise SystemExit("Не задан токен. Впишите access_token в TOKEN или "
                         "установите переменную окружения access_token.")

    for cid in COURSE_IDS:
        try:
            dump_course(cid)
        except Exception as e:
            print(f"Курс {cid} упал: {e}")



# import os, json, time, requests
# import re
# from dotenv import load_dotenv

# load_dotenv()

# token = os.environ.get("access_token")
# #TOKEN = token 

# # HEAD = {"Authorization": f"Bearer {TOKEN}"}

# # r = requests.get(
# #     "https://stepik.org/api/stepics/1",
# #     headers=HEAD
# # )

# # print(r.status_code)
# # print(r.text[:1000])

# # r = requests.get(
# #     "https://stepik.org/api/steps/13889",
# #     headers=HEAD
# # )

# # print(r.status_code)
# # print(r.text[:3000])
# # kurses = ['https://stepik.org/course/67/', 'https://stepik.org/course/100707/', 'https://stepik.org/course/63085/',
# #           'https://stepik.org/course/266048/', 'https://stepik.org/course/268534/', 'https://stepik.org/course/292537/', 
# #           'https://stepik.org/course/264409/', 'https://stepik.org/course/182715/', 'https://stepik.org/course/210768/', 
# #           'https://stepik.org/course/209247/', 'https://stepik.org/course/187230/', 'https://stepik.org/course/129/', 
# #           ]
# kurses = ['https://stepik.org/course/67/']

# TOKEN = token  # export STEPIK_TOKEN=...
# COURSE_IDS = [int(re.search(r'(\d+)/?$', url).group(1)) for url in kurses]

# BASE = "https://stepik.org/api"
# HEAD = {"Authorization": f"Bearer {TOKEN}"}
# OUT = "stepik_dump"
# os.makedirs(OUT, exist_ok=True)

# def get(path, **params):
#     """GET с автопагинацией."""
#     url = f"{BASE}/{path}"
#     results = []
#     while url:
#         r = requests.get(url, headers=HEAD, params=params, timeout=30)
#         if r.status_code != 200:
#             print(f"  ! {path} -> {r.status_code}: {r.text[:200]}")
#             return results
#         data = r.json()
#         results.extend(data.get(path.split("/")[0], []))
#         url = data.get("meta", {}).get("next")
#         params = None  # next уже содержит query
#         time.sleep(0.2)  # бережём API
#     return results

# def dump_course(cid):
#     print(f"\n=== Курс {cid} ===")
#     course = get(f"courses/{cid}")
#     if not course:
#         return
#     course = course[0]
#     print(f"  {course.get('title')}")

#     sections = get("sections", course=cid)
#     units    = get("units", course=cid)

#     # lesson_id -> section_id
#     lesson_to_section = {}
#     for u in units:
#         lesson_to_section[u["lesson"]] = u["section"]

#     result = {
#         "course": course,
#         "sections": sections,
#         "units": units,
#         "lessons": {},
#         "steps": {},
#     }

#     # уроки
#     lesson_ids = list(lesson_to_section.keys())
#     for lid in lesson_ids:
#         steps = get("steps", lesson=lid)

#         for s in steps:
#             sid = s["id"]
#             result["steps"][sid] = s

#     # шаги и их содержимое
#     for lid in lesson_ids:
#         steps = get("steps", lesson=lid)
#         for s in steps:
#             sid = s["id"]
#             result["steps"][sid] = s
#             # step-sources — тут текст/варианты ответов
#             src = get(f"step-sources/{s.get('stepSource', s.get('id'))}")
#             if not src:
#                 src = get("step-sources", step=sid)
#             if src:
#                 result["step_sources"][sid] = src[0]

#     # сохраняем
#     path = os.path.join(OUT, f"course_{cid}.json")
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(result, f, ensure_ascii=False, indent=2)
#     print(f"  → {path}  (уроков: {len(lesson_ids)}, шагов: {len(result['steps'])})")

# for cid in COURSE_IDS:
#     try:
#         dump_course(cid)
#     except Exception as e:
#         print(f"Курс {cid} упал: {e}")