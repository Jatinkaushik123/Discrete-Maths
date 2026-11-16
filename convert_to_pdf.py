"""
convert_to_pdf.py
=================
Complete, cross-platform Python automation script to convert 
'Discrete_Mathematics_Project_Report_Group_2.docx' into 
'Discrete_Mathematics_Project_Report_Group_2.pdf' while preserving 
100% of formatting, typography, equations, tables, and layout.

Methods supported:
1. Primary: docx2pdf (Native MS Word engine via COM automation on Windows / AppleScript on macOS)
2. Secondary: LibreOffice / soffice CLI (Cross-platform headless converter for Linux/macOS/Windows)
3. Tertiary: Direct PowerShell Word COM automation fallback (Windows native)
"""

import os
import sys
import shutil
import subprocess

def convert_word_to_pdf(docx_path: str, pdf_path: str) -> str:
    """
    Converts a .docx document to .pdf using the most reliable available engine.
    """
    abs_docx = os.path.abspath(docx_path)
    abs_pdf = os.path.abspath(pdf_path)

    if not os.path.exists(abs_docx):
        raise FileNotFoundError(f"Source Word file not found at: {abs_docx}")

    print(f"[*] Input Word Document : {abs_docx}")
    print(f"[*] Target PDF Output   : {abs_pdf}")

    # --------------------------------------------------------------------------
    # METHOD 1: docx2pdf (Primary Standard Method)
    # --------------------------------------------------------------------------
    print("\n[Method 1] Attempting conversion using 'docx2pdf'...")
    try:
        from docx2pdf import convert
        convert(abs_docx, abs_pdf)
        if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
            print(f"[SUCCESS] Converted successfully via docx2pdf!")
            print(f"          PDF File Size: {os.path.getsize(abs_pdf):,} bytes")
            return abs_pdf
    except Exception as err:
        print(f"          [Notice] docx2pdf encountered an exception: {err}")

    # --------------------------------------------------------------------------
    # METHOD 2: LibreOffice / soffice CLI (Headless Cross-Platform)
    # --------------------------------------------------------------------------
    print("\n[Method 2] Checking for LibreOffice / soffice headless converter...")
    soffice_path = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice_path:
        try:
            cmd = [
                soffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", os.path.dirname(abs_pdf),
                abs_docx
            ]
            print(f"          Executing: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                print(f"[SUCCESS] Converted successfully via LibreOffice!")
                print(f"          PDF File Size: {os.path.getsize(abs_pdf):,} bytes")
                return abs_pdf
        except Exception as err:
            print(f"          [Notice] LibreOffice execution failed: {err}")
    else:
        print("          LibreOffice binary ('soffice') not found on system PATH.")

    # --------------------------------------------------------------------------
    # METHOD 3: Windows PowerShell Word COM Automation (Windows Native Fallback)
    # --------------------------------------------------------------------------
    if sys.platform == "win32":
        print("\n[Method 3] Attempting conversion via Windows PowerShell Word COM Automation...")
        try:
            ps_script = f"""
            $ErrorActionPreference = 'Stop'
            $docx = '{abs_docx}'
            $pdf = '{abs_pdf}'
            try {{
                $word = [System.Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
            }} catch {{
                $word = New-Object -ComObject Word.Application
            }}
            $word.Visible = $false
            $word.DisplayAlerts = 0
            $doc = $null
            foreach ($d in $word.Documents) {{
                if ($d.FullName -eq $docx) {{
                    $doc = $d
                    break
                }}
            }}
            if ($doc -eq $null) {{
                $doc = $word.Documents.Open($docx, $false, $true)
            }}
            # 17 = wdFormatPDF
            $doc.SaveAs($pdf, 17)
            $doc.Close(0)
            """
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                print(f"[SUCCESS] Converted successfully via Windows PowerShell COM!")
                print(f"          PDF File Size: {os.path.getsize(abs_pdf):,} bytes")
                return abs_pdf
            else:
                if result.stderr.strip():
                    print(f"          PowerShell error output: {result.stderr.strip()}")
        except Exception as err:
            print(f"          [Notice] PowerShell COM conversion failed: {err}")

    # If all methods fail
    raise RuntimeError(
        "PDF conversion failed: Neither docx2pdf (with MS Word), LibreOffice, "
        "nor PowerShell COM could complete the conversion. Please ensure Microsoft Word "
        "or LibreOffice is installed and accessible."
    )

if __name__ == "__main__":
    input_file = "Discrete_Mathematics_Project_Report_Group_2.docx"
    output_file = "Discrete_Mathematics_Project_Report_Group_2.pdf"

    print("==================================================================")
    print("      WORD (.DOCX) TO PDF (.PDF) AUTOMATED CONVERSION PIPELINE     ")
    print("==================================================================")

    try:
        generated_pdf = convert_word_to_pdf(input_file, output_file)
        print("==================================================================")
        print(f"[ALL COMPLETE] Output PDF ready: {generated_pdf}")
        print("==================================================================")
    except Exception as exc:
        print(f"\n[FATAL ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

