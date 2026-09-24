import axios from "axios"
export const MAX_ATTEMPTS = 3
export const TIMEOUT_ERROR = "ETIMEDOUT"

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
  timeout: 5000,
  transitional: {
        clarifyTimeoutError: true,
    }
});

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

// fetch Crsf token and store it as a cookie
// for future requests
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

export async function updateParticipant(id, payload) {
  const response = await api.patch(`/participants/${id}/`, payload)
  return response.data
}

export async function deactivateParticipant(id) {
  const response = await api.post(`/participants/${id}/deactivate/`)
  return response.data
}

export async function deleteBranch(id) {
  const response = await api.delete(`/branches/${id}/`)
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

// scope: { start_date, end_date, branch_id? }; dates are inclusive YYYY-MM-DD.
export async function getAttendanceReport(scope) {
  const response = await getWithRetry('/reporting/attendance/', { params: scope })
  return response.data
}

export async function analyseAttendanceReport(scope) {
  // This only queues work. Never retry POSTs automatically: that could create two jobs.
  const response = await api.post('/reporting/attendance/analyse/', scope)
  return response.data
}

export async function getAttendanceAnalysisJob(jobId, signal) {
  const response = await getWithRetry(`/reporting/attendance/jobs/${jobId}/`, { signal })
  return response.data
}
