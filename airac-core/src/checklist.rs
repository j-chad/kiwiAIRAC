use std::process::Command;
use bitflags::bitflags;
use crate::airac::AIRACError;
use crate::pdf;

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
    let temp_file = pdf::save_pdf_to_tempfile("checklist", pdf_data)
        .map_err(|e| ChecklistError::ParseError(format!("Failed to create temp file: {}", e)))?;
    let text = pdf::extract_text(temp_file.path())
        .map_err(|e| ChecklistError::ParseError(format!("Failed to extract text from PDF: {}", e)))?;

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

    // Sort items by effective_date descending

    items.sort_unstable_by(|a, b| b.effective_date.cmp(&a.effective_date));
    Ok(items)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_checklist() {
        let checklist = get_checklist();
        assert!(!checklist.is_ok());
    }
}