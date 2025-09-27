use std::process::Command;
use bitflags::bitflags;
use crate::airac::AIRACError;

const CHECKLIST_URL: &str = "https://www.aip.net.nz/assets/AIP/General-GEN/0-GEN/GEN_0.4.pdf";

bitflags! {
    #[derive(Debug, Clone, Copy)]
    pub struct Volumes: u8 {
        const VOLUME_1 = 0b0001;
        const VOLUME_2 = 0b0010;
        const VOLUME_3 = 0b0100;
        const VOLUME_4 = 0b1000;
    }
}

pub enum ChecklistError {
    FetchError(String),
    ParseError(String),
}

type Result<T> = std::result::Result<T, ChecklistError>;

pub struct ChecklistItem {
    pub page_number: String,
    pub effective_date: chrono::NaiveDate,
    pub volumes: Volumes,
}

pub fn get_checklist() -> Result<Vec<ChecklistItem>> {
    let pdf_data = fetch_checklist_pdf(CHECKLIST_URL)?;
    parse_checklist_pdf(&pdf_data)
}

fn fetch_checklist_pdf(url: &str) -> Result<Vec<u8>> {
    ureq::get(url)
        .call()
        .map_err(|e| ChecklistError::FetchError(e.to_string()))?
        .body_mut()
        .read_to_vec()
        .map_err(|e| ChecklistError::FetchError(e.to_string()))
}

fn parse_checklist_pdf(pdf_data: &[u8]) -> Result<Vec<ChecklistItem>> {
    let temp_file = save_pdf_to_tempfile(pdf_data)?;
    let text = extract_text(&temp_file)?;

    let regex = regex::Regex::new(r"([A-Za-z]+ [\d.-]+) +(\d{1,2} [A-Z]{3} \d{2}) +((?:[1234] *)+)")
        .map_err(|e| ChecklistError::ParseError(format!("Failed to compile regex: {}", e)))?;

    let mut items = Vec::new();
    for cap in regex.captures_iter(&text) {
        let page_number = cap[1].trim().to_string();
        let effective_date = chrono::NaiveDate::parse_from_str(&cap[2], "%d %b %y")
            .map_err(|e| ChecklistError::ParseError(format!("Failed to parse date: {}", e)))?;

        let volumes_str = cap[3].trim();
        let mut volumes = Volumes::empty();
        for ch in volumes_str.chars() {
            match ch {
                '1' => volumes |= Volumes::VOLUME_1,
                '2' => volumes |= Volumes::VOLUME_2,
                '3' => volumes |= Volumes::VOLUME_3,
                '4' => volumes |= Volumes::VOLUME_4,
                _ => {},
            }
        }
        items.push(ChecklistItem {
            page_number,
            effective_date,
            volumes,
        });
    }

    Ok(items)
}

fn save_pdf_to_tempfile(pdf_data: &[u8]) -> Result<String> {
    let mut temp_file = std::env::temp_dir();
    temp_file.push("airac_schedule.pdf");
    std::fs::write(&temp_file, pdf_data)
        .map_err(|e| AIRACError::FetchError(e.to_string()))?;
    Ok(temp_file.to_str().unwrap().to_string())
}

fn extract_text(path: &str) -> Result<String>  {
    let output = Command::new("pdftotext")
        .arg("-layout")   // preserve table layout
        .arg(path)        // input PDF
        .arg("-")         // output to stdout instead of file
        .output()
        .map_err(|e| AIRACError::ParseError(format!("Failed to execute pdftotext: {}", e)))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).into_owned())
    } else {
        Err(ChecklistError::ParseError(format!(
            "pdftotext failed: {}",
            String::from_utf8_lossy(&output.stderr)
        )))
    }
}