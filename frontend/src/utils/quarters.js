// ISO date strings avoid browser timezone conversion of reporting boundaries.
export function calendarQuarters(year) {
  return ['03-31', '06-30', '09-30', '12-31'].map((end, index) => ({
    quarter: index + 1,
    start_date: `${year}-${String(index * 3 + 1).padStart(2, '0')}-01`,
    end_date: `${year}-${end}`,
  }))
}
