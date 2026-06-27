from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

client = OpenAI()

with open("sample_invoices/invoice_002.txt","r") as f:
    invoice_text = f.read()


response = client.chat.completions.create(
    model = "gpt-4o-mini",
    response_format = {"type":"json_object"},
    messages =[
        {
            "role" : "system",
            "content": "You extract structured data from invoices. Return JSON with these fields: vendor_name, vendor_vat, invoice_number, invoice_date, due_date, po_reference, currency, subtotal, vat_amount, total_amount, line_items (a list of objects each with description, quantity, unit_price, line_total). Use null for any field not present. Amounts should be numbers, not strings."
        },
        {
            "role" : "system",
            "content": invoice_text


        }


    ]
)

extracted = json.loads(response.choices[0].message.content)
print(json.dumps(extracted, indent = 2))