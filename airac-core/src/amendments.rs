use crate::checklist;

pub fn get_future_amendments(from: chrono::NaiveDate, items: &[checklist::ChecklistItem]) -> Vec<checklist::ChecklistItem> {
    let mut future_items: Vec<checklist::ChecklistItem> = items
        .iter()
        .filter(|item| item.effective_date >= from)
        .cloned()
        .collect();
    future_items.sort_by_key(|item| item.sort_order);
    future_items
}