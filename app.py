import streamlit as st
import json
from agents import extract_invoice, run_agent
from pypdf import PdfReader
st.set_page_config(page_title="Invoice Policy Agent", page_icon="📄", layout="wide")

st.title("📄 Invoice Policy Agent")
st.caption("An agentic AI workflow that reviews supplier invoices against company expense policy.")

with st.expander("ℹ️ How this works"):
    st.markdown("""
    1. **Paste an invoice** (or upload a `.txt` file).
    2. The agent **extracts** structured fields using GPT-4o-mini.
    3. The agent then **decides which policy checks to run** and calls them as tools.
    4. A final **exception report** is produced with a verdict and reasoning.

    Built as a small demonstration of the kind of agentic workflow described by
    PwC, Anthropic, and OpenAI — separating LLM reasoning from deterministic policy code.
    """)

# Input area
st.subheader("1. Provide an invoice")
uploaded_file = st.file_uploader("Upload an invoice (.txt or .pdf)", type=["txt", "pdf"])
pasted_text = st.text_area("...or paste the invoice text here:", height=200)

invoice_text = None
if uploaded_file is not None:
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        # PDF: extract text from each page using pypdf
        from pypdf import PdfReader
        reader = PdfReader(uploaded_file)
        pages = [page.extract_text() or "" for page in reader.pages]
        invoice_text = "\n".join(pages).strip()

        if not invoice_text:
            st.warning(
                "Could not extract any text from this PDF. "
                "It may be a scanned image rather than a text-based PDF. "
                "OCR support is not built in yet."
            )
            invoice_text = None

    else:
        # TXT: decode bytes, tolerating different encodings
        raw_bytes = uploaded_file.read()
        for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            try:
                invoice_text = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            invoice_text = raw_bytes.decode("utf-8", errors="replace")

elif pasted_text.strip():
    invoice_text = pasted_text

# Run button
if st.button("▶️ Run agent", type="primary", disabled=(invoice_text is None)):
    with st.spinner("Extracting invoice fields..."):
        extracted = extract_invoice(invoice_text)

    st.subheader("2. Extracted structured data")
    st.json(extracted)

    with st.spinner("Running compliance agent..."):
        report, tool_log = run_agent(extracted)

    st.subheader("3. Agent activity (tool calls)")
    for entry in tool_log:
        status = "✅" if entry["result"]["passed"] else "❌"
        with st.expander(f"{status} {entry['name']}"):
            st.write("**Arguments:**")
            st.json(entry["args"])
            st.write("**Result:**")
            st.json(entry["result"])

    st.subheader("4. Final compliance report")
    st.markdown(report)