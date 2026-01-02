from reportlab.pdfgen import canvas
import os

def generate_id_card(employee):
    """
    Generates an ID card PDF for an employee.
    Returns the generated file path.
    """

    emp_code = employee["emp_code"]
    name = employee["first_name"]

    # Ensure folder exists
    base_dir = "generated_files/id_cards"
    os.makedirs(base_dir, exist_ok=True)

    file_path = f"{base_dir}/{emp_code}.pdf"

    c = canvas.Canvas(file_path, pagesize=(240, 150))

    # Title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20, 120, "GTPL EMPLOYEE ID CARD")

    # Employee details
    c.setFont("Helvetica", 10)
    c.drawString(20, 95, f"Employee Code: {emp_code}")
    c.drawString(20, 80, f"Name: {name}")

    c.showPage()
    c.save()

    return file_path
