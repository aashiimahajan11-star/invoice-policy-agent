from dotenv import load_dotenv

from openai import OpenAI
import json

from tools import (
    check_line_amount_limit,
    check_po_required,
    check_vendor_approved,
)

load_dotenv()
client = OpenAI()


# Tell GPT what tools exist, what they do, and what arguments they take.
# This is the agent's "menu" — GPT picks from this list.

TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_line_amount_limit",
            "description": "Check if a single line item on an invoice exceeds the per-line approval limit. Call this once for EACH line item on the invoice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The text description of the line item, e.g. 'Office chairs (ergonomic)'."
                    },
                    "line_total": {
                        "type": "number",
                        "description": "The line total in the invoice currency."
                    }
                },
                "required": ["description", "line_total"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_po_required",
            "description": "Check if a PO reference is required based on invoice total, and if so whether one is present.",
            "parameters": {
                "type": "object",
                "properties": {
                    "total_amount": {
                        "type": "number",
                        "description": "The total invoice amount."
                    },
                    "po_reference": {
                        "type": ["string", "null"],
                        "description": "The PO reference from the invoice, or null if not present."
                    }
                },
                "required": ["total_amount", "po_reference"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_vendor_approved",
            "description": "Check if the vendor is on the company's approved supplier list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {
                        "type": "string",
                        "description": "The exact name of the vendor as it appears on the invoice."
                    }
                },
                "required": ["vendor_name"]
            }
        }
    }
]

# A simple lookup so we can call the right Python function by name.
TOOL_FUNCTIONS = {
    "check_line_amount_limit": check_line_amount_limit,
    "check_po_required": check_po_required,
    "check_vendor_approved": check_vendor_approved,
}

def extract_invoice(invoice_text: str) -> dict:
    """Stage 1: turn raw invoice text into structured JSON. (Same as Phase 3.)"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You extract structured data from invoices. Return JSON with: vendor_name, vendor_vat, invoice_number, invoice_date, due_date, po_reference, currency, subtotal, vat_amount, total_amount, line_items (list of {description, quantity, unit_price, line_total}). Use null for missing fields. Amounts as numbers."
            },
            {"role": "user", "content": invoice_text}
        ]
    )
    return json.loads(response.choices[0].message.content)


def run_agent(invoice_json: dict) -> str:
    """Stage 2: the agent loop. GPT decides which tools to call until it has enough info to give a verdict."""

    system_prompt = (
        "You are an AI compliance agent reviewing supplier invoices against company expense policy. "
        "You have tools to check individual line items, PO requirements, and vendor approval status. "
        "Decide which checks are needed for THIS invoice, call each tool with the right arguments, "
        "wait for results, and then produce a final structured exception report. "
        "The report should clearly state: overall verdict (APPROVE / FLAG_FOR_REVIEW / REJECT), "
        "and a bullet list of each check performed with pass/fail and reasoning."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Review this invoice:\n\n{json.dumps(invoice_json, indent=2)}"}
    ]

    # The loop: keep calling the model until it stops asking for tools.
    tool_log = []
    max_steps = 10
    for step in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_SCHEMA,
        )
        msg = response.choices[0].message

        # If the model wants to call tools, run them and feed results back.
        if msg.tool_calls:
            messages.append(msg)  # the model's tool-call request
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result = TOOL_FUNCTIONS[name](**args)
                tool_log.append({
                    "name": name,
                    "args": args,
                    "result": result,
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })
            continue  # back to the top: let GPT see results and decide what's next

        # No tool calls = model has finished and produced the final report.
        # No tool calls = model has finished and produced the final report.
        return msg.content, tool_log

    return "Agent exceeded max steps without finishing.", tool_log


# Entry point: run extraction + agent on a sample invoice.
if __name__ == "__main__":
    with open("sample_invoices/invoice_002.txt", "r") as f:
        invoice_text = f.read()

    print("📄 Extracting invoice...\n")
    extracted = extract_invoice(invoice_text)
    print(json.dumps(extracted, indent=2))

    print("\n🤖 Running compliance agent...\n")
    report, tool_log = run_agent(extracted)
    for entry in tool_log:
        print(f"  🔧 {entry['name']}({entry['args']}) → passed={entry['result']['passed']}")
    print("\n📋 Final report:\n")
    print(report)

