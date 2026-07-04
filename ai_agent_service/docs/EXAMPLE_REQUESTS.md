# Example Requests and Responses

All examples use:

```text
POST /api/v1/agent/process-message/
X-AI-Service-Key: <AI_SERVICE_API_KEY>
```

## 1) Booking Request

### Request

```json
{
  "business_id": "business_123",
  "channel": "whatsapp",
  "customer": {
    "customer_id": "cust_1",
    "name": "John",
    "phone": "+8801712345678",
    "language": "en"
  },
  "message": {
    "message_id": "msg_1",
    "text": "I want to book an appointment tomorrow.",
    "message_type": "text",
    "timestamp": "2026-07-02T10:00:00Z"
  },
  "business_context": {
    "business_name": "Example Clinic",
    "business_type": "clinic",
    "supported_languages": ["en", "bn"],
    "default_language": "en",
    "services": [
      {
        "service_id": "service_1",
        "name": "General Consultation",
        "price": 1000,
        "currency": "BDT",
        "booking_required": true
      }
    ],
    "staff_members": [],
    "working_hours": [],
    "booking": {
      "enabled": true
    },
    "faqs": [],
    "policies": [],
    "lead_qualification": {
      "enabled": true
    },
    "handoff_rules": [],
    "agent_rules": []
  },
  "conversation_history": [],
  "available_actions": ["send_message", "check_availability", "handoff_to_human"],
  "backend_action_results": []
}
```

### Response (sample)

```json
{
  "request_id": "uuid",
  "business_id": "business_123",
  "reply_message": "I can help with that. Which time works for you tomorrow?",
  "reply_language": "en",
  "intent": {
    "name": "booking_request",
    "confidence": 0.95
  },
  "conversation_state": {
    "status": "active",
    "current_flow": "booking",
    "next_required_information": ["preferred_time"]
  },
  "extracted_data": {
    "customer": {
      "name": null,
      "phone": null,
      "email": null,
      "language": "en"
    },
    "lead": {
      "service_interest": "General Consultation",
      "budget": null,
      "preferred_date": "2026-07-03",
      "preferred_time": null,
      "notes": "Customer wants tomorrow appointment."
    }
  },
  "actions": [
    {
      "action_id": "uuid",
      "type": "check_availability",
      "priority": "normal",
      "data": {
        "service_id": "service_1",
        "requested_date": "2026-07-03"
      },
      "requires_backend_result": true
    }
  ],
  "handoff": {
    "required": false,
    "department": null,
    "priority": null,
    "reason": null
  },
  "safety": {
    "flagged": false,
    "category": null,
    "instructions": null
  },
  "internal_summary": "Booking flow started."
}
```

## 2) Booking Availability Follow-Up

### Request snippet

```json
{
  "backend_action_results": [
    {
      "action_id": "uuid",
      "type": "check_availability",
      "success": true,
      "data": {
        "available_slots": [
          {
            "start": "2026-07-03T10:00:00+06:00",
            "end": "2026-07-03T10:30:00+06:00"
          },
          {
            "start": "2026-07-03T14:00:00+06:00",
            "end": "2026-07-03T14:30:00+06:00"
          }
        ]
      },
      "error": null
    }
  ]
}
```

### Response snippet

```json
{
  "reply_message": "Tomorrow we have 10:00 AM or 2:00 PM. Which time do you prefer?",
  "intent": {
    "name": "availability_request",
    "confidence": 0.92
  }
}
```

## 3) FAQ Request

Customer asks: `"Do you accept walk-ins?"`

Expected intent: `faq` and direct concise reply based on `business_context.faqs`.

## 4) Lead Qualification

Customer asks for service and price but leaves missing lead fields.

Expected behavior:

- intent `lead_qualification`
- `next_required_information` includes missing required fields
- action may include `create_lead` or `update_lead`

## 5) Customer Complaint

Customer says: `"I am unhappy, nobody responded to my booking."`

Expected behavior:

- intent `complaint`
- human handoff considered if repeated frustration
- action can include `create_support_ticket`

## 6) Human Handoff

Customer says: `"I want to speak to a human."`

Expected behavior:

```json
{
  "intent": {
    "name": "human_handoff",
    "confidence": 0.98
  },
  "handoff": {
    "required": true,
    "department": "support",
    "priority": "normal",
    "reason": "Customer requested human support."
  }
}
```

## 7) Order Tracking

Customer asks: `"Where is my order?"`

Expected behavior:

- intent `order_tracking`
- action `track_order` if available
- if action unavailable, handoff recommendation

## 8) Payment Link Request

Customer asks: `"Send me the payment link."`

Expected behavior:

- intent `payment_request`
- action `request_payment_link`
- reply must not confirm payment completion until backend result arrives
