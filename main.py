import os
import asyncio
import argparse
import json
import requests
import shutil
from dotenv import load_dotenv
from browser_use import Agent, ChatBrowserUse
from fpdf import FPDF
from PIL import Image


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dummy_data.json")

with open("dummy_data.json", encoding="utf-8") as f:
    dummy = json.load(f)


# test

def download_file(url: str, save_path: str):
    """Download file from URL and save locally"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False


# def create_test_files():
#     """Create test files in the current directory"""
#     test_image_path = os.path.join(BASE_DIR, "test_photo.jpg")
#     test_pdf_path = os.path.join(BASE_DIR, "test_passport.pdf")

#     # Create test image
#     try:

#         img = Image.new('RGB', (600, 600), color=(70, 130, 180))
#         img.save(test_image_path, "JPEG", quality=95)
#         print(f"Created test photo: {test_image_path}")
#     except ImportError:
#         # Fallback: download a simple image
#         try:
#             response = requests.get(
#                 "https://via.placeholder.com/600x600.jpg", timeout=10)
#             response.raise_for_status()
#             with open(test_image_path, 'wb') as f:
#                 f.write(response.content)
#             print(f"Downloaded placeholder photo: {test_image_path}")
#         except Exception as e:
#             print(f"Could not create test photo: {e}")
#             return None, None

#     # Create test PDF
#     try:

#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", size=12)
#         pdf.cell(200, 10, txt="TEST PASSPORT DOCUMENT", ln=1, align="C")
#         pdf.output(test_pdf_path)
#         print(f"Created test PDF: {test_pdf_path}")
#     except ImportError:
#         # Create minimal valid PDF
#         minimal_pdf = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF'
#         with open(test_pdf_path, 'wb') as f:
#             f.write(minimal_pdf)
#         print(f"Created minimal PDF: {test_pdf_path}")

#     # Verify files
#     if not os.path.exists(test_image_path) or os.path.getsize(test_image_path) == 0:
#         print(f"Photo invalid or empty")
#         return None, None

#     if not os.path.exists(test_pdf_path) or os.path.getsize(test_pdf_path) == 0:
#         print(f"PDF invalid or empty")
#         return None, None

#     print(f"Photo: {os.path.getsize(test_image_path)} bytes")
#     print(f"PDF: {os.path.getsize(test_pdf_path)} bytes")

#     return test_image_path, test_pdf_path
# test


def build_task(url: str, photo_path: str, pdf_path: str):
    # Extract data from JSON
    step1 = dummy["step_1_citizenship"]
    step2 = dummy["step_2_travel_information"]
    step4 = dummy["step_4_personal_information"]

    abs_photo_path = os.path.abspath(photo_path)
    abs_pdf_path = os.path.abspath(pdf_path)

    return f"""
    You are a deterministic browser automation agent with full DOM, vision, and reasoning capabilities. 
    You must follow all instructions EXACTLY, without guessing or improvisation.
    Your job is to fill and submit the primary form on: {url}
    
    =====================
    CRITICAL: FILE UPLOAD MECHANISM
    =====================
    You have access to the upload_file(index, path) tool for file uploads.

    UPLOADED FILES AVAILABLE:
    - Photo file path: {abs_photo_path}
    - Passport PDF path: {abs_pdf_path}

    HOW TO USE upload_file TOOL:
    1. Identify ALL <input type="file"> elements on the page
    2. Determine the INDEX of each file input (0 for first, 1 for second, etc.)
    3. Match each file input to its purpose (Photo vs Passport) by:
    - Checking the label text near it
    - Looking at accept attribute (accept="image/*" for photo, accept=".pdf" for passport)
    - Checking nearby text/labels
    4. Call upload_file(index, path) with:
    - index: the numeric index of the file input element (0, 1, 2, etc.)
    - path: the EXACT absolute path provided above

    EXAMPLE USAGE:
    - If photo input is the first file input (index 0): upload_file(0, "{abs_photo_path}")
    - If passport input is the second file input (index 1): upload_file(1, "{abs_pdf_path}")

    VERIFICATION AFTER UPLOAD:
    - After calling upload_file(), wait 2-3 seconds
    - Check if the filename appears on the page
    - Look for upload success indicators (✓, checkmark, "uploaded", progress bar completion)
    - If upload fails, try the next file input index

    STEP 4 UPLOAD SEQUENCE:
    1. First, identify ALL file input elements and their indices
    2. Determine which index is for photo (usually has accept="image/*" or label contains "photo")
    3. Determine which index is for passport PDF (usually has accept=".pdf" or label contains "passport")
    4. Call upload_file(photo_index, "{abs_photo_path}")
    5. Wait and verify photo upload success
    6. Call upload_file(pdf_index, "{abs_pdf_path}")
    7. Wait and verify PDF upload success
    8. Only proceed to Next button after BOTH uploads are confirmed

    IF UPLOAD FAILS:
    - Log which index you tried
    - Try the next available file input index
    - Check the page for error messages
    - Report: "Attempted upload_file(INDEX, PATH) - result: [success/failure]"

    =====================
    GENERAL BEHAVIOR RULES
    =====================
    - Work step-by-step, with careful reasoning at each UI element.
    - Infer labels and expected input types using multi-signal analysis.
    - Handle multi-step forms by repeating detection and filling on each step.
    - Take actions only when confident; log uncertainties.
    - Do not perform destructive operations.
    - Never click Next/Continue until all validation steps pass and all compulsory fields are filled.
    - Never assume success; always re-query the DOM.
    - If an element is missing, wait and retry instead of guessing.
    - Use strict selectors first; only use text-matching as last resort.
    - Scroll to elements before interacting.


    =====================
    1) PAGE READINESS
    =====================
    - Wait for DOM load and network idle.
    - If client-rendered, wait until form and fields stabilize.

    =====================
    2) FORM IDENTIFICATION
    =====================
    - Prefer the <form> with the largest number of usable inputs.
    - If no <form> exists, find the container acting like a form.

    =====================
    3) FIELD LABEL DETECTION
    =====================
    Determine human label using priority:
    1. <label for="...">
    2. aria-labelledby target
    3. aria-label / title
    4. clear placeholder
    5. visible text near or wrapping the field
    6. name/id pattern hints
    7. <legend> for grouped controls

    =====================
    4) VALUE RULES FOR INPUT TYPES
    =====================
    USE THE FOLLOWING SPECIFIC VALUES FROM OUR DATASET:

    STEP 1 VALUES:
    - Citizenship / Country → {step1['citizenship']}
    - Type of Travel Document / Passport → {step1['travel_document_type']}
    - Purpose of visit → {step1['purpose_of_visit']}
    - Insurance: {"checked" if step1['insurance'] else "unchecked"}

    STEP 2 VALUES:
    - Arrival Date → {step2['arrival_date']}

    STEP 4 VALUES:
    - First Name → {step4['first_name']}
    - Surname → {step4['surname']}
    - Date of Birth → {step4['date_of_birth']}
    - Sex → {step4['sex']}
    - Email Address → {step4['email']}
    - Travel Document No → {step4['travel_document_number']}
    - Expiration Date of Passport → {step4['expiry_date']}

    REPRESENTATIVE DATA (if section exists):
    - Relationship → {step4['representative']['relationship']}
    - Representative First Name → {step4['representative']['first_name']}
    - Representative Surname → {step4['representative']['surname']}
    - Representative Travel Document No → {step4['representative']['travel_document_number']}

    COMPANION DATA (if section exists):
    {chr(10).join([f"- person {i+1}: Relationship → {person['relationship']}, First Name → {person['first_name']}, Surname → {person['surname']}, Passport → {person['travel_document_number']}" for i, person in enumerate(step4['companion']['people'])])}

    =====================
    5) CAPTCHA HANDLING (OCR-BASED SOLUTION)
    =====================
    ONLY apply this logic if the CAPTCHA is a simple text-in-image code.

    Detect CAPTCHAs using:
    - Image immediately before/after an input labeled: "captcha", "verification code",
    "security code", "enter the text", "code below", etc.
    - Or if an image contains clear alphanumeric characters.

    If a CAPTCHA is detected:
    1. Extract the CAPTCHA image
    - Use vision to locate, crop, and isolate the CAPTCHA image.
    2. Perform OCR on the extracted image
    - Decode characters using OCR.
    3. OCR Uncertainty Handling
    - If OCR confidence is low:
            a) Enlarge the image (2×–3× zoom) and retry OCR.
            b) If characters overlap or are distorted, segment the image into individual character slices and OCR them separately.
            c) Compare first and second OCR attempts:
            - If a specific character differs, choose the visually sharper one.
            - Apply character-confusion heuristics:
                O ↔ 0
                I ↔ 1 ↔ l
                S ↔ 5
                B ↔ 8
                Z ↔ 2
            d) If a CAPTCHA refresh button is present:
            - Click refresh
            - Detect that a new image has appeared
            - Restart OCR with the updated image
            - Do NOT reuse previous OCR results, because the old image is invalid.
    4. Log:
    - Extracted text
    - Confidence or uncertainty
    - The selector of the associated field
    5. Retry Limit
    - Allow up to 3 total automated attempts (including OCR retries and refreshes).
    - If OCR still fails after 3 attempts:
    - Stop and ask the user:
            "OCR could not solve the CAPTCHA after 3 attempts. Please enter the CAPTCHA manually."

    =====================
    6) VALIDATION & ERROR HANDLING
    =====================
    - Fill required fields first.
    - Adjust values once if inline validation errors appear.
    - If server returns clear error messages, retry one time with correct values.

    =====================
    6.1) MULTI-STEP FORM NAVIGATION
    =====================
    If the form is multi-step:

    - Before pressing any "Next", "Continue", "Proceed", or arrow-navigation button:
        1. Check the current step for any required checkboxes such as:
        - "I have read…"
        - "I agree…"
        - "I accept…"
        - "I confirm that I have read and understood terms and conditions......."
        - Any checkbox marked as *required*
        2. If found, tick the checkbox before continuing.
        3. If multiple such checkboxes exist, tick all required ones.
        4. If the next-step button remains disabled, look for:
            - Hidden required fields
            - Collapsed consent sections
            - Scrolling required to unlock the button
            - Minor validation errors (fix once)

    - Only move to the next step once the button is enabled.

    On each new step:
    - Repeat full field detection and filling.

    =====================
    7) SUBMISSION LOGIC
    =====================
    - Identify submit button via:
        - <button type=submit>, <input type=submit>
        - Buttons with text: submit, send, register, continue, next, apply, save, confirm
    - Take a pre-submit screenshot.
    - Submit once and wait for:
        - Navigation completion, or
        - Visible success/confirmation message

    =====================
    9) FORM-SPECIFIC MULTI-STEP LOGIC (GEORGIA e-VISA WORKFLOW)
    =====================

    You are filling the official multi-step Georgia e-Visa application form.
    Follow these step-specific rules exactly:

    ----------------------------------------
    STEP 1 — Citizenship & Document Details
    ----------------------------------------
    1. Fill the following fields WITH EXACT
        Values:
        Citizenship: {step1['citizenship']}
        Travel Document Type: {step1['travel_document_type']}
        Purpose of Visit: {step1['purpose_of_visit']}
        Insurance: {"checked" if step1['insurance'] else "unchecked"}

        Selector priority for each field:
        1) select[name='<expected_name>']
        2) select[id='<expected_id>']
        3) input[name='<expected_name>']
        4) input[id='<expected_id>']
        5) ONLY IF ALL ABOVE FAIL: locate using nearest label text

        Procedure:
        1. Locate field using priority above.
        2. Scroll into view.
        3. For dropdowns: open → select EXACT visible text.
        4. For inputs: set value → trigger change event.
        5. Re-query DOM and confirm the filled value MATCHES the expected value.
        6. If mismatch → re-fill and re-verify until correct.

        Proceed only after ALL fields match expected DOM values.

    2. LOCATE THE CONFIRMATION CHECKBOX
        Checkbox specification:
        name="HasReadBorderCrossInfo"
        Label text contains:
            "I confirm that I have read and understood terms and conditions for entering territory Georgia."

        Selector priority (strict):
        1) input[name='HasReadBorderCrossInfo']
        2) input[id='HasReadBorderCrossInfo']
        3) label[for='HasReadBorderCrossInfo']
        4) ONLY IF ALL ABOVE FAIL: locate by label innerText containing required phrase

        If not found:
        - Wait 500ms and retry
        - Retry up to 10 times before failing

    3 — CHECKBOX CLICK LOGIC (REPEAT UNTIL SUCCESSFUL)
        Use this exact loop:

        Repeat until checkbox.checked == true:
            1. Scroll checkbox or its label into view.
            2. If label exists → CLICK LABEL (preferred)
            Else CLICK INPUT
            3. Wait 300ms
            4. Re-query the checkbox element (fresh DOM lookup)
            5. Read checkbox.checked value
            6. If false → retry

        Never rely on memory of prior DOM state.

    4. CAPTCHA HANDLING
        - Solve the CAPTCHA using OCR logic defined previously.
        After solving:
        - RE-VERIFY the confirmation checkbox because CAPTCHA may re-render the form.
        If checkbox becomes unchecked → repeat Step 3.  


    5. FINAL VALIDATION BEFORE PRESSING NEXT
        Before pressing Next:

        You MUST validate ALL of the following:

        1. All fields still contain exact provided values (re-query DOM).
        2. Checkbox input[name='HasReadBorderCrossInfo'] still exists.
        3. checkbox.checked == true (fresh DOM read).
        4. Visual tick still visible.
        5. No validation errors visible on the page.
        6. CAPTCHA solved (if applicable).

        If ANY condition fails:
            STOP immediately.
            Fix the issue.
            Re-run all validations.
        Proceed ONLY when 100% successful.

    6. PRESS NEXT BUTTON
        1. Locate the Next button.
        2. Scroll it into view.
        3. Ensure it is enabled and visible.
        4. Wait 500–1000ms (race condition protection).
        5. CLICK Next once.
        6. Wait for navigation to finish and confirm page transition.

        Never attempt navigation before validations.
        Never double-click.

    ----------------------------------------
    STEP 2 — Required Documents Dialog
    ----------------------------------------
    After clicking "Next" a dialog appears listing:
    - Passport-size photo requirement
    - Passport scanned PDF requirement

    Behavior:
    - Wait for the modal dialog.
    - Press "Continue".
    - Fill:
        - "Select the date of intended arrival to Georgia" → {step2['arrival_date']}
    - Press **Next** to proceed.

    ----------------------------------------
    STEP 3 — Mandatory Conditions & Declarations
    ----------------------------------------

    - Identify all visible checkbox controls inside the current step:
    - input[type="checkbox"], elements with role="checkbox", or elements exposing aria-checked.
    - For each checkbox found:
    1. Resolve a human label using priority: <label for="...">, aria-labelledby, aria-label/title, nearby visible text.
    2. Decide PURPOSE → mark as REQUIRED if ANY of:
        - has required attribute or aria-required
        - label/text contains keywords: "confirm", "I confirm", "I agree", "I accept", "declaration", "terms", "conditions", "mandatory", "I have read"
        - visibly part of a declarations/terms section or highlighted by validation
    3. Log entry: "Checkbox [N]: selector=[...], label=[...], reason=[required/optional]".
    - ACTION (REQUIRED checkboxes only):
    - Scroll into view and ensure element is interactable.
    - Click or set checked=true.
    - Wait 500–1000 ms.
    - Verify checked state via element.checked === true, aria-checked="true", or visible tick indicator.
    - If verification fails, retry up to 2 additional times (re-scroll, remove overlays, ensure enabled).
    - If still failing, stop and report: "Cannot check checkbox: selector=[...] — reason=[error details]".
    - After processing all checkboxes:
    - Confirm all REQUIRED ones are checked.
    - Only press Next when:
    - Every REQUIRED checkbox is verified checked, and
    - The Next button is enabled.
    - Final log summary: list each checkbox with selector, label, required/optional, and final state (checked/unchecked).

    ----------------------------------------
    STEP 4 — Applicant Information & Uploads
    ----------------------------------------
    Fill the following fields WITH EXACT VALUES:

        STEP 4A

            PRIMARY APPLICANT:
            - First Name → {step4['first_name']}
            - Surname → {step4['surname']}
            - Date of Birth → {step4['date_of_birth']}
            - Sex → {step4['sex']}
            - Email Address → {step4['email']}
            - Travel Document No → {step4['travel_document_number']}
            - Expiration Date of Passport → {step4['expiry_date']}

            FILE UPLOADS - CRITICAL SECTION:
            BEFORE filling representative or companion data, YOU MUST complete file uploads:

            1. Identify all <input type="file"> elements on the page
            2. Log their indices and purposes (photo vs passport)
            3. For PHOTO upload:
            - Find the file input for photo (check labels, accept attributes)
            - Call: upload_file(PHOTO_INPUT_INDEX, "{abs_photo_path}")
            - Wait 3 seconds
            - Verify upload success (look for filename or success indicator)
            4. For PASSPORT PDF upload:
            - Find the file input for passport
            - Call: upload_file(PDF_INPUT_INDEX, "{abs_pdf_path}")
            - Wait 3 seconds
            - Verify upload success

            LOG FORMAT FOR UPLOADS:
            "File Input Analysis:
            - Total file inputs found: [N]
            - Input 0: [purpose/label] - accept: [attribute value]
            - Input 1: [purpose/label] - accept: [attribute value]
            Attempting upload_file(0, {abs_photo_path})...
            Result: [success/failure with details]"

        ONLY AFTER BOTH UPLOADS ARE SUCCESSFUL:

        STEP 4B - REPRESENTATIVE AND COMPANION MODE(Checkbox + Dynamic Fields)

            Representative activation flag:
            representative_enabled = step4['representative']['enabled']

            Checkbox / Section description:
                "Application submitted by representative"
                
            Expected checkbox input name or identifiers:
                - input[name="ByRepresentative"] 
                - label contains: " Check the box if application is submitted by representative"

            Selector priority (strict):
            1) input[name='ByRepresentative']
            2) input[id='ByRepresentative']
            3) label[for='ByRepresentative']
            4) ONLY IF ALL ABOVE FAIL: nearest label whose text contains 
            "Application submitted by representative"

            If representative_enabled == True:

                # ENABLE THE CHECKBOX
                Repeat until checkbox.checked == true:
                    1. Scroll representative checkbox or label into view.
                    2. Click label (preferred) or input.
                    3. Wait 300ms.
                    4. Re-query fresh DOM.
                    5. If checked == false → retry.

                # VISUAL VERIFICATION
                Take screenshot of the checkbox region.
                Ensure visual tick exists.
                If mismatch → reclick until both DOM and UI agree.

                # WAIT FOR FIELDS TO APPEAR
                Wait until the representative fields render:
                    - Relationship field
                    - Representative First Name
                    - Representative Surname
                    - Representative Travel Document No

                # FILL REPRESENTATIVE FIELDS EXACTLY
                Fill:
                    Relationship → {step4['representative']['relationship']}
                    Representative First Name → {step4['representative']['first_name']}
                    Representative Surname → {step4['representative']['surname']}
                    Representative Travel Document No → {step4['representative']['travel_document_number']}

            Else (representative_enabled == False):

                If checkbox exists and is checked:
                    Uncheck it:
                        - Scroll into view
                        - Click label or input
                        - Wait 300ms
                        - Re-verify checkbox.checked == false

            ===========================================================

            Companion activation flag:
                companion_enabled = step4['companion']['enabled']
            Total companions expected:
                count = len(step4['companion']['people'])

            Checkbox / Section description:
                "Travelling With Companion"

            Expected checkbox input name or identifiers:
                - input[name="WithCompanion"]
                - label contains: "Travelling With Companion"

            Selector priority:
            1) input[name='WithCompanion']
            2) input[id='WithCompanion']
            3) label[for='WithCompanion']
            4) Label with text containing: " Travelling With Companion"

            If companion_enabled == True:

                # ENABLE THE CHECKBOX
                Repeat until checkbox.checked == true:
                    1. Scroll checkbox/label into view.
                    2. Click label (preferred).
                    3. Wait 300ms.
                    4. Re-query DOM state.
                    5. If not checked → retry.

                # VISUAL VERIFICATION
                Screenshot region → ensure tick visible.
                If mismatch → retry until consistent.

                # ALLOW FORM TO RENDER COMPANION FIELDS
                Wait for the companion fields section to appear.

                # HANDLE MULTIPLE COMPANIONS
                If count > 1:
                    - Find "Add Person" or "+ Add" button
                    - Click until the number of companion field groups equals count
                    - After each click: wait for DOM update

                # FILL EACH COMPANION EXACTLY
                For each person i in step['companion']['people']:
                    Person i+1:
                        Relationship → person['relationship']
                        First Name → person['first_name']
                        Surname → person['surname']
                        Travel Document No → person['travel_document_number']

                    After filling each field:
                        - Re-read value from DOM
                        - Refill if mismatch

            Else (companion_enabled == False):

                If the companion checkbox exists AND is currently checked:
                    Uncheck:
                        - Scroll into view
                        - Click label/input
                        - Wait 300ms
                        - Re-verify checkbox.checked == false

            ===========================================================
            IMPORTANT BEHAVIOR (SHARED):
            ===========================================================

            For BOTH representative and companion checkboxes:

            - The agent MUST NOT fill ANY representative or companion field  
            until:
                checkbox.checked == true AND UI visually shows a tick.

            - The agent MUST re-verify checkbox.checked before pressing NEXT.

            - The agent MUST NOT assume the fields exist; it must wait 
            for the fields to render after checkbox selection.

            - Every fill must be followed by a DOM re-read verification.

    - Press **Next** after validation passes.

    ----------------------------------------
    STEP 5 — Review & Verification
    ----------------------------------------
    This page lists all previously entered data.

    Actions:
    1. Scroll fully through the review page
    2. **CRITICAL - TAKE SCREENSHOT BEFORE CLICKING VERIFY:**
    - Use the screenshot tool to capture the current page state
    - This will automatically save the screenshot locally
    - Wait 2 seconds after taking the screenshot
    3. Press "Verify".
    4. Wait for navigation.

    SCREENSHOT COMMAND:
    Simply use the screenshot tool when you reach Step 5.

    Log: "Taking screenshot of Step 5 review page before clicking Verify button"

    ----------------------------------------
    FINAL STEP — Success Screen
    ----------------------------------------
    Expect message: "Your application has been successfully completed."
    - Save final URL
    - Save visible success message
    - Take screenshot
    - End task

    =====================
    EXECUTE NOW
    =====================
    Visit the page, identify the form, handle possible CAPTCHA, fill all fields using the provided dataset, 
    USE upload_file() TOOL FOR FILE UPLOADS IN STEP 4, USE write_file() TOOL WITH [screenshot] TAG IN STEP 5 BEFORE CLICKING VERIFY, submit, and produce the final report.
    """


async def main():
    parser = argparse.ArgumentParser(
        description="Automated form filler with CAPTCHA OCR")

    parser.add_argument("--url", "-u", help="URL of the form page")

    parser.add_argument("--data-file", "-d",
                        help="Optional JSON file with form data (default: dummy_data.json)")

    args = parser.parse_args()

    global dummy
    if args.data_file:
        with open(args.data_file, encoding="utf-8") as f:
            dummy = json.load(f)

    url = args.url or os.getenv("FORM_URL")

    if not url:
        url = input("Enter the URL of the page with the form: ").strip()

    print("Preparing files...")

    # Try to download from URLs first
    photo_path = os.path.join(BASE_DIR, "downloaded_photo.jpg")
    pdf_path = os.path.join(BASE_DIR, "downloaded_passport.pdf")

    photo_downloaded = False
    pdf_downloaded = False

    try:
        photo_url = dummy["step_4_personal_information"]["uploads"]["photo_path"]
        print("Downloading photo...")
        photo_downloaded = download_file(photo_url, photo_path)
    except Exception as e:
        print("Could not get photo URL: {e}")

    try:
        pdf_url = dummy["step_4_personal_information"]["uploads"]["passport_pdf_path"]
        print("Downloading PDF...")
        pdf_downloaded = download_file(pdf_url, pdf_path)
    except Exception as e:
        print("Could not get PDF URL: {e}")

    # Fallback to creating test files
    # if not photo_downloaded or not pdf_downloaded:
    #     print("Download failed, creating test files...")
    #     test_photo, test_pdf = create_test_files()

    #     if not photo_downloaded and test_photo:
    #         photo_path = test_photo
    #     if not pdf_downloaded and test_pdf:
    #         pdf_path = test_pdf

    # Final verification
    if not os.path.exists(photo_path):
        print(f"Photo file not found: {photo_path}")
        return
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return

    print(f"\nFiles ready:")
    print(
        f"  {os.path.abspath(photo_path)} ({os.path.getsize(photo_path)} bytes)")
    print(f"  {os.path.abspath(pdf_path)} ({os.path.getsize(pdf_path)} bytes)")
    print()

    task = build_task(url, photo_path, pdf_path)

    llm = ChatBrowserUse()
    agent = Agent(task=task, llm=llm, available_file_paths=[
                  photo_path, pdf_path])

    try:
        history = await agent.run()

        screenshot_paths = history.screenshot_paths()

        print("\nScreenshots saved locally:")
        for i, path in enumerate(screenshot_paths):
            print(f"   {i+1}. {path}")

        if screenshot_paths:
            step5_screenshot = screenshot_paths[-2]
            print(f"\nStep 5 screenshot saved at: {step5_screenshot}")

            final_screenshot_path = os.path.join(
                BASE_DIR, "step5_review_screenshot.png")
            shutil.copy2(step5_screenshot, final_screenshot_path)
            print(f"Copied to: {final_screenshot_path}")

    except Exception as e:
        print(f"[ERROR] Failed to execute agent: {e}")


if __name__ == "__main__":
    asyncio.run(main())
