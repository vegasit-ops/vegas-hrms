"""
Add custom fields to Employee for PAN, IFSC, then populate data
"""
import frappe


def run():
    # Step 1: Add custom fields
    custom_fields = [
        {
            "fieldname": "pan_number",
            "label": "PAN Number",
            "fieldtype": "Data",
            "insert_after": "company_email"
        },
        {
            "fieldname": "ifsc_code",
            "label": "IFSC Code",
            "fieldtype": "Data",
            "insert_after": "bank_ac_no"
        },
    ]

    for cf in custom_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": cf["fieldname"]}):
            doc = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Employee",
                **cf
            })
            doc.insert(ignore_permissions=True)
            print(f"✓ Added field: {cf['fieldname']}")
        else:
            print(f"⊙ Already exists: {cf['fieldname']}")
    frappe.db.commit()

    # Step 2: Populate all employee data
    employees_data = {
        "HR-EMP-00001": {  # Mallikarjunarao P
            "pan_number": "ABCDE1234F",  # Placeholder - will be updated
            "cell_number": "9999999999",
        },
        "HR-EMP-00002": {  # Vadalasetty Gowthamkrishna
            "pan_number": "AVKPV0206E",
            "cell_number": "+91 7416988166",
            "bank_name": "Axis",
            "bank_ac_no": "921010018260398",
            "ifsc_code": "UTIB0002749",
            "personal_email": "gowtham.krishna1940@gmail.com",
        },
        "HR-EMP-00006": {  # Orugunta Vishnu Vardhan
            "pan_number": "AEFPO4240P",
            "cell_number": "9676777904",
            "bank_name": "SBI",
            "bank_ac_no": "44610211150",
            "ifsc_code": "SBIN0018816",
            "personal_email": "vishnuvardhan7904@gmail.com",
        },
        "HR-EMP-00007": {  # Pasupuleti Kalyani
            "pan_number": "HJUPP0325P",
            "cell_number": "7330623109",
            "bank_name": "UNION BANK OF INDIA",
            "bank_ac_no": "18912010001223",
            "ifsc_code": "UBIN0801895",
            "personal_email": "pasupuletikalyani60@gmail.com",
        },
        "HR-EMP-00008": {  # Vipparthi Venkata Sai Srinidhi
            "pan_number": "BUIPV8492C",
            "cell_number": "9347787099",
            "bank_name": "SBI",
            "bank_ac_no": "20401447002",
            "ifsc_code": "SBIN0001344",
            "personal_email": "nidhivipparthi2002@gmail.com",
        },
        "HR-EMP-00009": {  # K Vivian Sudharshan
            "pan_number": "BQTPS7250L",
            "cell_number": "9676009453",
            "bank_name": "ICICI",
            "bank_ac_no": "112301000744",
            "ifsc_code": "ICIC0001123",
            "personal_email": "vivian.sudharshan45@gmail.com",
        },
    }

    print("\n=== Updating employees ===")
    for emp_id, data in employees_data.items():
        emp = frappe.get_doc("Employee", emp_id)
        for field, value in data.items():
            try:
                emp.set(field, value)
            except Exception as e:
                print(f"  ! Couldn't set {emp_id}.{field}: {e}")
        emp.save(ignore_permissions=True)
        frappe.db.commit()
        # Verify
        emp.reload()
        print(f"  ✓ {emp_id} ({emp.employee_name}):")
        print(f"      PAN: {emp.get('pan_number')}")
        print(f"      Cell: {emp.get('cell_number')}")
        print(f"      Bank: {emp.bank_name} | A/c: {emp.bank_ac_no} | IFSC: {emp.get('ifsc_code')}")

    frappe.clear_cache()
    print("\n✓ Done!")


run()
