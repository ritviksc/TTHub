import assert from 'node:assert/strict'
import { test } from 'node:test'
import { renderMarkdown } from '../src/utils/markdown.js'

test('renders report headings, emphasis, lists and tables', () => {
  const html = renderMarkdown('## Attendance\n\n**10** visits and *7* people.\n\n- One empty session\n\n1. Review records\n\n| Month | Visits |\n| --- | --- |\n| January | 10 |')
  assert.match(html, /<h2>Attendance<\/h2>/)
  assert.match(html, /<strong>10<\/strong>/)
  assert.match(html, /<em>7<\/em>/)
  assert.match(html, /<ul>/)
  assert.match(html, /<ol>/)
  assert.match(html, /<table>/)
  assert.match(html, /<td>January<\/td>/)
})

test('escapes raw HTML and rejects executable links', () => {
  const html = renderMarkdown('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[click](javascript:alert(1))\n\n[click](data:text/html;base64,PHNjcmlwdD4=)')
  assert.doesNotMatch(html, /<script|<img|href="(?:javascript|data):/i)
  assert.match(html, /&lt;script&gt;/)
})

test('does not load Markdown images and preserves ordinary links', () => {
  const html = renderMarkdown('![tracking](https://example.com/pixel.png)\n\n[Source](https://example.com/report)')
  assert.doesNotMatch(html, /<img/i)
  assert.match(html, /href="https:\/\/example.com\/report"/)
})

test('handles empty and plain text responses', () => {
  assert.equal(renderMarkdown(null), '')
  assert.equal(renderMarkdown(''), '')
  assert.equal(renderMarkdown('Attendance increased.'), '<p>Attendance increased.</p>\n')
})
