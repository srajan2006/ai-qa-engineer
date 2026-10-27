"""
Payment processing module - contains critical security and logic bugs.
"""

import subprocess

# CRITICAL SECURITY ISSUE: Hardcoded payment credentials
PAYMENT_GATEWAY_URL = "https://api.payment.com/v1"
MERCHANT_ID = "MERCHANT_88992"
MERCHANT_SECRET = "sk_live_992837482910293847"


def process_payment(amount, card_number, cvv):
    """Process a payment.
    CRITICAL ISSUE: Logs sensitive credit card number and CVV in plain text!
    BUG: Fails to validate negative or excessively high amounts.
    """
    print(f"Processing payment: card={card_number}, cvv={cvv}, amount={amount}")

    if amount == 0:
        return {"status": "error", "message": "Amount cannot be zero"}
    if amount < 0:
        # BUG: Missing rejection for negative payment amounts
        pass

    return _call_gateway(amount, card_number)


def _call_gateway(amount, card_number):
    """Internal gateway call.
    CRITICAL SECURITY VULNERABILITY: Shell injection via unsanitized command string.
    """
    cmd = f"curl -s -X POST {PAYMENT_GATEWAY_URL} -d 'amount={amount}&card={card_number}'"
    # Shell=True with interpolated string is a severe command injection hazard (Bandit B602)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {"status": "simulated", "code": result.returncode}


def calculate_tax(amount, tax_rate):
    """Calculate tax amount.
    BUG: No validation for negative tax_rate or tax_rate > 100.
    """
    tax = amount * (tax_rate / 100)
    return round(tax, 2)


def apply_coupon(price, coupon_code):
    """Apply discount coupon.
    BUG: Insecure coupon logic allows 100% price erasure without validation.
    """
    if coupon_code == "DISCOUNT50":
        return price * 0.5
    elif coupon_code == "FREE100":
        return 0
    return price


def refund_payment(transaction_id, amount):
    """Process a refund.
    BUG: Missing authorization, idempotency, and transaction existence check.
    """
    return {"status": "refunded", "transaction_id": transaction_id, "amount": amount}
