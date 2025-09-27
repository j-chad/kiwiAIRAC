use std::borrow::Cow;
use bitflags::bitflags;
use thiserror::Error;
use pdf;
use pdf::content::{Color, Op, Rgb};
use pdf::object::{NoResolve, Page, Resolve};

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

struct AiracCycle {
    pub cycle_id: String,
    pub effective_date: chrono::NaiveDate,
    pub content: AmendmentContent,
}

pub fn get_schedule_for_year(year: u16) -> Result<Vec<AiracCycle>> {
    let url = get_schedule_url(year);
    let pdf_data = fetch_schedule_pdf(&url)?;
    let text = parse_schedule_pdf(&pdf_data)?;

    let cycles = Vec::new();
    Ok(cycles)
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
    let pdf = pdf::file::FileOptions::cached().load(pdf_data)
        .map_err(|e| AIRACError::ParseError(e.to_string()))?;

    let mut cycles = Vec::new();
    for page in pdf.pages() {
        let page = page.map_err(|e| AIRACError::ParseError(e.to_string()))?;
        let parsed_cycles = parse_airac_on_page(&page, &pdf.resolver())?;
        cycles.extend(parsed_cycles);
    }
    Ok(cycles)
}

fn text_objects(operations: &[Op]) -> impl Iterator<Item = TextObject<'_>> + '_ {
    TextObjectParser {
        ops: operations.iter(),
    }
}

#[derive(Debug, Clone, PartialEq)]
struct TextObject<'src> {
    pub x: f32,
    pub y: f32,
    pub text: Cow<'src, str>,
    pub fill_color: Option<Rgb>
}

#[derive(Debug, Clone)]
struct TextObjectParser<'src> {
    ops: std::slice::Iter<'src, Op>,
}

impl<'src> Iterator for TextObjectParser<'src> {
    type Item = TextObject<'src>;

    fn next(&mut self) -> Option<Self::Item> {
        let mut last_coords = None;
        let mut last_text = None;
        let mut fill_color = None;

        while let Some(operator) = self.ops.next() {
            match (operator) {
                Op::FillColor {color: Color::Rgb(rgb)} => {
                    fill_color = Some(*rgb);
                }
                Op::BeginText => {
                    // Clear all prior state because we've just seen a
                    // "begin text" op
                    last_coords = None;
                    last_text = None;
                }
                Op::EndText => {
                    // "end of text" - we should have finished this text object,
                    // if we got all the right information then we can yield it
                    // to the caller. Otherwise, use take() to clear anything
                    // we've seen so far and continue.
                    if let (Some((x, y)), Some(text)) = (last_coords.take(), last_text.take()) {
                        return Some(TextObject { x, y, text, fill_color });
                    }
                },
                Op::MoveTextPosition {translation} => {
                    // "Text Location" contains the location of the text on the
                    // current page.
                    last_coords = Some((translation.x, translation.y));
                },
                Op::TextDraw {text} => {
                    last_text = text.to_string().map_or_else(|_| None, |s| Some(Cow::Owned(s)));
                }
                _ => continue,
            }
        }

        None
    }
}

fn parse_airac_on_page(page: &Page, resolver: &impl Resolve) -> Result<Vec<AiracCycle>> {
    let content = match &page.contents {
        Some(c) => c,
        None => return Ok(Vec::new()),
    };

    let operations = content.operations(resolver).map_err(|e| AIRACError::ParseError(e.to_string()))?;
    let text_objects = text_objects(&operations);

    let mut cycles = Vec::new();
    cycles.extend(text_objects);
    return Ok(vec![]);
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