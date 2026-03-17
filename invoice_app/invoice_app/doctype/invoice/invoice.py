import frappe
import frappe.model.naming
from frappe.model.document import Document
from frappe.utils import flt


class Invoice(Document):

    def autoname(self):
        self._set_naming_fields()
        series = f"INV/{self.customer_initials}/{self.issue_date_yymm}/.#####"
        self.name = frappe.model.naming.make_autoname(series)

    def before_save(self):
        self._set_customer_name()
        self._calculate_item_amounts()
        self._calculate_totals()
        self._update_payment_status()

    def _set_customer_name(self):
        if self.customer:
            self.customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")
            
    def _set_naming_fields(self):
        self.customer_initials = self._get_customer_initials()
        self.issue_date_yymm = self._get_issue_date_yymm()

    def _get_customer_initials(self):
        if not self.customer:
            return "XXX"
        customer_name = (
            frappe.db.get_value("Customer", self.customer, "customer_name")
            or self.customer
        )
        words = customer_name.strip().split()
        initials = "".join(word[0].upper() for word in words if word)
        return initials or "XXX"

    def _get_issue_date_yymm(self):
        if not self.tanggal_terbit:
            from frappe.utils import today
            self.tanggal_terbit = today()
        date_str = str(self.tanggal_terbit)
        year_2digit = date_str[2:4]
        month = date_str[5:7]
        return year_2digit + month

    def _calculate_item_amounts(self):
        for item in self.table_eesh:
            item.price = flt(item.quantity) * flt(item.rate)

    def _calculate_totals(self):
        self.total_harga_item = sum(flt(item.price) for item in self.table_eesh)
        tax_amount = self.total_harga_item * flt(self.presentase_pajak) / 100
        self.grand_total = self.total_harga_item + tax_amount
        self.outstanding_amount = flt(self.grand_total) - flt(self.payment_amount)

    def _update_payment_status(self):
        outstanding = flt(self.outstanding_amount)
        grand_total = flt(self.grand_total)
        if outstanding <= 0:
            self.payment_status = "Paid"
        elif outstanding < grand_total:
            self.payment_status = "Partially Paid"
        else:
            self.payment_status = "Unpaid"