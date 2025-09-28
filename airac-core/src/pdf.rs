use std::io;
use std::io::Write;
use std::path::Path;
use std::process::Command;
use tempfile::NamedTempFile;

pub fn save_pdf_to_tempfile(prefix: &str, pdf_data: &[u8]) -> io::Result<NamedTempFile> {
    let mut temp_file = tempfile::Builder::new().prefix(prefix).suffix(".pdf").tempfile()?;
    temp_file.write_all(pdf_data)?;
    Ok(temp_file)
}

pub fn extract_text(path: &Path) -> io::Result<String>  {
    let output = Command::new("pdftotext")
        .arg("-layout")   // preserve table layout
        .arg(path)        // input PDF
        .arg("-")         // output to stdout instead of file
        .output()?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).into_owned())
    } else {
        Err(io::Error::new(io::ErrorKind::Other, format!(
            "pdftotext failed: {}",
            String::from_utf8_lossy(&output.stderr)
        )))
    }
}