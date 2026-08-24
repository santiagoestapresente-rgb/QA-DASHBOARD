"""Readable short forms for contact-reason names.

Several CR Lv4 values only differ in their last few words, so naive truncation
renders them as identical strings in narrow table cells and chart axes.
"""

from __future__ import annotations

CR_LABELS = {
    "order appears as completed but customer haven't receive it - market place":
        "Completed but not received — market place",
    "order appears as completed but customer haven't receive it - full service":
        "Completed but not received — full service",
    "order is active but customer already received it":
        "Active order, already received",
    "user disagrees with cancellation charge/debt":
        "Disagrees with cancellation charge",
    "user request order status or delay information":
        "Order status / delay information",
    "cannot place cash order (under antifraud review)":
        "Cash order blocked (antifraud)",
    "after sales user fraud (under anti fraud review)":
        "After-sales fraud review",
    "i don't agree with the delivery fee": "Disagree with delivery fee",
    "issues while paying to courier": "Paying the courier",
    "issues paying with cash": "Paying with cash",
    "delivery fee information": "Delivery fee",
    "modify order products": "Modify the order",
    "appealing refund result or amount": "Appealing the refund",
    "can't choose card as payment method (under antifraud review)":
        "Card blocked as payment (antifraud)",
    "user don't want the order anymore": "No longer wants the order",
    "driver or store request to cancel order": "Driver or store cancelled",
    "user placed order with wrong information": "Wrong information on the order",
}


def cr_label(value, max_len=None):
    raw = str(value).strip()
    label = CR_LABELS.get(raw.casefold(), raw)
    if max_len and len(label) > max_len:
        label = label[: max_len - 1].rstrip() + "…"
    return label
