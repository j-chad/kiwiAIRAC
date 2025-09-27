use std::collections::HashMap;
use std::process::Command;
use bitflags::bitflags;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AIRACError {
    #[error("Invalid year: {0}. Year must be between 2000 and 2100.")]
    InvalidYear(u16),
    #[error("Failed to fetch schedule from URL: {0}")]
    FetchError(String),
    #[error("Failed to parse schedule PDF: {0}")]
    ParseError(String),
}

type Result<T> = std::result::Result<T, AIRACError>;

bitflags! {
    #[derive(Debug, Copy, Clone)]
    pub struct AmendmentContent: u8 {
        const SUP  = 0b0001; // AIP Supplements
        const AMDT = 0b0010; // AIP Amendment
        const ENRC = 0b0100; // En-route Charts
        const VNC  = 0b1000; // Visual Navigation Charts
    }
}

const AIP_UPDATE: AmendmentContent = AmendmentContent::SUP.union(AmendmentContent::AMDT);
const MIDYEAR_UPDATE: AmendmentContent = AIP_UPDATE.union(AmendmentContent::ENRC);
const ENDYEAR_UPDATE: AmendmentContent = MIDYEAR_UPDATE.union(AmendmentContent::VNC);

pub struct AiracCycle {
    pub cycle_id: String,
    pub effective_date: chrono::NaiveDate,
    pub content: AmendmentContent,
}

pub fn get_schedule_for_year(year: u16) -> Result<Vec<AiracCycle>> {
    let url = get_schedule_url(year);
    let pdf_data = fetch_schedule_pdf(&url)?;

    parse_schedule_pdf(&pdf_data)
}

fn get_schedule_url(year: u16) -> String {
    format!("https://www.aviation.govt.nz/assets/airspace-and-aerodromes/aip/AIP-NZ-Schedule-{}.pdf", year)
}

fn fetch_schedule_pdf(url: &str) -> Result<Vec<u8>> {
    ureq::get(url)
        .call()
        .map_err(|e| AIRACError::FetchError(e.to_string()))?
        .body_mut()
        .read_to_vec()
        .map_err(|e| AIRACError::FetchError(e.to_string()))
}

fn parse_schedule_pdf(pdf_data: &[u8]) -> Result<Vec<AiracCycle>> {
    let temp_file = save_pdf_to_tempfile(pdf_data)?;
    let text = extract_text(&temp_file)?;
    let cycles = extract_tables(&text);
    Ok(cycles)
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
        Err(AIRACError::ParseError(format!(
            "pdftotext failed: {}",
            String::from_utf8_lossy(&output.stderr)
        )))
    }
}

fn extract_tables(text: &str) -> Vec<AiracCycle> {
    let mut cycles = HashMap::new();

    let row_regex = regex::Regex::new(r"^\s*(\d{2}/\d{1,2})[0-9A-Za-z -]+?(\d{1,2}-[A-Za-z]{3}-\d{2})$").unwrap();

    let mut current_content = AmendmentContent::empty();
    for line in text.lines() {
        if line.contains("(SUP)") {
            current_content = AmendmentContent::SUP
        } else if line.contains("(AMDT)") {
            current_content = AmendmentContent::AMDT
        } else if line.contains("(ENRC)") {
            current_content = AmendmentContent::ENRC
        } else if line.contains("(VNC)") {
            current_content = AmendmentContent::VNC
        }

        if let Some(caps) = row_regex.captures(line) {
            let cycle_id = caps.get(1).unwrap().as_str().trim().to_string();
            let date_str = caps.get(2).unwrap().as_str().trim();
            if let Ok(effective_date) = chrono::NaiveDate::parse_from_str(date_str, "%d-%b-%y") {
                cycles.entry(cycle_id.clone())
                    .and_modify(|c: &mut AiracCycle| c.content |= current_content)
                    .or_insert(AiracCycle {
                    cycle_id: cycle_id.clone(),
                    effective_date,
                    content: current_content,
                });
            }
        }
    }

    let mut cycles_vec: Vec<AiracCycle> = cycles.into_values().collect();
    cycles_vec.sort_by_key(|c| c.effective_date);
    cycles_vec
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_schedule_for_year() {
        let year = 2025;
        let schedule = get_schedule_for_year(year).unwrap();
        assert!(!schedule.is_empty());
    }
}