// Signed-in navigation for each role. Rename the admin group here only.
export const ADMIN_LABEL = 'Administration'

export const NAV = {
  super_admin: {
    links: [
      { label: 'Overview',  to: '/super-admin/overview' },
      { label: 'Sessions',  to: '/super-admin/sessions' },
      { label: 'Kapa',      to: '/super-admin/branches' },
      { label: 'Kaumātua',  to: '/super-admin/participants' },
      { label: 'Reports',   to: '/super-admin/reporting' },
      { label: 'Feedback',  to: '/super-admin/feedback' },
    ],
    admin: {
      to: '/super-admin/administration',
      children: [
        { label: 'Users',     to: '/super-admin/users' },
        { label: 'Audit log', to: '/super-admin/administration/audit' },
        { label: 'Documents', to: '/documents' },
      ],
    },
  },
  branch_manager: {
    links: [
      { label: 'Overview',  to: '/branch-manager/overview' },
      { label: 'Sessions',  to: '/branch-manager/sessions' },
      { label: 'Kaumātua',  to: '/branch-manager/participants' },
      { label: 'Reports',   to: '/branch-manager/reports' },
      { label: 'Feedback',  to: '/branch-manager/feedback' },
    ],
    admin: {
      to: '/branch-manager/administration',
      children: [
        { label: 'Kaimahi',   to: '/branch-manager/instructors' },
        { label: 'Audit log', to: '/branch-manager/administration/audit' },
        { label: 'Documents', to: '/documents' },
      ],
    },
  },
  instructor: {
    links: [
      { label: 'Home',      to: '/instructor/home' },
      { label: 'Sessions',  to: '/instructor/sessions' },
      { label: 'Kaumātua',  to: '/instructor/participants' },
      { label: 'Feedback',  to: '/instructor/feedback' },
      // Kaimahi have no admin page, so Documents stays in their main row.
      { label: 'Documents', to: '/documents' },
    ],
  },
}

export const HELP_LINK = { label: 'Help', to: '/help' }

export const ROLE_LABELS = {
  super_admin: 'Super Admin',
  branch_manager: 'Branch Manager',
  instructor: 'Kaimahi',
}

// True when `path` is `to` or a page beneath it.
export function isUnder(path, to) {
  return path === to || path.startsWith(`${to}/`)
}
