"""
Use SQL to override payment_days = date_diff(month_end, doj) after submission
This forces 20 days for Apr 10-30 (not 21 as Frappe defaults to).
"""
import frappe
from frappe.utils import getdate, add_months, get_first_day, get_last_day, today, date_diff


def run():
    today_date = getdate(today())

    # Wipe slips
    frappe.db.sql("UPDATE `tabSalary Slip` SET docstatus=2")
    frappe.db.sql("DELETE FROM `tabSalary Slip`")
    frappe.db.sql("DELETE FROM `tabSalary Detail` WHERE parenttype='Salary Slip'")
    frappe.db.commit()
    print("✓ Wiped slips")

    real_employees = [
        {"id": "HR-EMP-00001", "doj": "2024-01-01", "monthly_base": 100000},
        {"id": "HR-EMP-00009", "doj": "2026-04-10", "monthly_base": 55000},
        {"id": "HR-EMP-00007", "doj": "2025-10-13", "monthly_base": 45000},
        {"id": "HR-EMP-00006", "doj": "2025-12-22", "monthly_base": 45000},
        {"id": "HR-EMP-00008", "doj": "2025-12-22", "monthly_base": 45000},
        {"id": "HR-EMP-00002", "doj": "2026-04-10", "monthly_base": 250000},
    ]

    def get_months_range(start_date, end_date):
        months = []
        cur = get_first_day(start_date)
        end_first = get_first_day(end_date)
        while cur <= end_first:
            months.append(cur)
            cur = get_first_day(add_months(cur, 1))
        return months

    earnings_pct = {
        "Basic Salary": 0.50,
        "House Rent Allowance": 0.20,
        "Conveyance Allowance": 0.06,
        "Special Allowance": 0.14,
        "Medical Allowance": 0.10,
    }

    def calc_annual_tax(base):
        annual_gross = base * 12
        taxable = max(0, annual_gross - 75000)
        if taxable <= 1200000:
            return 0
        if taxable <= 400000:
            slab = 0
        elif taxable <= 800000:
            slab = (taxable - 400000) * 0.05
        elif taxable <= 1200000:
            slab = 20000 + (taxable - 800000) * 0.10
        elif taxable <= 1600000:
            slab = 60000 + (taxable - 1200000) * 0.15
        elif taxable <= 2000000:
            slab = 120000 + (taxable - 1600000) * 0.20
        elif taxable <= 2400000:
            slab = 200000 + (taxable - 2000000) * 0.25
        else:
            slab = 300000 + (taxable - 2400000) * 0.30
        return slab * 1.04

    slip_count = 0

    for emp_data in real_employees:
        doj = getdate(emp_data["doj"])
        months = get_months_range(doj, today_date)
        emp_name = frappe.db.get_value("Employee", emp_data["id"], "employee_name")
        base = emp_data["monthly_base"]
        annual_tax = calc_annual_tax(base)
        first_month = True

        for month_start in months:
            month_end = get_last_day(month_start)

            # Insert slip
            ss = frappe.new_doc("Salary Slip")
            ss.employee = emp_data["id"]
            ss.employee_name = emp_name
            ss.start_date = month_start
            ss.end_date = month_end
            ss.posting_date = month_end
            ss.salary_structure = "VEGAS IT GLOBAL Standard CTC-2"
            ss.payroll_frequency = "Monthly"
            ss.company = "VEGAS IT GLOBAL"
            ss.insert(ignore_permissions=True)
            ss.submit()
            frappe.db.commit()

            # MY CALCULATION (overrides Frappe's calc)
            month_days = date_diff(month_end, month_start) + 1  # 30 for April
            if doj > month_start:
                worked_days = date_diff(month_end, doj)  # 20 for Apr 10-30 (NO +1)
            else:
                worked_days = month_days

            ratio = worked_days / month_days

            # Recompute earnings
            new_earnings = {}
            gross = 0
            for comp, pct in earnings_pct.items():
                amt = round(base * pct * ratio, 2)
                new_earnings[comp] = amt
                gross += amt

            # Recompute deductions
            bs = new_earnings.get("Basic Salary", 0)
            new_deductions = {}
            new_deductions["Provident Fund"] = round(min(bs * 0.12, 1800 * ratio), 2)
            new_deductions["Professional Tax"] = 200
            new_deductions["Income Tax"] = round((annual_tax / 12) * ratio, 2)
            total_ded = sum(new_deductions.values())
            net_pay = gross - total_ded

            # Update via SQL (bypass Frappe validation)
            frappe.db.sql("""UPDATE `tabSalary Slip` SET
                total_working_days = %s,
                payment_days = %s,
                gross_pay = %s,
                total_deduction = %s,
                net_pay = %s,
                rounded_total = %s,
                base_gross_pay = %s,
                base_total_deduction = %s,
                base_net_pay = %s,
                base_rounded_total = %s
                WHERE name = %s""",
                (month_days, worked_days, gross, total_ded, net_pay, round(net_pay),
                 gross, total_ded, net_pay, round(net_pay), ss.name))

            # Update earnings amounts
            for comp, amt in new_earnings.items():
                frappe.db.sql("""UPDATE `tabSalary Detail` SET amount=%s, default_amount=%s
                    WHERE parent=%s AND parenttype='Salary Slip' AND salary_component=%s""",
                    (amt, amt, ss.name, comp))

            # Update deductions amounts
            for comp, amt in new_deductions.items():
                frappe.db.sql("""UPDATE `tabSalary Detail` SET amount=%s, default_amount=%s
                    WHERE parent=%s AND parenttype='Salary Slip' AND salary_component=%s""",
                    (amt, amt, ss.name, comp))

            # Update in_words
            from frappe.utils import money_in_words
            words = money_in_words(net_pay, "INR")
            frappe.db.sql("UPDATE `tabSalary Slip` SET total_in_words=%s, base_total_in_words=%s WHERE name=%s",
                (words, words, ss.name))

            frappe.db.commit()
            slip_count += 1

            if first_month:
                print(f"  ✓ {emp_name} {month_start.strftime('%b %Y')} (joining): {worked_days}/{month_days} days | gross=₹{gross:,.0f} pf=₹{new_deductions['Provident Fund']:,.0f} it=₹{new_deductions['Income Tax']:,.0f} net=₹{net_pay:,.0f}")
                first_month = False

    print(f"\n>>> {slip_count} slips created")

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL Apr 2026 Summary")
    print("=" * 80)
    print(f"{'Employee':<35} {'DOJ':<12} {'Days':<8} {'Gross':<12} {'IT':<10} {'Net Pay':<14}")
    print("-" * 95)

    for emp_data in real_employees:
        slip_name = frappe.db.get_value("Salary Slip",
            {"employee": emp_data["id"], "start_date": "2026-04-01", "docstatus": 1}, "name")
        if slip_name:
            row = frappe.db.get_value("Salary Slip", slip_name,
                ["employee_name", "total_working_days", "payment_days", "gross_pay", "net_pay"], as_dict=True)
            it = frappe.db.get_value("Salary Detail",
                {"parent": slip_name, "salary_component": "Income Tax"}, "amount") or 0
            days = f"{row.payment_days:.0f}/{row.total_working_days:.0f}"
            print(f"{row.employee_name:<35} {emp_data['doj']:<12} {days:<8} ₹{row.gross_pay:<11,.0f} ₹{it:<9,.0f} ₹{row.net_pay:<13,.0f}")

    print("\n✓ DONE!")


run()
