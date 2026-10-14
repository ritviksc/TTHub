import axios from "axios"
import Cookies from "js-cookie"
import { parseNdjson } from "./utils/help.js"
export const MAX_ATTEMPTS = 3
export const TIMEOUT_ERROR = "ETIMEDOUT"
// Synchronous report generation can wait up to 200 seconds for the LLM.
const ANALYSIS_TIMEOUT_MS = 240000
// Vite substitutes this public setting at build time; include /api in the URL.
export const API_BASE = (import.meta.env?.VITE_API_BASE_URL?.trim() || "http://localhost:8000/api").replace(/\/+$/, "")

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
  // Allow time for the hosted backend to wake up before failing the request.
  timeout: 120000,
  transitional: {
        clarifyTimeoutError: true,
    }
});

// Backend cookies are unreadable on a separate frontend hostname. Keep the
// masked token in memory; login rotates it and /me restores it after reload.
let csrfToken = ""
api.interceptors.response.use(response => {
  if (response.data?.csrfToken) csrfToken = response.data.csrfToken
  return response
})
api.interceptors.request.use(config => {
  if (csrfToken && !["get", "head", "options"].includes(config.method)) {
    config.headers.set("X-CSRFToken", csrfToken)
    config.withXSRFToken = false
  }
  return config
})

// Helper function to pause execution for 'ms' milliseconds
function sleep(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms);
  });
}

// maxAttempts includes the initial request. Retry only timeouts; permission,
// validation and other errors must reach the caller without repeated requests.
export async function withRetry(maxAttempts, axiosFunction, ...args) {
  maxAttempts ??= MAX_ATTEMPTS
  if (!Number.isInteger(maxAttempts) || maxAttempts < 1) {
    throw new RangeError("maxAttempts must be a positive integer")
  }

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await axiosFunction(...args)
    } catch (error) {
      if (error.code !== TIMEOUT_ERROR || attempt === maxAttempts) {
        // Preserve Axios status and response data for the page's error handler.
        throw error
      }
      const jitter = Math.random() * 500
      await sleep(100 * Math.pow(2, attempt - 1) + jitter)
    }
  }
}

// Centralise GET retries so callers cannot accidentally omit them. Do not wrap
// exported GET functions in another withRetry call, which multiplies attempts.
function getWithRetry(url, config) {
  return withRetry(null, () => api.get(url, config))
}

// Fetch the cookie and the masked token used by subsequent writes.
export async function fetchCsrfCookie() {
  await getWithRetry("/auth/csrf/")
}

export async function login(email, password) {
  const response = await api.post(
    "/auth/login/",
    {
      email,
      password,
    }
  )
  return response.data;

}

export async function logout() {
  const response = await api.post(
    "/auth/logout/"
  )
  return response.data
}

export async function fetchMe() {
  const response = await getWithRetry(
    "/auth/me/",
  )
  return response.data
}

/* ---- staff ---- */

export async function createStaffAccount(payload){
  // Hidden branch pickers can retain an empty or previously selected value.
  const data = { ...payload }
  if (data.role === 'super_admin') data.branch = null
  else if (data.branch === '') delete data.branch
  const response = await api.post(
      "/auth/staff/", 
      data
    )
  return response.data
}

export async function listStaff() {
  const response = await getWithRetry("/auth/staff/list/")
  return response.data
}

export async function deactivateStaff(id) {
  const response = await api.post(`/auth/staff/${id}/deactivate/`)
  return response.data
}

export async function reactivateStaff(id) {
  const response = await api.post(`/auth/staff/${id}/reactivate/`)
  return response.data
}

export async function getStaff(id) {
  const response = await getWithRetry(`/auth/staff/${id}/`)
  return response.data
}

export async function updateStaff(id, payload) {
  const data = { ...payload }
  if (data.role === 'super_admin') data.branch = null
  else if (data.branch === '') delete data.branch
  const response = await api.patch(
    `/auth/staff/${id}/`,
    data
  )

  return response.data
}



/* ---- branches ---- */

// params: { search, no_manager } — both optional, both handled server side.
// Returns id/name/region plus manager_name and participant_count, so the same
// call serves both the Branch table and the branch pickers on the staff forms.
export async function listBranches(params = {}) {
  const response = await getWithRetry("/branches/", { params })
  return response.data
}

export async function createBranch(payload) {
  const response = await api.post("/branches/", payload)
  return response.data
}

export async function getBranch(id) {
  const response = await getWithRetry(`/branches/${id}/`)
  return response.data
}

export async function updateBranch(id, payload) {
  const response = await api.patch(`/branches/${id}/`, payload)
  return response.data
}

/* ---- participants ---- */

// params: { branch, is_active, search } — all optional.
export async function listParticipants(params = {}) {
  const response = await getWithRetry("/participants/", { params })
  return response.data
}

export async function getParticipant(id) {
  const response = await getWithRetry(`/participants/${id}/`)
  return response.data
}

export async function createParticipant(payload) {
  const response = await api.post("/participants/", payload)
  return response.data
}

export async function getParticipantAttendance(id) {
  const response = await getWithRetry(`/participants/${id}/attendance/`)
  return response.data
}

// Fetch through the authenticated API; no permanent document URL is exposed.
export async function downloadGpDocument(id) {
  const response = await getWithRetry(`/participants/${id}/gp-document/`, { responseType: 'blob' })
  return response.data
}

export async function updateParticipant(id, payload) {
  const response = await api.patch(`/participants/${id}/`, payload)
  return response.data
}

export async function deactivateParticipant(id) {
  const response = await api.post(`/participants/${id}/deactivate/`)
  return response.data
}

export async function reactivateParticipant(id) {
  const response = await api.post(`/participants/${id}/reactivate/`)
  return response.data
}

export async function deleteBranch(id) {
  const response = await api.delete(`/branches/${id}/`)
  return response.data
}

/* ---- documents ---- */

// params: { scope, branch, participant, folder } — all optional.
export async function listDocuments(params = {}) {
  const response = await getWithRetry("/documents/", { params })
  return response.data
}

// formData holds `file` plus, at most, one of `branch`, `participant` or `folder`.
// A longer timeout than the default 5s, since uploads can take a while.
export async function uploadDocument(formData) {
  const response = await api.post("/documents/", formData, { timeout: 60000 })
  return response.data
}

// Fetch through the authenticated API; no permanent document URL is exposed.
export async function downloadDocument(id) {
  const response = await getWithRetry(`/documents/${id}/download/`, { responseType: 'blob' })
  return response.data
}

// payload: { name? } to rename, { folder } to move (null moves to the scope's root).
export async function updateDocument(id, payload) {
  const response = await api.patch(`/documents/${id}/`, payload)
  return response.data
}

export async function deleteDocument(id) {
  const response = await api.delete(`/documents/${id}/`)
  return response.data
}

/* ---- help ---- */

// Articles for the signed-in user's role: [{ slug, title, order }].
export async function listHelpArticles() {
  const response = await getWithRetry("/help/articles/")
  return response.data
}

export async function getHelpArticle(slug) {
  const response = await getWithRetry(`/help/articles/${encodeURIComponent(slug)}/`)
  return response.data
}

// Ask the help assistant. The answer streams back as newline-delimited JSON
// events ({type: 'delta' | 'done' | 'error'}, see backend help/services/chat.py),
// passed to onEvent as they arrive. Uses fetch because axios cannot read a
// response while it is still arriving. Never retried: each attempt counts
// towards the hourly limit. Abort with `signal` (the Stop button, idle timeout).
// A non-2xx response throws an axios-shaped error ({ response: { status, data } }).
export async function streamHelp(question, history, { signal, onEvent }) {
  const response = await fetch(`${API_BASE}/help/chat/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken || Cookies.get("csrftoken") || "" },
    body: JSON.stringify({ question, history }),
    signal,
  })
  if (!response.ok) {
    const error = new Error(`Help request failed with status ${response.status}`)
    error.response = { status: response.status, data: await response.json().catch(() => ({})) }
    throw error
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  for (;;) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const { events, rest } = parseNdjson(done ? buffer + "\n" : buffer)
    events.forEach(onEvent)
    buffer = rest
    if (done) return
  }
}

/* ---- folders ---- */

// params: { scope: 'organisation' } or { branch }.
export async function listFolders(params = {}) {
  const response = await getWithRetry("/folders/", { params })
  return response.data
}

// payload: { name, parent?, branch? }. A subfolder's branch is taken from its parent.
export async function createFolder(payload) {
  const response = await api.post("/folders/", payload)
  return response.data
}

// payload: { name? } to rename, { parent } to move (null moves to the scope's root).
export async function updateFolder(id, payload) {
  const response = await api.patch(`/folders/${id}/`, payload)
  return response.data
}

export async function deleteFolder(id) {
  const response = await api.delete(`/folders/${id}/`)
  return response.data
}

// Assigning also grants the Branch Manager role, and moves the person off any
// branch they were on. The response reports both so the UI can say what happened.
export async function assignBranchManager(branchId, userId) {
  const response = await api.post(`/branches/${branchId}/managers/`, { user_id: userId })
  return response.data
}

export async function removeBranchManager(branchId, userId) {
  const response = await api.delete(`/branches/${branchId}/managers/${userId}/`)
  return response.data
}

export async function assignBranchInstructor(branchId, userId) {
  const response = await api.post(`/branches/${branchId}/instructors/`, { user_id: userId })
  return response.data
}

export async function removeBranchInstructor(branchId, userId) {
  const response = await api.delete(`/branches/${branchId}/instructors/${userId}/`)
  return response.data
}

/* ---- sessions ---- */

export async function listSessions(params = {}) {
  const response = await getWithRetry("/sessions/", { params })
  return response.data
}

export async function getSession(id) {
  const response = await getWithRetry(`/sessions/${id}/`)
  return response.data
}

export async function createSession(payload) {
  const response = await api.post("/sessions/", payload)
  return response.data
}

export async function updateAttendance(sessionId, attendanceId, changes) {
  const response = await api.patch(`/sessions/${sessionId}/attendance/${attendanceId}/`, changes)
  return response.data
}

export async function deleteSession(id) {
  await api.delete(`/sessions/${id}/`)
}

export async function setAttendanceFinalised(sessionId, finalised) {
  const response = await api.patch(`/sessions/${sessionId}/attendance-state/`, {
    attendance_finalised: finalised,
  })
  return response.data
}

/* ---- reporting ---- */

export async function getACCSources(scope, page = 1) {
  return (await getWithRetry('/reporting/acc/sources/', { params: { ...scope, page } })).data
}
export async function generateACCReport(payload) {
  return (await api.post('/reporting/acc/analyse/', payload, { timeout: ANALYSIS_TIMEOUT_MS })).data
}
export async function getACCAnalysisJob(jobId, signal) {
  return (await getWithRetry(`/reporting/acc/jobs/${jobId}/`, { signal })).data
}

export async function getReportHistory(reportType, { id, page = 1 } = {}) {
  return (await getWithRetry(`/reporting/${reportType}/history/${id ? `${id}/` : ''}`, { params: { page } })).data
}

export async function saveReportNarrative(reportType, jobId, narrative) {
  return (await api.patch(`/reporting/${reportType}/jobs/${jobId}/`, { narrative })).data
}

// scope: { start_date, end_date, branch_id? }; dates are inclusive YYYY-MM-DD.
export async function getAttendanceReport(scope) {
  const response = await getWithRetry('/reporting/attendance/', { params: scope })
  return response.data
}

export async function analyseAttendanceReport(scope) {
  // Never retry POSTs automatically: that could create two jobs.
  const response = await api.post('/reporting/attendance/analyse/', scope, { timeout: ANALYSIS_TIMEOUT_MS })
  return response.data
}

export async function getAttendanceAnalysisJob(jobId, signal) {
  const response = await getWithRetry(`/reporting/attendance/jobs/${jobId}/`, { signal })
  return response.data
}

/* ---- physical assessments ---- */
export async function listPhysicalAssessments(participantId) {
  return (await getWithRetry(`/physical-tests/participants/${participantId}/`)).data
}
// Starting is idempotent: the backend resumes the participant's existing draft.
export async function startPhysicalAssessment(participantId) {
  return (await api.post(`/physical-tests/participants/${participantId}/`)).data
}
export async function getPhysicalAssessment(id) {
  return (await getWithRetry(`/physical-tests/${id}/`)).data
}
export async function updatePhysicalAssessmentDate(id, assessed_on, version) {
  return (await api.patch(`/physical-tests/${id}/`, { assessed_on, version })).data
}
export async function savePhysicalResults(id, group, results, version) {
  return (await api.put(`/physical-tests/${id}/results/${group}/`, { results, version })).data
}
export async function completePhysicalAssessment(id, version) {
  return (await api.post(`/physical-tests/${id}/complete/`, { version })).data
}


/* ---- physical reporting ---- */
export async function getPhysicalReport(scope) {
  return (await getWithRetry('/reporting/physical/', { params: scope })).data
}
export async function analysePhysicalReport(scope) {
  return (await api.post('/reporting/physical/analyse/', scope, { timeout: ANALYSIS_TIMEOUT_MS })).data
}
export async function getPhysicalAnalysisJob(jobId, signal) {
  return (await getWithRetry(`/reporting/physical/jobs/${jobId}/`, { signal })).data
}

export async function listFeedback() {
  return (await getWithRetry('/participants/feedback/')).data
}
export async function createFeedback(payload) {
  return (await api.post('/participants/feedback/', payload)).data
}

/* ---- branch reporting quarters ---- */
export async function getBranchQuarters(branchId, year) {
  return (await getWithRetry(`/branches/${branchId}/quarters/${year}/`)).data
}

export async function saveBranchQuarters(branchId, year, quarters) {
  return (await api.put(`/branches/${branchId}/quarters/${year}/`, { quarters })).data
}

/* ---- audit trail (admins; branch scope enforced by server) ---- */
export async function listAuditEvents(params = {}) {
  return (await getWithRetry('/audit/', { params })).data
}

export async function getReportModels() {
  return (await getWithRetry('/reporting/models/')).data
}
