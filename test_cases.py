"""
test_cases.py
=============
Benchmark test cases for Code-Mixed Customer Support Triage Assistant.
Contains 35 realistic customer support messages across:
- Tanglish (Tamil + English)
- Hinglish (Hindi + English)
- English

Each test case specifies:
- id: int
- message: str
- language: str ("Tanglish", "Hinglish", "English")
- expected_intent: str
- expected_urgency: str ("high", "medium", "low")
- expected_escalate: bool (True, False)
- notes: str
"""

TEST_CASES = [
    # -------------------------------------------------------------------------
    # Hinglish Test Cases (Hindi + English)
    # -------------------------------------------------------------------------
    {
        "id": 1,
        "message": "mera paisa do baar cut gaya",
        "language": "Hinglish",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Classic duplicate debit complaint requiring finance escalation."
    },
    {
        "id": 2,
        "message": "order mein problem hai, help me",
        "language": "Hinglish",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "General order issue inquiry requiring agent follow-up."
    },
    {
        "id": 3,
        "message": "My login nahi ho raha, please help",
        "language": "Hinglish",
        "expected_intent": "Account Access",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Authentication trouble with app login."
    },
    {
        "id": 4,
        "message": "bhai delivery kab tak aayegi? 4 din ho gaye status pending hai",
        "language": "Hinglish",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Query regarding delayed courier shipment."
    },
    {
        "id": 5,
        "message": "packet khola toh glass bottle toota hua nikla, turant refund chahiye",
        "language": "Hinglish",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Broken item received, urgent replacement/refund needed."
    },
    {
        "id": 6,
        "message": "paise account se deduct ho gaye par order id create nahi hua",
        "language": "Hinglish",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Payment deducted without order generation; critical finance escalation."
    },
    {
        "id": 7,
        "message": "kripya mera order cancel kardo, mujhe urgent trip pe jana hai",
        "language": "Hinglish",
        "expected_intent": "Order Cancellation",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Standard customer cancellation before dispatch."
    },
    {
        "id": 8,
        "message": "phone pe refund status updated nahi dikha raha, 7 days passed",
        "language": "Hinglish",
        "expected_intent": "Refund Request",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Escalated refund follow-up exceeding typical SLA."
    },
    {
        "id": 9,
        "message": "OTP receive nahi ho raha mobile par, register nahi kar pa raha",
        "language": "Hinglish",
        "expected_intent": "Account Access",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Registration roadblock due to telecom OTP delay."
    },
    {
        "id": 10,
        "message": "maine blue color order kiya tha lekin red color bhej diya",
        "language": "Hinglish",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Incorrect variant received, replacement needed."
    },
    {
        "id": 11,
        "message": "delivery agent badtameezi kar raha tha aur package nahi diya",
        "language": "Hinglish",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Courier partner behavioral issue and non-delivery."
    },
    {
        "id": 12,
        "message": "kya ye product cod par available hai?",
        "language": "Hinglish",
        "expected_intent": "General Inquiry",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Pre-purchase payment mode question."
    },
    {
        "id": 13,
        "message": "card se paise cut gaye lekin transaction failed aaya",
        "language": "Hinglish",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Failed checkout debit requiring reconciliation."
    },
    {
        "id": 14,
        "message": "mujhe bill download karna hai, how to download invoice?",
        "language": "Hinglish",
        "expected_intent": "General Inquiry",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Self-service invoice request."
    },

    # -------------------------------------------------------------------------
    # Tanglish Test Cases (Tamil + English)
    # -------------------------------------------------------------------------
    {
        "id": 15,
        "message": "order vandhuchu but box damaged, refund venum",
        "language": "Tanglish",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Box damaged on arrival, requesting prompt refund."
    },
    {
        "id": 16,
        "message": "delivery romba late aagudhu",
        "language": "Tanglish",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Complaint about sluggish delivery."
    },
    {
        "id": 17,
        "message": "account la irundhu money debited aana order book aagala",
        "language": "Tanglish",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Money debited from account but order not booked."
    },
    {
        "id": 18,
        "message": "wrong size shirt anupiteenga, exchange panna mudiyuma?",
        "language": "Tanglish",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Size mismatch query for apparel exchange."
    },
    {
        "id": 19,
        "message": "parcel open panna item broken condition la irukku, urgent help please",
        "language": "Tanglish",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Broken item delivered, urgent supervisor escalation."
    },
    {
        "id": 20,
        "message": "indha order cancel panna mudiyuma, mistake ah place panniten",
        "language": "Tanglish",
        "expected_intent": "Order Cancellation",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Accidental order placement, requesting cancellation."
    },
    {
        "id": 21,
        "message": "OTP varave illa, app login panna mudila",
        "language": "Tanglish",
        "expected_intent": "Account Access",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "OTP failed to arrive, preventing app login."
    },
    {
        "id": 22,
        "message": "payment duplicate deduct aayiduchu, bank statement kooda send panren",
        "language": "Tanglish",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Double debit with customer ready to furnish statement."
    },
    {
        "id": 23,
        "message": "product romba super, but invoice download aagala",
        "language": "Tanglish",
        "expected_intent": "General Inquiry",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Positive feedback with invoice download assistance needed."
    },
    {
        "id": 24,
        "message": "delivery partner call edukkala, location therila nu solraru",
        "language": "Tanglish",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Delivery driver address navigation issue."
    },
    {
        "id": 25,
        "message": "courier packed sealed ah illa, item missing ullara",
        "language": "Tanglish",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Tampered seal and missing item in package."
    },
    {
        "id": 26,
        "message": "refund innum credit aagala, 10 days aachu",
        "language": "Tanglish",
        "expected_intent": "Refund Request",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Refund overdue past standard timeline."
    },

    # -------------------------------------------------------------------------
    # English Test Cases
    # -------------------------------------------------------------------------
    {
        "id": 27,
        "message": "I was charged twice on my credit card for a single transaction",
        "language": "English",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Standard English duplicate credit card charge."
    },
    {
        "id": 28,
        "message": "My parcel arrived severely damaged and items are leaking",
        "language": "English",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Damaged packaging with leaking liquids."
    },
    {
        "id": 29,
        "message": "Where is my order? The tracking has not updated for 5 days",
        "language": "English",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Stagnant tracking information for nearly a week."
    },
    {
        "id": 30,
        "message": "Please cancel order #88491 as I ordered the incorrect model",
        "language": "English",
        "expected_intent": "Order Cancellation",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Explicit order cancellation request with order number."
    },
    {
        "id": 31,
        "message": "I am unable to reset my password, error says user not found",
        "language": "English",
        "expected_intent": "Account Access",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "User identity or credential reset failure."
    },
    {
        "id": 32,
        "message": "I want a full refund for order #12344, the product is defective",
        "language": "English",
        "expected_intent": "Refund Request",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Defective item return and full refund request."
    },
    {
        "id": 33,
        "message": "Can you tell me the warranty period for this electronic device?",
        "language": "English",
        "expected_intent": "General Inquiry",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Product warranty specifications inquiry."
    },
    {
        "id": 34,
        "message": "Unauthorized debit of Rs 4500 from my linked card without OTP",
        "language": "English",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Potential fraud/unauthorized payment; critical escalation."
    },
    {
        "id": 35,
        "message": "Delivery was promised yesterday but status still shows preparing",
        "language": "English",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Missed delivery SLA with order still in preparation."
    },

    # -------------------------------------------------------------------------
    # Telugu + English Test Cases (Tenglish / Teluglish)
    # -------------------------------------------------------------------------
    {
        "id": 36,
        "message": "tracking link pani cheyyatledu, order ekkada undi?",
        "language": "Telugu + English",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Order tracking issue with non-functional link."
    },
    {
        "id": 37,
        "message": "order cancel cheyyali, wrongly ordered wrong item",
        "language": "Telugu + English",
        "expected_intent": "Order Cancellation",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Standard customer cancellation before shipping."
    },
    {
        "id": 38,
        "message": "refund kavali, amount account lo padaledu",
        "language": "Telugu + English",
        "expected_intent": "Refund Request",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Refund amount missing from bank account; requires finance audit."
    },
    {
        "id": 39,
        "message": "payment rendu saarlu cut ayyindi",
        "language": "Telugu + English",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Duplicate payment deduction requiring escalation."
    },
    {
        "id": 40,
        "message": "failed payment aindi kani money cut ayindi account lo",
        "language": "Telugu + English",
        "expected_intent": "Payment Issue",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Failed checkout transaction with money deducted."
    },
    {
        "id": 41,
        "message": "naa order inka delivery avvaledu, chala late avutundi",
        "language": "Telugu + English",
        "expected_intent": "Delivery Delay",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Late delivery status inquiry."
    },
    {
        "id": 42,
        "message": "product damage ayindi, box open cheste glass broken undi",
        "language": "Telugu + English",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Damaged item with shattered glass on delivery."
    },
    {
        "id": 43,
        "message": "wrong product vachindi, return cheyyali",
        "language": "Telugu + English",
        "expected_intent": "Damaged / Wrong Item",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Incorrect variant received, requesting replacement/return."
    },
    {
        "id": 44,
        "message": "naa account login avvatledu, OTP raaledu",
        "language": "Telugu + English",
        "expected_intent": "Account Access",
        "expected_urgency": "medium",
        "expected_escalate": False,
        "notes": "Login trouble due to missing authentication OTP."
    },
    {
        "id": 45,
        "message": "customer care tho matladali, konchem problem undi",
        "language": "Telugu + English",
        "expected_intent": "General Inquiry",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Ambiguous support request asking to talk to care."
    },
    {
        "id": 46,
        "message": "naku money refund cheyyandi, 10 days nunchi pending",
        "language": "Telugu + English",
        "expected_intent": "Refund Request",
        "expected_urgency": "high",
        "expected_escalate": True,
        "notes": "Long overdue refund exceeding 10 days SLA."
    },
    {
        "id": 47,
        "message": "urgent ga cancel cheyyali order, please help",
        "language": "Telugu + English",
        "expected_intent": "Order Cancellation",
        "expected_urgency": "low",
        "expected_escalate": False,
        "notes": "Immediate cancellation request prior to processing."
    }
]


def get_test_cases():
    """Return a deep copy or reference to all test cases."""
    return TEST_CASES
