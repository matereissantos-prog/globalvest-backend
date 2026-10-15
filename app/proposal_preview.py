"""Read-only preview of simulated portfolio adjustments."""


def preview(decision):
    return {"mode": "PAPER", "real_money": False, "execution_allowed": False, "broker_order_sent": False, "status": decision["status"], "suggestions": decision.get("orders", [])}
