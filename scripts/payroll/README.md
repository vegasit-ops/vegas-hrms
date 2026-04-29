# Payroll Scripts

Production scripts for VEGAS IT GLOBAL HRMS payroll management.

## Files

- **`generate_payslips.py`** — Wipes existing salary slips, recreates them from each employee's DOJ to today's month with proper proration:
  - Calendar days (30/31) used as denominator
  - Joining month: `worked_days = month_end - DOJ` (excluding joining day)
  - PF capped at ₹1,800 (12% of Basic, max ₹15k wage)
  - Professional Tax: ₹200 (AP/TS slab)
  - Income Tax: India FY 2025-26 (Budget 2025) New Regime + 4% cess
    - 87A rebate: 0 tax up to ₹12L taxable

- **`create_print_format.py`** — Creates the "VEGAS Payslip" Print Format (Indutech-style 1-page layout) with:
  - VEGAS IT GLOBAL header (logo + address + email + website)
  - Employee info: Name, Emp ID, DOJ, PAN, Bank, A/C No, IFSC, PF Account, Designation, Department, Gender
  - Earnings & Deductions side-by-side table
  - Gross Pay (A), Gross Deductions (B), Net Pay (A)-(B)
  - Footer disclaimer

- **`setup_employee_fields.py`** — Adds Custom Fields for `pan_number`, `ifsc_code`, `pf_account_no` to the Employee doctype, then populates real employee data.

## How to Run

Inside the backend container:

```bash
docker cp scripts/payroll/generate_payslips.py hrms-backend-1:/tmp/
echo 'exec(open("/tmp/generate_payslips.py").read(), globals())' | \
  docker exec -i hrms-backend-1 bench --site hrms.cloudagents.uk console
```

## Indian Tax Rules Applied (FY 2025-26)

| Slab | Rate |
|---|---|
| Up to ₹4,00,000 | Nil |
| ₹4,00,001 – ₹8,00,000 | 5% |
| ₹8,00,001 – ₹12,00,000 | 10% |
| ₹12,00,001 – ₹16,00,000 | 15% |
| ₹16,00,001 – ₹20,00,000 | 20% |
| ₹20,00,001 – ₹24,00,000 | 25% |
| Above ₹24,00,000 | 30% |

- **Standard Deduction**: ₹75,000
- **Section 87A Rebate**: Zero tax up to ₹12L taxable income
- **Health & Education Cess**: 4% on tax
