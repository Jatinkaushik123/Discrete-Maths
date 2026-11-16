"""
convert_doc_to_pdf.py
=====================
Cross-platform automation script to convert 'Discrete_Mathematics_Project_Report_Group_2.docx'
into a publication-grade PDF named 'Discrete_Mathematics_Project_Report_Group_2.pdf'.

Supports:
1. Native Windows MS Word COM automation via docx2pdf
2. Active-Instance Word COM export (handles case where file is already open in MS Word)
3. Cross-platform headless LibreOffice / soffice CLI fallback
4. Windows PowerShell Word COM fallback
"""

import os
import sys
import shutil
import subprocess

def convert_docx_to_pdf(docx_path: str, pdf_path: str):
    abs_docx = os.path.abspath(docx_path)
    abs_pdf = os.path.abspath(pdf_path)

    if not os.path.exists(abs_docx):
        raise FileNotFoundError(f"Input Word document not found: {abs_docx}")

    print(f"[*] Input Word Document : {abs_docx}")
    print(f"[*] Target PDF Document: {abs_pdf}")

    # Remove existing PDF if present to ensure clean overwrite
    if os.path.exists(abs_pdf):
        try:
            os.remove(abs_pdf)
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Method 1: docx2pdf (Primary standard method)
    # --------------------------------------------------------------------------
    print("[1/4] Attempting conversion using 'docx2pdf'...")
    try:
        from docx2pdf import convert
        convert(abs_docx, abs_pdf)
        if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
            print(f"[SUCCESS] Converted via docx2pdf! PDF size: {os.path.getsize(abs_pdf):,} bytes")
            return abs_pdf
    except Exception as e:
        print(f"      docx2pdf encountered an exception: {e}")

    # --------------------------------------------------------------------------
    # Method 2: Direct Windows COM Automation (win32com.client)
    # Handles both new instance and already-open document in MS Word
    # --------------------------------------------------------------------------
    if sys.platform == "win32":
        print("[2/4] Attempting conversion via Windows Word COM automation (win32com)...")
        try:
            import win32com.client
            import pythoncom

            pythoncom.CoInitialize()
            word = None
            try:
                # Try getting active object first (in case Word is currently running with the file open)
                try:
                    word = win32com.client.GetActiveObject("Word.Application")
                except Exception:
                    word = win32com.client.Dispatch("Word.Application")

                word.Visible = False
                doc = None

                # Check if the document is already open in Word
                for open_doc in word.Documents:
                    if os.path.abspath(open_doc.FullName).lower() == abs_docx.lower():
                        doc = open_doc
                        print("      Found document already open in Word.")
                        break

                if doc is None:
                    doc = word.Documents.Open(abs_docx, ReadOnly=True)

                # wdExportFormatPDF = 17
                doc.ExportAsFixedFormat(
                    OutputFileName=abs_pdf,
                    ExportFormat=17,
                    OpenAfterExport=False,
                    OptimizeFor=0,  # wdExportOptimizeForPrint
                    CreateBookmarks=1  # wdExportCreateHeadingBookmarks
                )
                print("      ExportAsFixedFormat executed.")
            finally:
                pythoncom.CoUninitialize()

            if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                print(f"[SUCCESS] Converted via Windows Word COM! PDF size: {os.path.getsize(abs_pdf):,} bytes")
                return abs_pdf
        except Exception as e:
            print(f"      Windows Word COM encountered an exception: {e}")

    # --------------------------------------------------------------------------
    # Method 3: Cross-platform LibreOffice / soffice CLI
    # --------------------------------------------------------------------------
    print("[3/4] Checking for LibreOffice / soffice...")
    soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice_cmd:
        try:
            cmd = [
                soffice_cmd,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", os.path.dirname(abs_pdf),
                abs_docx
            ]
            print(f"      Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                print(f"[SUCCESS] Converted via LibreOffice! PDF size: {os.path.getsize(abs_pdf):,} bytes")
                return abs_pdf
        except Exception as e:
            print(f"      LibreOffice encountered an exception: {e}")

    # --------------------------------------------------------------------------
    # Method 4: Windows PowerShell COM Automation
    # --------------------------------------------------------------------------
    if sys.platform == "win32":
        print("[4/4] Attempting conversion via Windows PowerShell Word COM script...")
        try:
            ps_script = f"""
            $ErrorActionPreference = 'Stop'
            $docPath = '{abs_docx}'
            $pdfPath = '{abs_pdf}'
            try {{
                $word = [System.Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
            }} catch {{
                $word = New-Object -ComObject Word.Application
            }}
            $word.Visible = $false
            $doc = $null
            foreach ($d in $word.Documents) {{
                if ($d.FullName -eq $docPath) {{
                    $doc = $d
                    break
                }}
            }}
            if ($doc -eq $null) {{
                $doc = $word.Documents.Open($docPath, $false, $true)
            }}
            $doc.ExportAsFixedFormat($pdfPath, 17, $false, 0)
            Write-Output 'Exported'
            """
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                print(f"[SUCCESS] Converted via PowerShell COM! PDF size: {os.path.getsize(abs_pdf):,} bytes")
                return abs_pdf
            else:
                print(f"      PowerShell STDERR: {result.stderr.strip()}")
        except Exception as e:
            print(f"      PowerShell COM encountered an exception: {e}")

    raise RuntimeError(
        "PDF conversion could not be completed with the available methods. "
        "Ensure Microsoft Word or LibreOffice is installed and accessible."
    )

if __name__ == "__main__":
    input_doc = "Discrete_Mathematics_Project_Report_Group_2.docx"
    output_pdf = "Discrete_Mathematics_Project_Report_Group_2.pdf"

    try:
        pdf_file = convert_docx_to_pdf(input_doc, output_pdf)
        print("==================================================================")
        print(f"CONVERSION COMPLETE: {pdf_file}")
        print("==================================================================")
    except Exception as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        sys.exit(1)

