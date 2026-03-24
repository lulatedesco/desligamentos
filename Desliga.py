import requests
import json

from datetime import datetime, timedelta

def get_target_date():
    today = datetime.now()

    # Não roda fim de semana
    if today.weekday() >= 5:
        return None

    # Segunda -> sexta
    if today.weekday() == 0:
        target = today - timedelta(days=3)
    else:
        target = today - timedelta(days=1)

    return target.strftime("%Y-%m-%d")

# =========================
# CONFIG
# =========================
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET = os.getenv("SECRET")
TENANT = os.getenv("TENANT")

# =========================
# AUTH
# =========================
def get_token():
    url = "https://platform.senior.com.br/t/senior.com.br/bridge/1.0/rest/platform/authentication/actions/loginWithKey"

    payload = {
        "accessKey": ACCESS_KEY,
        "secret": SECRET,
        "tenantName": TENANT
    }

    response = requests.post(url, json=payload)

    print("AUTH STATUS:", response.status_code)
    print("AUTH RESPONSE:", response.text)

    response.raise_for_status()

    data = response.json()

    json_token = data.get("jsonToken")

    if isinstance(json_token, str):
        json_token = json.loads(json_token)

    token = json_token.get("access_token")

    if not token:
        raise Exception("Token não encontrado")

    return token


# =========================
# GET ALL EMPLOYEES
# =========================
def get_all_employees(token):
    url = "https://api.senior.com.br/hcm/employeejourney/getEmployee"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "client_id": "9584f64a-0df0-49c2-8c5a-545124331d1b"
    }

    all_records = []
    
    offset = 0
    size = 100

    while True:
        payload = {
            "size": size,
            "offset": offset,
            "displayFields": "registerNumber,dismissalDate,department.name,department.code,person.fullName, emails.email",
            "filter": "",
            "orderBy": ""
        }
        
        # 🔥 TUDO isso precisa estar dentro do while
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print("ERROR BODY:", response.text)
            response.raise_for_status()

        data = response.json()

        contents = data.get("contents", [])
        total_pages = data.get("totalPages", 1)

        all_records.extend(contents)

        #print(f"PAGE {offset} -> {len(contents)} registros")
        
        if offset >= total_pages - 1:
            break

        offset += 1

    print("TOTAL COLETADO:", len(all_records))

    return all_records

# =========================
# MAIN
# =========================
def main():
    token = get_token()

    #print("\nTOKEN OK\n")

    employees = get_all_employees(token)

    #target_date = "2026-03-24"
    
    target_date = get_target_date()

    if not target_date:
      #print("Fim de semana - não executa")
      return

    filtered = []

    for emp in employees:
        dismissal = emp.get("dismissalDate")

        if not dismissal:
            continue

        date_only = dismissal.split("T")[0]

        if date_only == target_date:
            filtered.append(emp)

    print("TOTAL DESLIGADOS:", len(filtered))
    #input("Pressione ENTER para continuar...")

    file_name = f"Desligados_{target_date}.json"

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"Arquivo salvo: {file_name}")

    print("\nTOTAL REGISTROS:", len(employees))

    # mostra alguns exemplos
    #for emp in filtered:
    #    print(json.dumps(emp, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()