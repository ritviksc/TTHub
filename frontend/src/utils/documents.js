// Shared helpers for navigating a flat list of folders as a tree, without
// fetching a subtree per click -- there are only ever a handful of folders
// per branch, so the whole scope is fetched once and walked client-side.

/** Every folder directly inside `parentId` (null for the scope's root), name-sorted. */
export function childrenOf(folders, parentId) {
  return folders
    .filter(f => (f.parent ?? null) === parentId)
    .sort((a, b) => a.name.localeCompare(b.name))
}

/** The chain of folders from the root down to `folderId`, root first. Empty at the root. */
export function folderTrail(folders, folderId) {
  const byId = new Map(folders.map(f => [f.id, f]))
  const trail = []
  let current = folderId ? byId.get(folderId) : null
  while (current) {
    trail.unshift(current)
    current = current.parent ? byId.get(current.parent) : null
  }
  return trail
}

/** "Policies › H&S" style label for `folderId`, or "" at the root. */
export function folderPath(folders, folderId) {
  return folderTrail(folders, folderId).map(f => f.name).join(' › ')
}

/** `folderId` and everything nested under it, including itself. Used to keep a
 * folder from being moved into its own subtree. */
export function folderAndDescendantIds(folders, folderId) {
  const ids = new Set([folderId])
  // Folders only ever nest a few levels deep, so a fixed-point pass over the
  // whole list is simpler than recursion and just as fast at this scale.
  let grew = true
  while (grew) {
    grew = false
    for (const f of folders) {
      if (f.parent && ids.has(f.parent) && !ids.has(f.id)) {
        ids.add(f.id)
        grew = true
      }
    }
  }
  return ids
}

/** Branches grouped under their region for the branch switcher: regions in
 * alphabetical order, branches by name, and anything without a region last
 * under "Other". Each branch is { key, label, region }. */
export function groupBranchesByRegion(branches) {
  const groups = new Map()
  for (const branch of branches) {
    const region = branch.region?.trim() || ''
    if (!groups.has(region)) groups.set(region, [])
    groups.get(region).push(branch)
  }
  return [...groups.entries()]
    .sort(([a], [b]) => (a === '') - (b === '') || a.localeCompare(b))
    .map(([region, list]) => ({
      title: region || 'Other',
      branches: [...list].sort((a, b) => a.label.localeCompare(b.label)),
    }))
}

/** `keys` with `key` moved to the front, without duplicates, capped at `max`. */
export function pushRecent(keys, key, max = 5) {
  return [key, ...keys.filter(k => k !== key)].slice(0, max)
}
