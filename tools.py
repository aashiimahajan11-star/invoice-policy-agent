from policy import MAX_LINE_AMOUNT, PO_REQUIRED_OVER , APPROVED_VENDORS

def check_line_amount_limit(description:str,line_total:float)-> dict:
    if line_total> MAX_LINE_AMOUNT:
        return{
            "passed" : False,
            "rule": "max_line_amount",
            "reason" : f"line '{description} is eur{line_total:.2f},which exceeds the eur{MAX_LINE_AMOUNT:.2f}per line limit. Needs manager approval."
        }
    return{
            "passed" : True,
            "rule": "max_line_amount",
            "reason" : f"line '{description} is (eur{line_total:.2f}), is within eur{MAX_LINE_AMOUNT:.2f}per line limit. Needs no manager approval."
        }


def check_po_required(total_amount:float,po_reference)->dict:
    if total_amount > PO_REQUIRED_OVER and not po_reference:
        return {
            "passed": False,
            "rule": "po_required",
            "reason": f"Invoice total €{total_amount:.2f} exceeds €{PO_REQUIRED_OVER:.2f} but no PO reference was provided."
        }
    if total_amount > PO_REQUIRED_OVER and po_reference:
        return {
            "passed": True,
            "rule": "po_required",
            "reason": f"Invoice total €{total_amount:.2f} requires a PO; reference '{po_reference}' is present."
        }
    return {
        "passed": True,
        "rule": "po_required",
        "reason": f"Invoice total €{total_amount:.2f} is below the €{PO_REQUIRED_OVER:.2f} threshold; no PO required."
    }



def check_vendor_approved(vendor_name: str) -> dict:
    if vendor_name in APPROVED_VENDORS:
        return {
            "passed": True,
            "rule": "vendor_approved",
            "reason": f"Vendor '{vendor_name}' is on the approved supplier list."
        }
    return {
        "passed": False,
        "rule": "vendor_approved",
        "reason": f"Vendor '{vendor_name}' is NOT on the approved supplier list. Needs supplier onboarding review."
    }