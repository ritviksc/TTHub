import MarkdownIt from 'markdown-it'

// Model output is untrusted: render Markdown while escaping embedded HTML.
const markdown = new MarkdownIt({ html: false, linkify: false })
// Reports do not need remote images, which could make unsolicited network requests.
markdown.disable('image')

export function renderMarkdown(text) {
  return markdown.render(text ?? '')
}
