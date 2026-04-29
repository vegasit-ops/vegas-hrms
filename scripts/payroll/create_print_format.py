"""
Indutech-style payslip format for VEGAS IT GLOBAL
"""
import frappe


def run():
    if frappe.db.exists("Print Format", "VEGAS Payslip"):
        frappe.delete_doc("Print Format", "VEGAS Payslip", force=True)
        frappe.db.commit()

    html = """{%- set emp = frappe.get_doc("Employee", doc.employee) -%}
{%- set ns = namespace(other_deductions=0) -%}
{%- for d in doc.deductions -%}
  {%- if d.salary_component != "Professional Tax" -%}
    {%- set ns.other_deductions = ns.other_deductions + (d.amount or 0) -%}
  {%- endif -%}
{%- endfor -%}
<style>
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Times New Roman', 'Liberation Serif', serif; color: #000; font-size: 11pt; line-height: 1.3; }
table { width: 100%; border-collapse: collapse; }
.payslip { border: 2px solid #000; }
.payslip td, .payslip th { border: 1px solid #000; padding: 6px 10px; vertical-align: middle; font-size: 10pt; }

/* Top header with logo + company info */
.header-row td { padding: 12px; }
.logo-cell { width: 30%; text-align: center; vertical-align: middle; padding: 12px; }
.logo-box {
  display: inline-block;
  width: 80px; height: 80px;
  background: linear-gradient(135deg, #8b5cf6, #ec4899);
  color: white;
  font-size: 28px; font-weight: 800;
  line-height: 80px;
  border-radius: 50%;
  text-align: center;
  vertical-align: middle;
  font-family: Arial, sans-serif;
}
.company-cell { text-align: right; padding: 12px 16px; }
.company-name { font-size: 14pt; font-weight: 700; margin-bottom: 4px; }
.company-detail { font-size: 9.5pt; line-height: 1.5; }

/* Centered Payslip title */
.title-row td { background: #DCE6F1; text-align: center; font-weight: 700; font-size: 12pt; padding: 8px; }

/* Section header */
.section-header td { background: #DCE6F1; font-weight: 700; font-size: 10pt; text-align: center; padding: 6px; }

/* Employee info rows */
.info-row td { padding: 6px 10px; }
.label-cell { width: 18%; font-weight: normal; }
.value-cell { width: 32%; font-weight: 700; }

/* Earning / Deduction tables */
.amount-header td { background: #DCE6F1; font-weight: 700; padding: 6px 10px; }
.amount-row td { padding: 6px 10px; }
.amount-cell { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
.totals-row td { font-weight: 700; background: #f4f4f4; }

/* Net pay */
.netpay-row td { font-weight: 700; font-size: 11pt; padding: 8px 10px; }

/* Footer */
.footer-row td { background: #f0f0f0; text-align: center; padding: 8px; font-size: 9.5pt; font-style: italic; }

.no-border { border: none !important; }
</style>

<table class="payslip">
  <!-- Top header: Logo + Company name -->
  <tr class="header-row">
    <td class="logo-cell" style="width:30%;">
      <div class="logo-box">V</div>
    </td>
    <td class="company-cell" colspan="3" style="width:70%;">
      <div class="company-name">VEGAS IT GLOBAL</div>
      <div class="company-detail">
        Cloudagents Project Office, India<br>
        Phone: +91 7416988166 | E-mail: hr@vegasitglobal.com | www.cloudagents.uk
      </div>
    </td>
  </tr>

  <!-- Title -->
  <tr class="title-row">
    <td colspan="4">Payslip for the month of {{ frappe.utils.formatdate(doc.start_date, "MMMM yyyy") }}</td>
  </tr>

  <!-- Section: Employee Information -->
  <tr class="section-header">
    <td colspan="4">EMPLOYEE INFORMATION</td>
  </tr>

  <!-- Employee details: 2-column layout -->
  <tr class="info-row">
    <td class="label-cell">EMP NAME</td>
    <td class="value-cell">{{ emp.employee_name }}</td>
    <td class="label-cell">PAN NO</td>
    <td class="value-cell">{{ emp.get('pan_number') or '—' }}</td>
  </tr>
  <tr class="info-row">
    <td class="label-cell">BANK NAME</td>
    <td class="value-cell">{{ emp.bank_name or '—' }}</td>
    <td class="label-cell">ACCOUNT NO</td>
    <td class="value-cell">{{ emp.bank_ac_no or '—' }}</td>
  </tr>
  <tr class="info-row">
    <td class="label-cell">EMP ID</td>
    <td class="value-cell">{{ emp.name }}</td>
    <td class="label-cell">PROCESSED DAYS</td>
    <td class="value-cell">{{ "%.0f" % (doc.total_working_days or 0) }}</td>
  </tr>
  <tr class="info-row">
    <td class="label-cell">DESIGNATION</td>
    <td class="value-cell">{{ emp.designation or '—' }}</td>
    <td class="label-cell">WORKED DAYS</td>
    <td class="value-cell">{{ "%.0f" % (doc.payment_days or 0) }}</td>
  </tr>
  <tr class="info-row">
    <td class="label-cell">DEPARTMENT</td>
    <td class="value-cell">{{ (doc.department or emp.department or '—') | replace(' - VIG', '') }}</td>
    <td class="label-cell">GENDER</td>
    <td class="value-cell">{{ emp.gender or '—' }}</td>
  </tr>
  <tr class="info-row">
    <td class="label-cell">DOJ</td>
    <td class="value-cell">{{ frappe.utils.formatdate(emp.date_of_joining, "dd MMM yyyy") }}</td>
    <td class="label-cell">PF ACCOUNT</td>
    <td class="value-cell">{{ emp.get('pf_account_no') or '—' }}</td>
  </tr>

  <!-- Earnings + Deductions table -->
  <tr class="amount-header">
    <td>EARNING</td>
    <td class="amount-cell">AMOUNT (RS)</td>
    <td>DEDUCTION</td>
    <td class="amount-cell">AMOUNT (RS)</td>
  </tr>

  {%- set num_earnings = doc.earnings|length -%}
  {%- set num_deductions = doc.deductions|length -%}
  {%- set max_rows = (num_earnings if num_earnings > num_deductions else num_deductions) -%}

  {%- for i in range(max_rows) %}
  <tr class="amount-row">
    {% if i < num_earnings %}
      {% set e = doc.earnings[i] %}
      <td>{{ e.salary_component | upper }}</td>
      <td class="amount-cell">{{ "{:,.2f}".format(e.amount or 0) }}</td>
    {% else %}
      <td>&nbsp;</td>
      <td>&nbsp;</td>
    {% endif %}
    {% if i < num_deductions %}
      {% set d = doc.deductions[i] %}
      <td>{{ d.salary_component | upper }}</td>
      <td class="amount-cell">{{ "{:,.2f}".format(d.amount or 0) }}</td>
    {% else %}
      <td>&nbsp;</td>
      <td>&nbsp;</td>
    {% endif %}
  </tr>
  {%- endfor %}

  <!-- Totals row -->
  <tr class="totals-row">
    <td>GROSS PAY (A)</td>
    <td class="amount-cell">{{ "{:,.2f}".format(doc.gross_pay) }}</td>
    <td>GROSS DEDUCTIONS (B)</td>
    <td class="amount-cell">{{ "{:,.2f}".format(doc.total_deduction) }}</td>
  </tr>

  <!-- Net Pay -->
  <tr class="netpay-row">
    <td>NET PAY (A)-(B)</td>
    <td class="amount-cell">{{ "{:,.2f}".format(doc.net_pay) }}</td>
    <td colspan="2" style="text-align:left;font-weight:normal;font-size:9pt;">
      <i>In words: {{ doc.total_in_words or '—' }}</i>
    </td>
  </tr>

  <!-- Footer -->
  <tr class="footer-row">
    <td colspan="4">This is a computer generated Payslip. No signature required.</td>
  </tr>
</table>
"""

    pf = frappe.get_doc({
        "doctype": "Print Format",
        "name": "VEGAS Payslip",
        "doc_type": "Salary Slip",
        "module": "HR",
        "standard": "No",
        "custom_format": 1,
        "print_format_type": "Jinja",
        "html": html,
        "show_section_headings": 0,
        "default_print_language": "en",
        "margin_top": 10,
        "margin_bottom": 10,
        "margin_left": 10,
        "margin_right": 10,
        "absolute_value": 0,
        "disabled": 0
    })
    pf.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"✓ Print Format updated: {pf.name}")
    frappe.clear_cache()


run()
