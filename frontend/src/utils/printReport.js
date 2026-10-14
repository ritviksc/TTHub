export function printReport(element, title) {
  const printWindow = window.open('', '_blank')
  if (!printWindow) throw new Error('Allow pop-ups for this site, then try downloading the PDF again.')
  printWindow.opener = null
  const report = element.cloneNode(true)
  // Export the reviewed report only, including when original feedback is expanded on screen.
  report.querySelectorAll('button, form, [role="status"], [data-print-exclude]').forEach(node => node.remove())
  report.querySelectorAll('details').forEach(node => { node.open = true })

  const doc = printWindow.document
  doc.title = title
  const style = doc.createElement('style')
  style.textContent = `
    @page { size: A4; margin: 16mm; }
    body { max-width: 180mm; margin: 24px auto; padding: 0 16px; color: #111; background: #fff; font: 11pt/1.5 Arial, sans-serif; }
    * { box-sizing: border-box; overflow-wrap: anywhere; }
    h1 { font-size: 22pt; line-height: 1.2; margin-bottom: 8px; }
    h2 { font-size: 15pt; margin: 20px 0 10px; }
    h3 { font-size: 11pt; }
    h1, h2, h3, summary { break-after: avoid; }
    .page-subtitle { color: #444; }
    .report-section { margin: 20px 0; padding-top: 12px; border-top: 1px solid #bbb; }
    .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .stat-tile-value { font-size: 18pt; font-weight: bold; }
    .stat-tile-label { font-size: 10pt; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; }
    th, td { padding: 8px; border: 1px solid #bbb; text-align: left; }
    .engagement-table { table-layout: fixed; min-width: 0; font-size: 9pt; }
    .engagement-table th, .engagement-table td { padding: 5px 6px; overflow-wrap: normal; }
    .engagement-table tbody th { font-weight: normal; }
    thead { display: table-header-group; }
    tr, blockquote, .source, .stat-tile { break-inside: avoid; }
    blockquote { border-left: 3px solid #666; margin: 16px 0; padding-left: 14px; }
    .source { border-top: 1px solid #ddd; margin-top: 14px; }
    .source-text { white-space: pre-wrap; }
    summary { font-weight: bold; }
    a { color: inherit; }
    @media print { body { max-width: none; margin: 0; padding: 0; } .print-action { display: none; } }
  `
  doc.head.append(style)
  const printButton = doc.createElement('button')
  printButton.className = 'print-action'
  printButton.textContent = 'Print / Save as PDF'
  printButton.addEventListener('click', () => printWindow.print())
  doc.body.append(printButton, report)
  printWindow.focus()
  printWindow.requestAnimationFrame(() => printWindow.print())
}
