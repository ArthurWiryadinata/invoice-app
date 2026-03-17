import frappe
from frappe.utils import flt


@frappe.whitelist(allow_guest=True)
def get_invoice(invoice_number):
    if not frappe.db.exists("Invoice", invoice_number):
        frappe.throw(f"Invoice {invoice_number} tidak ditemukan.")

    invoice = frappe.get_doc("Invoice", invoice_number)

    return {
        "invoice_number": invoice.name,
        "customer": invoice.customer,
        "tanggal_terbit": invoice.tanggal_terbit,
        "items": [
            {
                "nama_item": item.item_name,
                "kuantitas": item.quantity,
                "rate": item.rate,
                "harga": item.price,
            }
            for item in invoice.table_eesh
        ],
        "total_harga_item": invoice.total_harga_item,
        "presentase_pajak": invoice.presentase_pajak,
        "grand_total": invoice.grand_total,
        "payment_amount": invoice.payment_amount,
        "outstanding_amount": invoice.outstanding_amount,
        "payment_status": invoice.payment_status,
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def mark_as_paid():
    data = frappe.local.form_dict

    invoice_number = data.get("invoice_number")
    payment_amount = flt(data.get("payment_amount"))

    if not invoice_number:
        frappe.throw("invoice_number wajib diisi.")

    if payment_amount <= 0:
        frappe.throw("payment_amount harus lebih dari 0.")

    if not frappe.db.exists("Invoice", invoice_number):
        frappe.throw(f"Invoice {invoice_number} tidak ditemukan.")

    invoice = frappe.get_doc("Invoice", invoice_number)

    if invoice.payment_status == "Paid":
        frappe.throw("Invoice ini sudah lunas.")

    invoice.payment_amount = flt(invoice.payment_amount) + payment_amount

    frappe.set_user("Administrator")
    invoice.save()
    frappe.db.commit()

    return {
        "message": "Pembayaran berhasil dicatat.",
        "invoice_number": invoice.name,
        "payment_amount": invoice.payment_amount,
        "outstanding_amount": invoice.outstanding_amount,
        "payment_status": invoice.payment_status,
    }