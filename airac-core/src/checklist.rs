use bitflags::bitflags;
use regex::CaptureMatches;
use crate::pdf;

const CHECKLIST_URL: &str = "https://www.aip.net.nz/assets/AIP/General-GEN/0-GEN/GEN_0.4.pdf";
const COLUMN_REGEX: &str = r"(?:(?:(?<page>(?:[A-Z]+ )?[A-Za-z]+ [\d.Y-]+) +(?<effective_date>\d{1,2} [A-Z]{3} \d{2}))|(?<blank>Blank)) +(?<volumes>(?:[1234] *)+)";

bitflags! {
    #[derive(Debug, Clone, Copy)]
    pub struct Volumes: u8 {
        const VOLUME_1 = 0b0001;
        const VOLUME_2 = 0b0010;
        const VOLUME_3 = 0b0100;
        const VOLUME_4 = 0b1000;
    }
}

#[derive(Debug)]
pub enum ChecklistError {
    FetchError(String),
    ParseError(String),
}

type Result<T> = std::result::Result<T, ChecklistError>;

#[derive(Clone)]
pub struct ChecklistItem {
    pub sort_order: usize,
    pub page_number: String,
    pub effective_date: chrono::NaiveDate,
    pub volumes: Volumes,
    pub blank_back: bool,
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

    let col1_page_regex = regex::Regex::new(format!(r"(?m)^{}", COLUMN_REGEX).as_str())
        .map_err(|e| ChecklistError::ParseError(format!("Failed to compile regex: {}", e)))?;
    let col2_page_regex = regex::Regex::new(format!(r"(?m){}$", COLUMN_REGEX).as_str())
        .map_err(|e| ChecklistError::ParseError(format!("Failed to compile regex: {}", e)))?;

    let mut sort_order = 0;
    let mut items = Vec::new();

    let pages = text.split("\u{c}");
    for page in pages {
        let col1_matches = col1_page_regex.captures_iter(page);
        parse_page_column(col1_matches, &mut sort_order, &mut items)?;

        let col2_matches = col2_page_regex.captures_iter(page);
        parse_page_column(col2_matches, &mut sort_order, &mut items)?;
    }

    Ok(items)
}

fn parse_page_column(matches: CaptureMatches, sort_order: &mut usize, items: &mut Vec<ChecklistItem>) -> Result<()> {
    for cap in matches {
        if cap.name("blank").is_some() {
            // top item on the stack is a blank page
            let last_item = items.last_mut().ok_or(ChecklistError::ParseError("Missing blank item".to_string()))?;
            last_item.blank_back = true;
            continue;
        }

        let page_number = cap.name("page").ok_or(ChecklistError::ParseError(
            "Missing page number".to_string(),
        ))?.as_str().trim().to_string();

        let date_str = cap.name("effective_date").ok_or(ChecklistError::ParseError(
            "Missing effective date".to_string(),
        ))?.as_str().trim();
        let effective_date = chrono::NaiveDate::parse_from_str(date_str, "%d %b %y")
            .map_err(|e| ChecklistError::ParseError(format!("Failed to parse date: {}", e)))?;

        let volumes_str = cap.name("volumes").ok_or(ChecklistError::ParseError(
            "Missing volumes".to_string(),
        ))?.as_str().trim();
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
            sort_order: *sort_order,
            page_number,
            effective_date,
            volumes,
            blank_back: false,
        });

        *sort_order += 1;
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use crate::amendments::get_future_amendments;
    use super::*;

    #[test]
    fn test_get_checklist() {
        let checklist = get_checklist().unwrap();
        let future = get_future_amendments(chrono::NaiveDate::from_ymd(2025, 7, 6), &checklist);
        assert!(!future.is_empty());
    }
}