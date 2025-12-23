from typing import Dict, Any, List
from db import get_cursor
from models.utils import row_to_dict

# ---------------- FETCH PROFILE ----------------
def get_employee_profile(emp_code: str) -> Dict[str, Any]:
    conn, cur = get_cursor()
    profile = {}

    try:
        # EMPLOYEE
        cur.execute("""
            SELECT emp_code, first_name, last_name, father_name, dob, gender, marital_status,
                   blood_group, designation, department, manager, location,
                   marriage_date, wife_name, wife_dob, children_name, children_dob,
                   insurance_number, vehicle_number, driving_license_number
            FROM employees
            WHERE emp_code = %s
        """, (emp_code,))
        emp = cur.fetchone()
        profile["employee"] = row_to_dict(emp) if emp else None

        # EMERGENCY CONTACTS
        cur.execute("""
            SELECT id, name, relationship, phone, alternate_phone, address, email
            FROM employee_emergency_contacts
            WHERE emp_code = %s
            ORDER BY id
        """, (emp_code,))
        emg = cur.fetchall()
        profile["emergency_contacts"] = [row_to_dict(r) for r in emg]

        # STATUTORY
        cur.execute("""
            SELECT bank_name, account_number, ifsc_code, pan_number,
                   epf_uan_ssn, aadhar_number, of_number, esi_number
            FROM employee_statutory
            WHERE emp_code = %s
        """, (emp_code,))
        stat = cur.fetchone()
        profile["statutory"] = row_to_dict(stat) if stat else None

        return profile

    finally:
        cur.close()
        conn.close()


# ---------------- UPDATE HELPERS ----------------
def update_employee(emp_code: str, data: dict, allowed: List[str]):
    fields = []
    values = []

    for k in allowed:
        if k in data:
            fields.append(f"{k} = %s")
            values.append(data[k])

    if not fields:
        return {"updated": False, "message": "No valid fields"}

    values.append(emp_code)

    conn, cur = get_cursor()
    try:
        cur.execute(
            f"UPDATE employees SET {', '.join(fields)} WHERE emp_code = %s",
            tuple(values)
        )
        conn.commit()
        return {"updated": True}
    finally:
        cur.close()
        conn.close()


def update_personal(emp_code, data):
    return update_employee(emp_code, data,
        ["first_name", "last_name", "father_name", "dob",
         "gender", "marital_status", "blood_group"])


def update_official(emp_code, data):
    return update_employee(emp_code, data,
        ["designation", "department", "manager", "location"])


def update_family(emp_code, data):
    return update_employee(emp_code, data,
        ["marriage_date", "wife_name", "wife_dob",
         "children_name", "children_dob"])


def update_vehicle(emp_code, data):
    return update_employee(emp_code, data,
        ["insurance_number", "vehicle_number", "driving_license_number"])


# ---------------- STATUTORY ----------------
def upsert_statutory(emp_code, data):
    conn, cur = get_cursor()
    try:
        cur.execute(
            "SELECT 1 FROM employee_statutory WHERE emp_code = %s",
            (emp_code,)
        )
        exists = cur.fetchone()

        fields = list(data.keys())
        values = list(data.values())

        if exists:
            sets = ", ".join([f"{k} = %s" for k in fields])
            cur.execute(
                f"UPDATE employee_statutory SET {sets} WHERE emp_code = %s",
                tuple(values + [emp_code])
            )
        else:
            cols = ", ".join(["emp_code"] + fields)
            placeholders = ", ".join(["%s"] * (len(fields) + 1))
            cur.execute(
                f"INSERT INTO employee_statutory ({cols}) VALUES ({placeholders})",
                tuple([emp_code] + values)
            )

        conn.commit()
        return {"updated": True}

    finally:
        cur.close()
        conn.close()


# ---------------- EMERGENCY CONTACTS ----------------
def upsert_emergency_contacts(emp_code, contacts: List[dict]):
    conn, cur = get_cursor()
    try:
        cur.execute(
            "DELETE FROM employee_emergency_contacts WHERE emp_code = %s",
            (emp_code,)
        )

        for c in contacts:
            cur.execute("""
                INSERT INTO employee_emergency_contacts
                (emp_code, name, relationship, phone,
                 alternate_phone, address, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                emp_code,
                c.get("name"),
                c.get("relationship"),
                c.get("phone"),
                c.get("alternate_phone"),
                c.get("address"),
                c.get("email"),
            ))

        conn.commit()
        return {"updated": True, "count": len(contacts)}

    finally:
        cur.close()
        conn.close()
