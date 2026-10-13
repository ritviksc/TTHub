// Pure helpers for the Help page: the article explorer and the chat assistant.

export const MAX_QUESTION = 500
export const MAX_HISTORY = 6

/* ---- explorer ---- */

// Articles arrive in explorer order (audience, then order). Group them into
// audience folders, then section folders, keeping that order.
export function buildHelpTree(articles) {
  const audiences = new Map()
  for (const article of articles) {
    if (!audiences.has(article.audience)) {
      audiences.set(article.audience, {
        id: `a:${article.audience}`, kind: 'audience', label: article.audience_label, sections: new Map(),
      })
    }
    const sections = audiences.get(article.audience).sections
    if (!sections.has(article.section)) {
      sections.set(article.section, {
        id: `s:${article.audience}/${article.section}`, kind: 'section', label: article.section, children: [],
      })
    }
    sections.get(article.section).children.push({ id: article.slug, kind: 'article', label: article.title, slug: article.slug })
  }
  return [...audiences.values()].map(({ sections, ...audience }) => ({ ...audience, children: [...sections.values()] }))
}

// The rows currently visible, with their depth. While searching, only matching
// articles and the folders above them are shown, all opened.
export function treeRows(tree, expanded, query = '') {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean)
  const matches = node => words.every(word => node.label.toLowerCase().includes(word))
  const rows = []
  for (const audience of tree) {
    const sections = audience.children
      .map(section => ({ section, articles: words.length ? section.children.filter(matches) : section.children }))
      .filter(({ articles }) => articles.length)
    if (!sections.length) continue
    const audienceOpen = words.length > 0 || expanded.has(audience.id)
    rows.push({ node: audience, depth: 0, open: audienceOpen })
    if (!audienceOpen) continue
    for (const { section, articles } of sections) {
      const sectionOpen = words.length > 0 || expanded.has(section.id)
      rows.push({ node: section, depth: 1, open: sectionOpen })
      if (sectionOpen) for (const article of articles) rows.push({ node: article, depth: 2 })
    }
  }
  return rows
}

// The articles either side of this one within its section, for Previous / Next links.
export function siblings(articles, slug) {
  const current = articles.find(article => article.slug === slug)
  if (!current) return { previous: null, next: null }
  const section = articles.filter(a => a.audience === current.audience && a.section === current.section)
  const index = section.indexOf(current)
  return { previous: section[index - 1] ?? null, next: section[index + 1] ?? null }
}

/* ---- chat ---- */

// The answer cites articles as [slug]; the Sources chips show them, so hide the
// raw markers. A Markdown link such as [text](url) is left alone. While an answer
// is still streaming, a half-written marker at the end ("[docum") is hidden too.
export function stripCitations(text, { streaming = false } = {}) {
  const tidy = text.replace(/[ \t]?\[[a-z0-9]+(?:-[a-z0-9]+)*\](?!\()/g, '')
  return streaming ? tidy.replace(/[ \t]?\[[a-z0-9-]*$/, '') : tidy
}

// Earlier turns sent with a new question, so follow-ups like "and then?" make
// sense. Stopped and failed turns are left out; the server also keeps at most six.
export function chatHistory(messages, max = MAX_HISTORY) {
  return messages
    .filter(message => !message.omit)
    .map(({ role, content }) => ({ role, content }))
    .slice(-max)
}

// Split newline-delimited JSON. `rest` is an incomplete last line to keep for
// the next chunk of the stream.
export function parseNdjson(buffer) {
  const lines = buffer.split('\n')
  const rest = lines.pop()
  return { events: lines.filter(line => line.trim()).map(line => JSON.parse(line)), rest }
}

export function helpError(error) {
  const status = error?.response?.status
  if (status === 429) return 'You have asked a lot of questions recently. Please wait a while and try again.'
  if (status === 503) return error.response.data?.detail || 'The help assistant is unavailable right now.'
  if (status === 400) return 'Questions can be up to 500 characters.'
  if (error?.code === 'ETIMEDOUT') return 'The help assistant took too long to answer. Please try again.'
  return 'Could not reach the help assistant. Please try again.'
}

export function messageTime(date) {
  return date.toLocaleTimeString('en-NZ', { hour: 'numeric', minute: '2-digit' })
}
